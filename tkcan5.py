#!/usr/bin/python3
# GUI Can data display using tkinter

from tkinter import *
import time
import can
import subprocess
import signal
import sys
import argparse
import queue
import math
import webbrowser

# Use parser to provide help and command line options
parser = argparse.ArgumentParser("GUI dashboard canbus data display built for 2018+ Jeep JL/JT/etc... products")
parser.add_argument('--vcan', action='store_true',
                    help='Use VCAN0 and VCAN1 for testing')
parser.add_argument('--fullscreen', '-f', action='store_true',
                    help='Enable Full Screen')
args = parser.parse_args()

if args.vcan:
    canIHS = "vcan0"
    canC = "vcan1"
else:
    canIHS = "can0"
    canC = "can1"

# Initialize variables
canFilter = list()
shutting_down = False
backgroundcolor = '#F0F0F0'
currentPage = 1
cam = None
dump = None
batterybars = []
batterytexts = []
batterylabelsdrawn = []
oldpstemp = None
oldrpm = 0
oldxfer = None
oldtilt = 0.0
oldroll = 0.0
oldiat = None
oldcoolant = None
oldoiltemp = None
oldoilpres = None
oldboost = None
oldbaro = 0
oldbatterytemps = [0] * 18
oldbatterycurrent = None
packvoltage = None
cellvoltages = [0.0] * 96
avgcellvoltage = 0.0
mincellvoltage = 0.0
maxcellvoltage = 0.0
celldelta = 0.0
horizoncanvas = None
horizonline = None
pitchtext = None
rolltext = None
filteredRoll = 0.0
filteredTilt = 0.0
oldcurrentgear = None
oldinputrpm = 0
oldacmode = None
oldevaptemp = None
oldrecirc = None
dark_mode = None
olddimmer = 0
oldignition = 0
packavg = [0.0] * 8
packlabels = []
oldgps = [0] * 2

# defined types to process the data. x = can message , a = byte 1 , b = byte 2
def raw8(x,a): #Raw decimal 8 bit
    return(x[a])

def raw16(x,a,b): #Raw decimal 16 bit
    return((x[a]<<8) + x[b])

def volt(x,a): #Battery Volts
    return(x[a] / 10)

def temp(x,a): #Oil temperature in F
    return(round((((x[a] - 40) * (9 / 5)) + 32)))

def tilt(x,a,b): #Angle in Degrees
    return(round(((x[a]<<8) + x[b] - 2048) / 10))

def rpm(x,a,b):
    if x[a] == 0xFF:
        return(0)
    return((x[a]<<8) +  x[b])

def mph(x,a,b):
    return(round(((x[a]<<8) + x[b]) / 200,1))

def psi(x,a): #Oil Pressure in PSI
    return(round(((x[a] * 4) * 0.145038)))

def steer(x,a,b): #Steering angle
    return(((x[a]<<8) + x[b]) - 0x1000)

def pstemp(x,a): #Power Steering pump temperature in F
    return(round(((x[a] * (9 / 5)) + 32)))

def boost(x,a,b): #MAP and Boost normalized and combined in PSI
    mapl = round((x[a] - oldbaro) * 0.145038)
    mapt = round((((x[b] * 0.8) + 94.6) - oldbaro) * 0.145038)
    if mapl > 0:
        return(mapt)
    else:
        return(mapl)

def baro(x,a): #Barometer in KPA
    return(x[a])

def gear(x,a): #Transmission gear selection
    GEARS = {
        0x4E: "N",
        0x52: "R",
        0x31: "1",
        0x32: "2",
        0x33: "3",
        0x34: "4",
        0x35: "5",
        0x36: "6",
        0x37: "7",
        0x38: "8",
        0x50: "P",
        0x44: "D"
        }
    return GEARS.get(x[a], f"{x[a]:x}")

def curgear(x,a): #Transmission gear selection
    GEARS = {
        0x11: "1",
        0x22: "2",
        0x33: "3",
        0x44: "4",
        0x55: "5",
        0x66: "6",
        0x77: "7",
        0x88: "8",
        0xDD: "P",
        0x00: "N",
        0xBB: "R",
        0xB0: "R",
        }
    return GEARS.get(x[a], f"{x[a]:x}")

def xfer(x,a): #Transfer Case gear selection
    XFERS = {
        0x00: "2H",
        0x02: "N",
        0x10: "4H",
        0x20: "N",
        0x40: "4L",
        0x80: "XX",
        }
    return XFERS.get(x[a], f"{x[a]:x}")

def batterycurrent(x,a): #4xe HV battery pack current
    raw = ((x[a] << 8) | x[a+1])
    return(round((((raw * 0.05) - 255) * 2) ,1))

def cellvoltage(x,a): #4xe HV Battery pack individual cell voltage
    raw = ((x[a] << 8) | x[a+1])
    return(round(raw / 1000.0, 3))

def acmode(x,a): #Air Conditioning selection
    MODE = {
        0x00: "Off",
        0x01: "Vent",
        0x03: "AC",
        0x07: "Defrost",
        0x23: "Max AC"
        }
    return MODE.get(x[a], f"{x[a]:x}")

def gpstrans(x,a): #Gps data transformation
    return(x)

def can36c_to_wgs84(x):
    """
    payload = 8-byte CAN data from ID 0x36C
    returns (lat, lon)
    """
    lat_raw = int.from_bytes(x[0:4], "little")
    lon_raw = int.from_bytes(x[4:8], "little")

    lat = lat_raw * 360.0 / 2**32 - 90.0
    lon = lon_raw * 360.0 / 2**32 - 180.0

    return lat, lon

# Display Functions
def newrpm(lrpm):
    global oldrpm
    low_r = 0 # chart low range
    hi_r = 7000 # chart hi range
    if lrpm == 65535:
      lrpm = 0
    if lrpm != oldrpm:
      oldrpm = lrpm
      updatetach()
      
def newmph(lmph):
    if str(lmph) != text1label["text"]:
      text1label["text"] = str(lmph)

def newbattv(lbattv):
    if str(lbattv) != text2label["text"]:
      text2label["text"] = str(lbattv)

def newgear(lgear):
    if str(lgear) != text3label["text"]:
        text3label["text"] = str(lgear)

def newxfer(lxfer):
    global oldxfer
    if lxfer != oldxfer:
        oldxfer = lxfer

def newpstemp(lpstemp):
    global oldpstemp
    low_r = 50 # chart low range
    hi_r = 250 # chart hi range
    if lpstemp != oldpstemp:
      text8label["text"] = str(lpstemp)
      pstempangle = (120 * (hi_r - lpstemp) / (hi_r - low_r) + 30)
      gauge2.itemconfig(gauge2needle,start = pstempangle)
      gauge2.grid()
      oldpstemp = lpstemp

def newiat(liat):
    global oldiat
    low_r = 50 # chart low range
    hi_r = 250 # chart hi range
    if liat != oldiat:
      text9label["text"] = str(liat)
      iattempangle = (120 * (hi_r - liat) / (hi_r - low_r) + 30)
      gauge3.itemconfig(gauge3needle,start = iattempangle)
      gauge3.grid()
      oldiat = liat

def newcoolant(lcoolant):
    global oldcoolant
    low_r = 100 # chart low range
    hi_r = 300 # chart hi range
    if str(lcoolant) != text7label["text"]:
      text7label["text"] = str(lcoolant)
      coolanttempangle = (120 * (hi_r - lcoolant) / (hi_r - low_r) + 30)
      gauge1.itemconfig(gauge1needle,start = coolanttempangle)
      gauge1.grid()
      oldcoolant = lcoolant

def newoiltemp(loiltemp):
    global oldoiltemp
    low_r = 100 # chart low range
    hi_r = 300 # chart hi range
    if loiltemp != oldoiltemp:
      text11label["text"] = str(loiltemp)
      oiltemptempangle = (120 * (hi_r - loiltemp) / (hi_r - low_r) + 30)
      gauge5.itemconfig(gauge5needle,start = oiltemptempangle)
      gauge5.grid()
      oldoiltemp = loiltemp

def newoilpres(loilpres):
    global oldoilpres
    low_r = 0 # chart low range
    hi_r = 80 # chart hi range
    if loilpres != oldoilpres:
      text12label["text"] = str(loilpres)
      oilprestempangle = (120 * (hi_r - loilpres) / (hi_r - low_r) + 30)
      gauge6.itemconfig(gauge6needle,start = oilprestempangle)
      gauge6.grid()
      oldoilpres = loilpres

def newtilt(ltilt):
    global oldtilt
    global filteredTilt
    FILTER = 0.05 # 0.10 = smoother, 0.25 = more responsive
    filteredTilt += FILTER * ((ltilt * -1) - filteredTilt)
    if filteredTilt != oldtilt:
       oldtilt = filteredTilt
       updatehorizon()

def newroll(lroll):
    global oldroll
    global filteredRoll
    FILTER = 0.05 # 0.10 = smoother, 0.25 = more responsive
    filteredRoll += FILTER * ((lroll * -1) - filteredRoll)
    if filteredRoll != oldroll:
       oldroll = filteredRoll
       updatehorizon()

def newboost(lboost):
    global oldboost
    low_r = -35 # chart low range
    hi_r = 35 # chart hi range
    if lboost != oldboost:
      text10label["text"] = str(lboost)
      boosttempangle = (120 * (hi_r - lboost) / (hi_r - low_r) + 30)
      gauge4.itemconfig(gauge4needle,start = boosttempangle)
      gauge4.grid()
      oldboost = lboost

def newbaro(lbaro):
    global oldbaro
    oldbaro = lbaro

def newcurrentgear(lcurrentgear):
    global oldcurrentgear
    if oldcurrentgear != lcurrentgear:
        oldcurrentgear = lcurrentgear
        text4label["text"] = str(lcurrentgear)

def newinputrpm(linputrpm):
    global oldinputrpm
    if oldinputrpm != linputrpm:
        oldinputrpm = linputrpm
        updatetach()

def newbatterytemp(index, value):
    global oldbatterytemps
    global packtempmin
    global packtempmax
    global packtempavg
    global packtempdelta
    if oldbatterytemps[index] != value:
        oldbatterytemps[index] = value
        validtemps = [t for t in oldbatterytemps if t > 0]
        batterycanvas.itemconfig(
            batterytexts[index],
            text=f"{value}°")
        low_t = 50
        high_t = 160
        clipped = max(low_t, min(high_t, value))
        height = int((clipped - low_t) * 2)
        color = "green"
        if value > 89:
            color = "yellow"
        if value > 99:
            color = "orange"
        if value > 109:
            color = "red"
        x = 20 + (index * 41)
        batterycanvas.coords(
            batterybars[index],
            x,
            320 - height,
            x + 30,
            320)
        batterycanvas.itemconfig(
            batterybars[index],
            fill=color)
        batterycanvas.coords(
            batterytexts[index],
            x + 22,
            305 - height)
        if len(validtemps) == 18:
            packmin = min(validtemps)
            packmax = max(validtemps)
            packavg = round(sum(validtemps) / len(validtemps), 1)
            packdelta = packmax - packmin
            text5label["text"] = str(packmax)

def newbatterykw():
    global oldbatterycurrent
    global packvoltage
    if packvoltage is None or oldbatterycurrent is None:
        return
    livekw = round(
        (packvoltage * oldbatterycurrent) / 1000,
        1)
    text6label["text"] = str(livekw)

def newbatterycurrent(lbatterycurrent):
    global oldbatterycurrent
    if lbatterycurrent != oldbatterycurrent:
        oldbatterycurrent = lbatterycurrent
        newbatterykw()

def newacmode(lacmode):
    global oldacmode
    if lacmode != oldacmode:
        oldbacmode = lacmode
        actext1label["text"] = str(lacmode)

def newrecirc(lrecirc):
    global oldrecirc
    if lrecirc != oldrecirc:
        oldrecirc = lrecirc
        actext3label["text"] = f"{lrecirc:#04x}"

def newevaptemp(levaptemp):
    global oldevaptemp
    if levaptemp != oldevaptemp:
        oldevaptemp = levaptemp
        actext2label["text"] = str(levaptemp)

def newdimmer(ldimmer):
    global olddimmer
    global dark_mode
    if olddimmer != ldimmer:
        olddimmer = ldimmer
        if ldimmer == 0:
            if dark_mode:
                print("Dimmer off")
                toggleDark()
        else:
            if not dark_mode:
                print("Dimmer on")
                toggleDark()

def newignition(lignition):
    global oldignition
    if oldignition != lignition:
        oldignition = lignition
        if lignition == 0:
            print("Activating Screensaver")
            try:
                subprocess.call(['xscreensaver-command', '-activate'])
            except:
                print('No Screensaver Available -activate')
        else:
            print("Deactivating Screensaver")
            try:
                subprocess.call(['xscreensaver-command', '-deactivate'])
            except:
                print('No Screensaver Available -deactivate')
            

def newcellvoltage(index, value):
    global avgcellvoltage
    global packvoltage
    global mincellvoltage
    global maxcellvoltage
    if cellvoltages[index] is not value:
        cellvoltages[index] = value
        validcells = [
            v for v in cellvoltages
            if 2.0 < v < 4.5
            ]
        if len(validcells) > 0:
            avgcellvoltage = round(
                sum(validcells) / len(validcells),
                3)
            mincellvoltage = round(min(validcells), 3)
            maxcellvoltage = round(max(validcells), 3)
        if len(validcells) == 96:
            lpackvoltage = round(
                sum(validcells),
                1)
            if packvoltage is not lpackvoltage:
                packvoltage = lpackvoltage
                newbatterykw()
    if index == 95:
        updatepackvoltages()

def newgps(lgps):
    global oldgps
    textgps = str()
    for i in lgps:
        textgps += f"{i} " ""
    #print(textgps)
    oldgps[0] = lgps[0]
    oldgps[1] = lgps[1]  
    actext4label["text"] = round(oldgps[0],5)
    actext5label["text"] = round(oldgps[1],5)

def updatehorizon():
    global oldtilt
    global oldroll
    cx = 100
    cy = 87.5
    pitchscale = 1.5
    length = 75
    p = max(-20, min(20, oldtilt)) # keep the line on the display
    yc = cy - p * pitchscale
    theta = math.radians(oldroll)
    dx = length * math.cos(theta)
    dy = length * math.sin(theta)
    x1 = cx - dx
    y1 = yc + dy
    x2 = cx + dx
    y2 = yc - dy
    angle = max(abs(oldtilt), abs(oldroll))
    if angle < 15:
        color = "lime"
    elif angle < 25:
        color = "yellow"
    elif angle < 35:
        color = "orange"
    else:
        color = "red"
    horizoncanvas.coords(
        horizonline,
        x1, y1,
        x2, y2
    )
    horizoncanvas.itemconfig(
        horizonline,
        fill=color
    )
    roundtilt=abs(round(oldtilt))
    horizoncanvas.itemconfig(
        pitchtext,
        text=f"P:{roundtilt}°"
    )
    roundroll=abs(round(oldroll))
    horizoncanvas.itemconfig(
        rolltext,
        text=f"R:{roundroll}°"
    )

def updatetach():
    global oldrpm
    global oldinputrpm
    cx = 100
    cy = 87.5
    radius = 85
    deadband = 50
    enginedeg = -210 + (oldrpm/7000.0)*240
    inputdeg  = -210 + (oldinputrpm/7000.0)*240
    engineangle = math.radians(enginedeg)
    engx = cx + (radius-22)*math.cos(engineangle)
    engy = cy + (radius-22)*math.sin(engineangle)
    tachometer.coords(engineneedle,
      cx,cy,
      engx,engy)
    inputangle = math.radians(inputdeg)
    inx = cx + (radius-30)*math.cos(inputangle)
    iny = cy + (radius-30)*math.sin(inputangle)
    tachometer.coords(transneedle,
      cx,cy,
      inx,iny)
    arc_engine = 360 - enginedeg
    arc_input  = 360 - inputdeg
    extent = arc_input - arc_engine
    while extent > 180:
        extent -= 360
    while extent < -180:
        extent += 360
    rpmdiff = oldinputrpm - oldrpm
    if rpmdiff > 50:
        color = "green"
    elif rpmdiff < -50:
        color = "firebrick"
    else:
        color = "yellow"
    tachometer.itemconfig(
        tachometerarc,
        start=arc_engine,
        extent=extent,
        outline=color,
        width=10)

def updatepackvoltages():
    global packavg
    for pack in range(8):
        start = pack * 12
        end = start + 12
        vals = cellvoltages[start:end]
        if vals:
            #avg = sum(vals) / len(vals)
            avg = sum(vals)
            packavg[pack] = round(avg,1)
            packlabels[pack].config(text=f"{packavg[pack]:.1f}")


# list of can ID's and details to monitor in this order:
# (ID, Channel, [("name", process, type, function, byte1, byte2)])
monitorlist=[(0x2C2,
              canIHS,
              [("Batt V",volt,newbattv,2)]),
             (0x02B,
              canC,
              [("Roll",tilt,newroll,0,1),
               ("Tilt",tilt,newtilt,2,3)]),
             (0x322,
              canIHS,
              [("RPM",rpm,newrpm,0,1),
               ("MPH",mph,newmph,2,3)]),
             (0x127,
              canC,
              [("IAT",temp,newiat,0),
               ("Coolant",temp,newcoolant,1),
               ("BARO",baro,newbaro,2)]),
             (0x13D,
              canC,
              [("Oil Temp",temp,newoiltemp,3),
               ("Oil Pres",psi,newoilpres,2)]),
             (0x093,
              canC,
              [("Gear",gear,newgear,2)]),
             (0x277,
              canC,
              [("Transfer",xfer,newxfer,0)]),
             (0x128,
              canC,
              [("PS Temp",pstemp,newpstemp,1)]),
              (0x081,
              canC,
              [("MAP",boost,newboost,2,4)]),
             (0x4A0,
              canC,
              [("Temp1", temp, lambda v: newbatterytemp(0, v), 0),
               ("Temp2", temp, lambda v: newbatterytemp(1, v), 1),
               ("Temp3", temp, lambda v: newbatterytemp(2, v), 2),
               ("Temp4", temp, lambda v: newbatterytemp(3, v), 3),
               ("Temp5", temp, lambda v: newbatterytemp(4, v), 4),
               ("Temp6", temp, lambda v: newbatterytemp(5, v), 5)]),
             (0x4A1,
              canC,
              [("Temp7", temp, lambda v: newbatterytemp(6, v), 0),
               ("Temp8", temp, lambda v: newbatterytemp(7, v), 1),
               ("Temp9", temp, lambda v: newbatterytemp(8, v), 2),
               ("Temp10", temp, lambda v: newbatterytemp(9, v), 3),
               ("Temp11", temp, lambda v: newbatterytemp(10, v), 4),
               ("Temp12", temp, lambda v: newbatterytemp(11, v), 5)]),
             (0x4A2,
              canC,
              [("Temp13", temp, lambda v: newbatterytemp(12, v), 0),
               ("Temp14", temp, lambda v: newbatterytemp(13, v), 1),
               ("Temp15", temp, lambda v: newbatterytemp(14, v), 4),
               ("Temp16", temp, lambda v: newbatterytemp(15, v), 5),
               ("Temp17", temp, lambda v: newbatterytemp(16, v), 6),
               ("Temp18", temp, lambda v: newbatterytemp(17, v), 7)]),  
             (0x485,
              canC,
              [("BatteryCurrent",batterycurrent,newbatterycurrent,0)]),
             (0x085,
              canC,
              [("CurrentGear",curgear,newcurrentgear,1),
               ("InputRPM",rpm,newinputrpm,5,6)]),
             (0x230,
              canIHS,
              [("ACmode",acmode,newacmode,0),
               ("UnknTemp",temp,newevaptemp,1),
               ("Unknown",raw8,newrecirc,3)]),
             (0x291,
              canC,
              [("Dimmer",raw8,newdimmer,6)]),
             (0x077,
              canC,
              [("Ignition",raw8,newignition,0)]),
             (0x36C,
              canIHS,
              [("GPS",can36c_to_wgs84,newgps)])
             ]
for canid in range(0x487, 0x49F):
    basecell = (canid - 0x487) * 4
    monitorlist.append(
        (canid,
         canC,
         [
          (f"Cell{basecell}",
           cellvoltage,
           lambda v, i=basecell:
               newcellvoltage(i, v),
           0),
          (f"Cell{basecell+1}",
           cellvoltage,
           lambda v, i=basecell+1:
               newcellvoltage(i, v),
           2),
            (f"Cell{basecell+2}",
             cellvoltage,
             lambda v, i=basecell+2:
                newcellvoltage(i, v),
             4),
            (f"Cell{basecell+3}",
             cellvoltage,
             lambda v, i=basecell+3:
                 newcellvoltage(i, v),
             6)
         ]))


# Button commands
def maxac():
  maxaccmd = can.Message(data=[0x80, 0, 0, 0, 0, 0], is_extended_id=False, arbitration_id=0x342, channel=canIHS)
  bus.send(maxaccmd, timeout=1)

def synchvac():
  synchvaccmd = can.Message(data=[0, 0, 0, 0x04, 0], is_extended_id=False, arbitration_id=0x342, channel=canIHS)
  bus.send(synchvaccmd, timeout=1)

def gpslink():
    webbrowser.open(f"https://www.google.com/maps/search/?api=1&query={oldgps[0]},{oldgps[1]}")

def togglePage(page):
    global currentPage
    global cam
    gaugeframe.pack_forget()
    acframe.pack_forget()
    batteryframe.pack_forget()
    batterybutton.config(relief=RAISED, bg=backgroundcolor, activebackground=backgroundcolor)
    acbutton.config(relief=RAISED, bg=backgroundcolor, activebackground=backgroundcolor)
    cambutton.config(relief=RAISED, bg=backgroundcolor, activebackground=backgroundcolor)
    if page == currentPage: # Return to Gauge page
        currentPage = 1
        if cam:
            cam.terminate()
            cam = None
            if olddimmer == 0:
                toggledark()
        gaugeframe.pack(side=TOP, fill="x")
    elif page == 2: # Show Battery Page
        currentPage = 2
        batteryframe.pack(side=TOP, fill="both", expand=True)
        batterybutton.config(relief=SUNKEN, bg="yellow", activebackground="yellow")
    elif page == 3: # Show AC Page
        currentPage = 3
        acframe.pack(side=TOP, fill="both", expand=True)
        acbutton.config(relief=SUNKEN, bg="yellow", activebackground="yellow")
    elif page == 4: # Show Camera
        try:
            cam = subprocess.Popen(["raspivid", "-t", "0", "-v", "-w", "800", "-h", "480", "-op", "200"])
        except:
            print("No Camera")
            cam = None
            togglePage(1)
        else:
            camstatus = cam.poll()
            if camstatus is None:
                currentPage = 4
                toggleDark()
                cambutton.config(relief=SUNKEN, bg="yellow", activebackground="yellow")
    else:
        currentPage = 1
        gaugeframe.pack(side=TOP, fill="x")

def toggleDark():
    global dark_mode
    global backgroundcolor
    if dark_mode == True and currentPage != 4:
        dark_mode = None
        backgroundcolor = '#F0F0F0'
        root.tk_setPalette(background=backgroundcolor, foreground='black',
               activeBackground=backgroundcolor, activeForeground='black')
        for children in gaugeframe.children.values():
            children.itemconfigure('gauge', fill='white')
        if currentPage == 2:
            batterybutton.config(relief=SUNKEN, bg="yellow", activebackground="yellow")
        if currentPage == 3:
            acbutton.config(relief=SUNKEN, bg="yellow", activebackground="yellow")
        if currentPage == 4:
            cambutton.config(relief=SUNKEN, bg="yellow", activebackground="yellow")
        horizoncanvas.itemconfigure('gauge', fill='white')
        tachometer.itemconfigure('gauge', fill='white')
        batterycanvas.itemconfigure('text', fill='black')
    else:
        dark_mode = True
        backgroundcolor = 'black'
        root.tk_setPalette(background=backgroundcolor, foreground='white',
               activeBackground=backgroundcolor, activeForeground='white')
        for children in gaugeframe.children.values():
            children.itemconfigure('gauge', fill='grey')
        for b in (
            batterybutton,
            acbutton,
            cambutton,
            dumpbutton,
            darkbutton,
            quitbutton,
            screenoffbutton,
            ):
            b.configure(bg=backgroundcolor, activebackground=backgroundcolor)
        if currentPage == 2:
            batterybutton.config(relief=SUNKEN, bg="yellow", activebackground="yellow")
        if currentPage == 3:
            acbutton.config(relief=SUNKEN, bg="yellow", activebackground="yellow")
        if currentPage == 4:
            cambutton.config(relief=SUNKEN, bg="yellow", activebackground="yellow")
        if dump:
            dumpbutton.config(relief=SUNKEN, bg="yellow", activebackground="yellow")
        horizoncanvas.itemconfigure('gauge', fill='grey')
        tachometer.itemconfigure('gauge', fill='grey')
        batterycanvas.itemconfigure('text', fill='white')


# Subprocess functions - executes external commands
def blankscreen():
    try:
        subprocess.call(['xscreensaver-command', '-activate'])
    except:
        print('No Screensaver Available')

def candump():
    global dump
    if dump:
        dump.terminate()
        dump = None
        dumpbutton.config(relief=RAISED, bg=backgroundcolor, activebackground=backgroundcolor)
    else:
        dump = subprocess.Popen(["candump", "-l", "any", "-n", "1000000", "-T", "1000"])
        dumpbutton.config(relief=SUNKEN, bg="yellow", activebackground="yellow")

def quitprogram(): # Correctly and cleanly close this program
    global notifier
    global bus
    global dump
    global cam
    global root
    global shutting_down
    global queue_after
    shutting_down = True
    notifier.stop(timeout = 1)
    bus.shutdown()
    root.after_cancel(queue_after)
    if dump:
        dump.terminate()
    if cam:
        cam.terminate()
    try:
        root.quit()
    except:
        root.destroy()
    sys.exit(0)


# Special display configuration
def setuphorizondisplay(parent, row, column): # artificial horizon for displaying tilt and roll
    global horizoncanvas
    global horizonline
    global pitchtext
    global rolltext
    w = 200
    h = 175
    cx = w / 2
    cy = h / 2
    radius = 85
    horizoncanvas = Canvas(
        parent,
        width=w,
        height=h,
    )
    horizoncanvas.grid(row=row, column=column)
    horizoncanvas.create_oval( # outer circle
        cx-radius,
        cy-radius,
        cx+radius,
        cy+radius,
        outline="black",
        fill="white",
        width=2,
        tags="gauge"
    )
    for angle in range(-90, 91, 30): # roll tick marks
        a = math.radians(angle - 90)
        outer = radius
        inner = radius - 8
        if angle in (-90, 0, 90):
            inner = radius - 14
        x1 = cx + inner * math.cos(a)
        y1 = cy + inner * math.sin(a)
        x2 = cx + outer * math.cos(a)
        y2 = cy + outer * math.sin(a)
        horizoncanvas.create_line(
            x1, y1, x2, y2,
            fill="black",
            width=2
        )
    horizoncanvas.create_oval( # center dot
        cx-2,
        cy-2,
        cx+2,
        cy+2,
        fill="black",
        outline="black"
    )
    horizonline = horizoncanvas.create_line( # horizon line
        0, 0, 0, 0,
        fill="lime",
        width=10
    )
    pitchtext = horizoncanvas.create_text(
        cx,
        h-40,
        text="P:0°",
        fill="black",
        font=("Helvetica", "16")
    )
    rolltext = horizoncanvas.create_text(
        cx,
        h-20,
        text="R:0°",
        fill="black",
        font=("Helvetica", "16")
    )

def setuptachometer(parent, row, column): # Tachometer
    global tachometer
    global engineneedle
    global transneedle
    global tachometerarc
    w = 200
    h = 175
    cx = w / 2
    cy = h / 2
    radius = 85
    tachometer = Canvas(parent,
        width=w,
        height=h)
    tachometer.grid(row=row, column=column)
    tachometer.create_oval(cx-radius, cy-radius, # outer ring
        cx+radius, cy+radius,
        outline="black",
        fill="white",
        width=2,
        tags="gauge")
    for rpm in range(0, 7001, 500): # tick marks
        angle = math.radians(-210 + (rpm/7000.0)*240)
        x1 = cx + (radius-6)*math.cos(angle)
        y1 = cy + (radius-6)*math.sin(angle)
        if rpm % 1000 == 0:
            x2 = cx + (radius-18)*math.cos(angle)
            y2 = cy + (radius-18)*math.sin(angle)
        else:
            x2 = cx + (radius-12)*math.cos(angle)
            y2 = cy + (radius-12)*math.sin(angle)
        tachometer.create_line(x1,y1,x2,y2,
                       fill="black",
                       width=2)
    for rpm in range(0,8): # labels
        angle = math.radians(-210 + rpm*(240/7))
        tx = cx + (radius-32)*math.cos(angle)
        ty = cy + (radius-32)*math.sin(angle)
        tachometer.create_text(tx,
             ty,
             text=str(rpm),
             fill="black",
             font=("Arial",10,"bold"))
    tachometerarc = tachometer.create_arc( # difference arc
        cx-radius,
        cy-radius,
        cx+radius,
        cy+radius,
        start=0,
        extent=0,
        style=ARC,
        width=10,
        fill="",
        outline=""
        )
    tachometer.create_text(cx, # title text
        cy+48,
        text="RPM x1000",
        fill="black",
        font=("Arial",10))
    engineneedle = tachometer.create_line( # engine RPM needle
        cx, cy,
        cx,
        cy-radius+20,
        fill="black",
        width=10,
        capstyle=ROUND
        )
    transneedle = tachometer.create_line( # transmission input RPM needle
        cx, cy,
        cx,
        cy-radius+28,
        fill="deepskyblue",
        width=8,
        capstyle=ROUND
        )


# Setup the graphics window
root = Tk()
root.geometry("800x480+0+0")
root.title("This is Root")
root.protocol("WM_DELETE_WINDOW", quitprogram)
if args.fullscreen:
    root.attributes("-fullscreen", True)
    

# Setup the button row
buttonframe=Frame(root)
buttonframe.configure()
buttonframe.pack(side=BOTTOM, fill="x")

cambutton = Button(
    buttonframe, text="CAMERA", fg="red", activeforeground="red", font=("Helvetica", "16"), highlightthickness=3, highlightbackground="grey", height=2, width=7, command=lambda: togglePage(4))
cambutton.pack(side=LEFT)
acbutton = Button(
    buttonframe, text="AC", fg="red", activeforeground="red", font=("Helvetica", "16"), highlightthickness=3, highlightbackground="grey", height=2, width=7, command=lambda: togglePage(3))
acbutton.pack(side=LEFT)
batterybutton = Button(
    buttonframe, text="BATTERY", fg="red", activeforeground="red", font=("Helvetica", "16"), highlightthickness=3, highlightbackground="grey", height=2, width=7, command=lambda: togglePage(2))
batterybutton.pack(side=LEFT)
dumpbutton = Button(
    buttonframe, text="CANDUMP", fg="red", activeforeground="red", font=("Helvetica", "16"), highlightthickness=3, highlightbackground="grey", height=2, width=7, command=candump)
dumpbutton.pack(side=LEFT)
darkbutton = Button(
    buttonframe, text="DARK", fg="red", activeforeground="red", font=("Helvetica", "16"), highlightthickness=3, highlightbackground="grey", height=2, width=7, command=toggleDark)
darkbutton.pack(side=LEFT)
quitbutton = Button(
    buttonframe, text="QUIT", fg="red", activeforeground="red", font=("Helvetica", "16"), highlightthickness=3, highlightbackground="grey", height=2, width=7, command=quitprogram)
quitbutton.pack(side=LEFT)
screenoffbutton = Button(
    buttonframe, text="Screen OFF", fg="red", activeforeground="red", font=("Helvetica", "16"), wraplength=100, highlightthickness=3, highlightbackground="grey", height=2, width=7, command=blankscreen)
screenoffbutton.pack(side=LEFT)


# Setup the text row
textframe=Frame(root)
textframe.pack(side=BOTTOM, fill="x")

text1dsc = Label(textframe, text="MPH", font=("Helvetica", "16"))
text1dsc.pack(side=LEFT)
text1label = Label(textframe, font=("Helvetica", "16"), width=5)
text1label.pack(side=LEFT)

text2dsc = Label(textframe, text="Batt V", font=("Helvetica", "16"))
text2dsc.pack(side=LEFT)
text2label = Label(textframe, font=("Helvetica", "16"), width=5)
text2label.pack(side=LEFT)

text3dsc = Label(textframe, text="Select", font=("Helvetica", "16"))
text3dsc.pack(side=LEFT)
text3label = Label(textframe, font=("Helvetica", "16"), width=5)
text3label.pack(side=LEFT)

text4dsc = Label(textframe, text="Current", font=("Helvetica", "16"))
text4dsc.pack(side=LEFT)
text4label = Label(textframe, font=("Helvetica", "16"), width=5)
text4label.pack(side=LEFT)

text5dsc = Label(textframe, text="PMax", font=("Helvetica", "16"))
text5dsc.pack(side=LEFT)
text5label = Label(textframe, font=("Helvetica", "16"), width=5)
text5label.pack(side=LEFT)

text6dsc = Label(textframe, text="Live KW", font=("Helvetica", "16"))
text6dsc.pack(side=LEFT)
text6label = Label(textframe, font=("Helvetica", "16"), width=5)
text6label.pack(side=LEFT)

textframe2=Frame(root)
textframe2.pack(side=BOTTOM, fill="x")

text7dsc = Label(textframe2, text="CoolT", font=("Helvetica", "16"))
text7dsc.pack(side=LEFT)
text7label = Label(textframe2, font=("Helvetica", "16"), width=5)
text7label.pack(side=LEFT)

text8dsc = Label(textframe2, text="PsTemp", font=("Helvetica", "16"))
text8dsc.pack(side=LEFT)
text8label = Label(textframe2, font=("Helvetica", "16"), width=5)
text8label.pack(side=LEFT)

text9dsc = Label(textframe2, text="IAT", font=("Helvetica", "16"))
text9dsc.pack(side=LEFT)
text9label = Label(textframe2, font=("Helvetica", "16"), width=5)
text9label.pack(side=LEFT)

text10dsc = Label(textframe2, text="MAP", font=("Helvetica", "16"))
text10dsc.pack(side=LEFT)
text10label = Label(textframe2, font=("Helvetica", "16"), width=5)
text10label.pack(side=LEFT)

text11dsc = Label(textframe2, text="Oil", font=("Helvetica", "16"))
text11dsc.pack(side=LEFT)
text11label = Label(textframe2, font=("Helvetica", "16"), width=5)
text11label.pack(side=LEFT)

text12dsc = Label(textframe2, text="OilPres", font=("Helvetica", "16"))
text12dsc.pack(side=LEFT)
text12label = Label(textframe2, font=("Helvetica", "16"), width=5)
text12label.pack(side=LEFT)


# Setup the gauge frame
gaugeframe = Frame(root)
gaugeframe.pack(side=TOP, fill="x")
gaugeframe.configure(bg='black')

coord = 0, 0, 200, 350 # define the size of the gauge
fullcoord = 0, 0, 175, 175

gauge1 = Canvas(gaugeframe, width=200, height=175)
gauge1.grid(row=1, column=1)
gauge1.create_arc(coord, start=30, extent=120, fill="white",  width=2, tags="gauge")
gauge1desc = gauge1.create_text(100,120, text="CoolT", font=("Helvetica", "16"))
gauge1needle = gauge1.create_arc(coord, start= 150, extent=1, width=7)

gauge2 = Canvas(gaugeframe, width=200, height=175)
gauge2.grid(row=1, column=2)
gauge2.create_arc(coord, start=30, extent=120, fill="white",  width=2, tags="gauge")
gauge2desc = gauge2.create_text(100,120, text="PSTEMP", font=("Helvetica", "16"))
gauge2label = gauge2.create_text(100,80, text="", font=("Helvetica", "16"))
gauge2needle = gauge2.create_arc(coord, start= 150, extent=1, width=7)

gauge3 = Canvas(gaugeframe, width=200, height=175)
gauge3.grid(row=1, column=3)
gauge3.create_arc(coord, start=30, extent=120, fill="white",  width=2, tags="gauge")
gauge3desc = gauge3.create_text(100,120, text="IAT", font=("Helvetica", "16"))
gauge3label = gauge3.create_text(100,80, text="", font=("Helvetica", "16"))
gauge3needle = gauge3.create_arc(coord, start= 150, extent=1, width=7)

gauge4 = Canvas(gaugeframe, width=200, height=175)
gauge4.grid(row=1, column=4)
gauge4.create_arc(coord, start=30, extent=120, fill="white",  width=2, tags="gauge")
gauge4desc = gauge4.create_text(100,120, text="MAP", font=("Helvetica", "16"))
gauge4needle = gauge4.create_arc(coord, start= 150, extent=1, width=7)

gauge5 = Canvas(gaugeframe, width=200, height=175)
gauge5.grid(row=2, column=1)
gauge5.create_arc(coord, start=30, extent=120, fill="white",  width=2, tags="gauge")
gauge5desc = gauge5.create_text(100,120, text="OilTemp", font=("Helvetica", "16"))
gauge5needle = gauge5.create_arc(coord, start= 150, extent=1, width=7)

gauge6 = Canvas(gaugeframe, width=200, height=175)
gauge6.grid(row=2, column=2)
gauge6.create_arc(coord, start=30, extent=120, fill="white",  width=2, tags="gauge")
gauge6desc = gauge6.create_text(100,120, text="OilPres", font=("Helvetica", "16"))
gauge6label = gauge6.create_text(100,80, text="", font=("Helvetica", "16"))
gauge6needle = gauge6.create_arc(coord, start= 150, extent=1, width=7)

gauge7 = Canvas(gaugeframe, width=200, height=175)
gauge7.grid(row=2, column=3)
setuptachometer(gauge7,row=2, column=3)

gauge8 = Canvas(gaugeframe, width=200, height=175)
gauge8.grid(row=2, column=4)
setuphorizondisplay(gauge8,row=2, column=4)


# Setup battery frame
batteryframe = Frame(root)
batterycanvas = Canvas(
    batteryframe,
    width=800,
    height=350,
    highlightthickness=0)
batterylabels = [
    label
    for canid, _, signals in monitorlist
    if 0x4A0 <= canid <= 0x4A2
    for label, _, _, _ in signals
]
batterycanvas.create_text(
        400,
        20,
        text="4xe HV Battery Voltages",
        fill="black",
        tags="text",
        font=("Helvetica", "20", "bold"))
packlabels = []
for i in range(8):
    x = 75 + (i % 8) * 90
    y = 55 + (i // 8) * 44
    # Pack title
    batterycanvas.create_text(
        x,
        y,
        text=f"Pack {i+1}",
        tags="text",
        font=("Arial",12,"bold")
    )
    # Average voltage
    lbl = Label(
        batterycanvas,
        text="00.0",
        width=6,
        font=("Courier",14,"bold")
    )
    batterycanvas.create_window(
        x,
        y + 24,
        window=lbl
    )
    packlabels.append(lbl)
batterycanvas.create_text(
        400,
        150,
        text="4xe HV Battery Temperatures",
        fill="black",
        tags="text",
        font=("Helvetica", "20", "bold"))
for i in range(18):
        x = 30 + (i * 41)
        bar = batterycanvas.create_rectangle(
            x,
            280,
            x + 30,
            320,
            fill="green",
            outline="white",
            width=2)
        batterybars.append(bar)
        temptext = batterycanvas.create_text(
            x + 14,
            240,
            text="0°",
            fill="black",
            tags="text",
            font=("Helvetica", "10", "bold"))
        batterytexts.append(temptext)
        label = batterycanvas.create_text(
            x + 8,
            320,
            text=batterylabels[i],
            fill="black",
            tags="text",
            angle=45,
            font=("Helvetica", "8"))
        batterylabelsdrawn.append(label)
batterycanvas.pack(fill="both", expand=True)


# Setup the AC frame
acframe = Frame(root)
accanvas = Canvas(
    acframe,
    width=800,
    height=350,
    highlightthickness=0)
maxacbutton = Button(
    acframe, text="MAX AC", fg="red", activeforeground="red", bg="black", activebackground="black", font=("Helvetica", "16"), height=2, width=7, command=maxac)
maxacbutton.grid(row=1, column=1)
syncacbutton = Button(
    acframe, text="SYNC AC", fg="red", activeforeground="red", bg="black", activebackground="black", font=("Helvetica", "16"), height=2, width=7, command=synchvac)
syncacbutton.grid(row=1, column=2)
gpslinkbutton = Button(
    acframe, text="GPS Link", fg="red", activeforeground="red", bg="black", activebackground="black", font=("Helvetica", "16"), height=2, width=7, command=gpslink)
gpslinkbutton.grid(row=1, column=5)

actext1dsc = Label(acframe, text="ACMode", font=("Helvetica", "16"))
actext1dsc.grid(row=2, column=1)
actext1label = Label(acframe, font=("Helvetica", "16"), width=5)
actext1label.grid(row=3, column=1)

actext2dsc = Label(acframe, text="Unknown T", font=("Helvetica", "16"))
actext2dsc.grid(row=2, column=2)
actext2label = Label(acframe, font=("Helvetica", "16"), width=5)
actext2label.grid(row=3, column=2)

actext3dsc = Label(acframe, text="Unknown", font=("Helvetica", "16"))
actext3dsc.grid(row=2, column=3)
actext3label = Label(acframe, font=("Helvetica", "16"), width=5)
actext3label.grid(row=3, column=3)

actext4dsc = Label(acframe, text="Lat", font=("Helvetica", "16"))
actext4dsc.grid(row=2, column=4)
actext4label = Label(acframe, font=("Helvetica", "16"), width=10)
actext4label.grid(row=3, column=4)

actext5dsc = Label(acframe, text="Long", font=("Helvetica", "16"))
actext5dsc.grid(row=2, column=5)
actext5label = Label(acframe, font=("Helvetica", "16"), width=10)
actext5label.grid(row=3, column=5)


# Queue every single message received from the canbus
gui_queue = queue.Queue()

def newmsg(msg):
  if shutting_down:
   return
  for monitor in monitorlist:
   if msg.arbitration_id == monitor[0] and msg.channel == monitor[1]:
    for detail in monitor[2]:
     name = detail[0]
     decoder = detail[1]
     callbk = detail[2]
     args = detail[3:]
     value = decoder(msg.data, *args)
     gui_queue.put((callbk, value))


# Build out the can bus filtering list. only receive messages that we care about.
for monitor in monitorlist:
 canFilter.append({"can_id": monitor[0], "can_mask": 0xFFF, "can_channel": monitor[1]})


# Define the can bus
bus = can.interface.Bus('', interface='socketcan', filter=canFilter)
notifier = can.Notifier(bus, [newmsg], loop=None)


# Forces tkinter to periodically look for external signals/interrupts and run things while in mainloop()
def check_signals():
    global dump
    global cam
    if dump: # Check if candump has closed and if so reset the button
        poll = dump.poll()
        if poll is not None:
            candump()
    if cam: # Check if raspivid has closed and if so reset the button
        poll = cam.poll()
        if poll is not None:
            togglePage(4)
    root.after(1000, check_signals)

root.after(100, check_signals)


# Process all of the queued the can messages inside tkinter mainloop()
def process_gui_queue():
    global queue_after
    while True:
        try:
            callbk, value = gui_queue.get_nowait()
        except queue.Empty:
            break
        try:
            callbk(value)
        except Exception as e:
            print(f"GUI callback {callbk.__name__} failed: {e}")
    queue_after = root.after(10, process_gui_queue)

queue_after = root.after(10, process_gui_queue)


# Start the tkinter mainloop and shutdown cleanly when closed
try:
    root.mainloop()
except KeyboardInterrupt:
    print("\nKeyboardInterrupt detected. Closing GUI safely...")
finally:
    quitprogram()

