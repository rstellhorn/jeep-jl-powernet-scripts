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


# Use parser to provide help and command line options
parser = argparse.ArgumentParser("GUI dashboard canbus data display built for 2018+ Jeep JL/JT/etc... products")
parser.add_argument('--vcan', action='store_true',
                    help='Use VCAN0 and VCAN1 for testing')
parser.add_argument('--fullscreen', '-f', action='store_true',
                    help='Turn off Full Screen for testing')
args = parser.parse_args()


# If using vcan for log playback, change the values in the quotes below
if args.vcan:
    canIHS = "vcan0"
    canC = "vcan1"
else:
    canIHS = "can0"
    canC = "can1"

# Initialize variables
canFilter = list()
shutting_down = False
cam = None
dump = None
oldpstemp = None
oldrpm = None
oldtilt = None
oldroll = None
oldiat = None
oldcoolant = None
oldoiltemp = None
oldoilpres = None
oldboost = None
oldbaro = 0

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
    return GEARS.get(x[a], "?")

def xfer(x,a): #Transfer Case gear selection
    XFERS = {
        0x00: "2H",
        0x02: "N",
        0x10: "4H",
        0x20: "N",
        0x40: "4L",
        0x80: "XX",
        }
    return XFERS.get(x[a], "?")


# Display Functions
def newrpm(lrpm):
    global oldrpm
    low_r = 0 # chart low range
    hi_r = 7000 # chart hi range
    if lrpm == 65535:
      lrpm = 0
    if lrpm != oldrpm:
      oldrpm = lrpm

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
    if str(lxfer) != text4label["text"]:
        text4label["text"] = str(lxfer)

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
    if ltilt != oldtilt:
       gauge7.itemconfig(gauge7label, text=str(ltilt))
       gauge7.itemconfig(gauge7needle, start=ltilt)
       gauge7.grid()
       oldtilt = ltilt
       if ltilt > 15:
               gauge7.itemconfig(gauge7needle, fill="yellow")
       if ltilt > 25:
               gauge7.itemconfig(gauge7needle, fill="red")
       else:
               gauge7.itemconfig(gauge7needle, fill="green")

def newroll(lroll):
    global oldroll
    if lroll != oldroll:
       gauge8.itemconfig(gauge8label, text=str(lroll))
       gauge8.itemconfig(gauge8needle, start=lroll)
       gauge8.grid()
       oldroll = lroll
       if lroll > 15:
               gauge8.itemconfig(gauge8needle, fill="yellow")
       if lroll > 25:
               gauge8.itemconfig(gauge8needle, fill="red")
       else:
               gauge8.itemconfig(gauge8needle, fill="green")

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
              [("MAP",boost,newboost,2,4)])
             ]


# Button commands
def maxac():
  maxaccmd = can.Message(data=[0x80, 0, 0, 0, 0, 0], is_extended_id=False, arbitration_id=0x342, channel=canIHS)
  bus.send(maxaccmd, timeout=1)

def synchvac():
  synchvaccmd = can.Message(data=[0, 0, 0, 0x04, 0], is_extended_id=False, arbitration_id=0x342, channel=canIHS)
  bus.send(synchvaccmd, timeout=1)


# Subprocess functions - executes external commands
def blankscreen():
    subprocess.call(['xscreensaver-command', '-activate'])

def camera():
    global cam
    if cam:
        cam.terminate()
        cam = None
        frame.pack(side=TOP, fill="x")
    else:
        cam = subprocess.Popen(["raspivid", "-t", "0", "-v", "-w", "800", "-h", "480", "-op", "200"])
        camstatus = cam.poll()
        if camstatus is None:
                frame.pack_forget()

def candump():
    global dump
    if dump:
        dump.terminate()
        dump = None
        bigbutton2.config(relief=RAISED, bg="black", activebackground="black")
    else:
        dump = subprocess.Popen(["candump", "-l", "any", "-n", "50000", "-T", "1000"])
        bigbutton2.config(relief=SUNKEN, bg="yellow", activebackground="yellow")


# Correctly and cleanly close this program
def quitprogram():
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
    root.quit()
    root.destroy()
    sys.exit(0)


# Setup the graphics window
root = Tk()
root.geometry("800x480+0+0")
root.title("This is Root")
root.protocol("WM_DELETE_WINDOW", quitprogram)
if args.fullscreen:
    root.attributes("-fullscreen", True)
root.configure(bg='black')


# Setup the button row
topframe=Frame(root)
topframe.configure(bg='black')
topframe.pack(side=BOTTOM, fill="x")

bigbutton1 = Button(
    topframe, text="CAMERA", fg="red", activeforeground="red", bg="black", activebackground="black", font=("Helvetica", "16"), height=2, width=7, command=camera)
bigbutton1.pack(side=LEFT)
bigbutton2 = Button(
    topframe, text="CANDUMP", fg="red", activeforeground="red", bg="black", activebackground="black", font=("Helvetica", "16"), height=2, width=7, command=candump)
bigbutton2.pack(side=LEFT)
maxacbutton = Button(
    topframe, text="MAX AC", fg="red", activeforeground="red", bg="black", activebackground="black", font=("Helvetica", "16"), height=2, width=7, command=maxac)
maxacbutton.pack(side=LEFT)
batterybutton = Button(
    topframe, text="SYNC AC", fg="red", activeforeground="red", bg="black", activebackground="black", font=("Helvetica", "16"), height=2, width=7, command=synchvac)
batterybutton.pack(side=LEFT)
quitbutton = Button(
    topframe, text="QUIT", fg="red", activeforeground="red", bg="black", activebackground="black", font=("Helvetica", "16"), height=2, width=7, command=quitprogram)
quitbutton.pack(side=LEFT)
screenoffbutton = Button(
    topframe, text="Screen OFF", fg="red", activeforeground="red", bg="black", activebackground="black", font=("Helvetica", "16"), height=2, width=7, command=blankscreen)
screenoffbutton.pack(side=LEFT)
radiorebootbutton = Button(
    topframe, text="BUTTON7", fg="red", activeforeground="red", bg="black", activebackground="black", font=("Helvetica", "16"), height=2, width=7)
radiorebootbutton.pack(side=LEFT)


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

text3dsc = Label(textframe, text="Gear", font=("Helvetica", "16"))
text3dsc.pack(side=LEFT)
text3label = Label(textframe, font=("Helvetica", "16"), width=5)
text3label.pack(side=LEFT)

text4dsc = Label(textframe, text="Xfer", font=("Helvetica", "16"))
text4dsc.pack(side=LEFT)
text4label = Label(textframe, font=("Helvetica", "16"), width=5)
text4label.pack(side=LEFT)

text5dsc = Label(textframe, text="", font=("Helvetica", "16"))
text5dsc.pack(side=LEFT)
text5label = Label(textframe, font=("Helvetica", "16"), width=5)
text5label.pack(side=LEFT)

text6dsc = Label(textframe, text="", font=("Helvetica", "16"))
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


# Setup the gauge display
frame = Frame(root)
frame.pack(side=TOP, fill="x")
frame.configure(bg='black')

coord = 0, 0, 200, 350 # define the size of the gauge
fullcoord = 0, 0, 175, 175

gauge1 = Canvas(frame, width=200, height=175)
gauge1.grid(row=1, column=1)
gauge1.create_arc(coord, start=30, extent=120, fill="white",  width=2)
gauge1desc = gauge1.create_text(100,120, text="CoolT", font=("Helvetica", "16"))
gauge1needle = gauge1.create_arc(coord, start= 150, extent=1, width=7)

gauge2 = Canvas(frame, width=200, height=175)
gauge2.grid(row=1, column=2)
gauge2.create_arc(coord, start=30, extent=120, fill="white",  width=2)
gauge2desc = gauge2.create_text(100,120, text="PSTEMP", font=("Helvetica", "16"))
gauge2label = gauge2.create_text(100,80, text="", font=("Helvetica", "16"))
gauge2needle = gauge2.create_arc(coord, start= 150, extent=1, width=7)

gauge3 = Canvas(frame, width=200, height=175)
gauge3.grid(row=1, column=3)
gauge3.create_arc(coord, start=30, extent=120, fill="white",  width=2)
gauge3desc = gauge3.create_text(100,120, text="IAT", font=("Helvetica", "16"))
gauge3label = gauge3.create_text(100,80, text="", font=("Helvetica", "16"))
gauge3needle = gauge3.create_arc(coord, start= 150, extent=1, width=7)

gauge4 = Canvas(frame, width=200, height=175)
gauge4.grid(row=1, column=4)
gauge4.create_arc(coord, start=30, extent=120, fill="white",  width=2)
gauge4desc = gauge4.create_text(100,120, text="MAP", font=("Helvetica", "16"))
gauge4needle = gauge4.create_arc(coord, start= 150, extent=1, width=7)

gauge5 = Canvas(frame, width=200, height=175)
gauge5.grid(row=2, column=1)
gauge5.create_arc(coord, start=30, extent=120, fill="white",  width=2)
gauge5desc = gauge5.create_text(100,120, text="OilTemp", font=("Helvetica", "16"))
gauge5needle = gauge5.create_arc(coord, start= 150, extent=1, width=7)

gauge6 = Canvas(frame, width=200, height=175)
gauge6.grid(row=2, column=2)
gauge6.create_arc(coord, start=30, extent=120, fill="white",  width=2)
gauge6desc = gauge6.create_text(100,120, text="OilPres", font=("Helvetica", "16"))
gauge6label = gauge6.create_text(100,80, text="", font=("Helvetica", "16"))
gauge6needle = gauge6.create_arc(coord, start= 150, extent=1, width=7)

gauge7 = Canvas(frame, width=200, height=175)
gauge7.grid(row=2, column=3)
gauge7.create_oval(fullcoord, fill="white",  width=2)
gauge7desc = gauge7.create_text(100,120, text="TILT", font=("Helvetica", "16"))
gauge7label = gauge7.create_text(100,140, text="", font=("Helvetica", "16"))
gauge7needle = gauge7.create_arc(fullcoord, start= 0, extent=180, width=7, fill="green")

gauge8 = Canvas(frame, width=200, height=175)
gauge8.grid(row=2, column=4)
gauge8.create_oval(fullcoord, fill="white",  width=2)
gauge8desc = gauge8.create_text(100,120, text="ROLL", font=("Helvetica", "16"))
gauge8label = gauge8.create_text(100,140, text="", font=("Helvetica", "16"))
gauge8needle = gauge8.create_arc(fullcoord, start= 0, extent=180, width=7, fill="green")


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
    # Check if candump has closed and if so reset the button
    global dump
    if dump:
        poll = dump.poll()
        if poll is not None:
            dump.terminate()
            dump = None
            bigbutton2.config(relief=RAISED, bg="black", activebackground="black")
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

