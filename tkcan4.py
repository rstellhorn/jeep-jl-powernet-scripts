#!/usr/bin/python3
# GUI Can data display using tkinter

from tkinter import *
import time
import can
import subprocess
import signal

# If using vcan for log playback, change the values in the quotes below
canIHS = "can0"
canC = "can1"

canFilter = list()

battv = None
rpm = None
mph = None
fsstate = True
cam = None
oldpstemp = None
oldrpm = None
oldtilt = None
oldroll = None
oldiat = None
oldcoolant = None
oldoiltemp = None
oldoilpres = None

# defined types to process the data. x = can message , a = byte 1 , b = byte 2
def raw8(x,a):
    return(x[a])

def raw16(x,a,b):
    return((x[a]<<8) + x[b])

def volt(x,a):
    return(x[a] / 10)

def temp(x,a):
    return(round((((x[a] - 40) * (9 / 5)) + 32)))

def tilt(x,a,b):
    return(round(((x[a]<<8) + x[b] - 2048) / 10))

def rpm(x,a,b):
    if x[a] == 0xFF:
        return(0)
    return((x[a]<<8) +  x[b])

def mph(x,a,b):
    return(round(((x[a]<<8) + x[b]) / 200,1))

def psi(x,a):
    return(round(((x[a] * 4) * 0.145038)))

def gear(x,a):
    if x[a] == 0x4E:
        return('N')
    elif x[a] == 0x52:
        return('R')
    elif x[a] == 0x31:
        return('1')
    elif x[a] == 0x32:
        return('2')
    elif x[a] == 0x33:
        return('3')
    elif x[a] == 0x34:
        return('4')
    elif x[a] == 0x35:
        return('5')
    elif x[a] == 0x36:
        return('6')
    elif x[a] == 0x37:
        return('7')
    elif x[a] == 0x38:
        return('8')
    elif x[a] == 0x50:
        return('P')
    elif x[a] == 0x44:
        return('D')

def xfer(x,a):
    if x[a] == 0x00:
        return('2H')
    elif x[a] == 0x02:
        return('N')
    elif x[a] == 0x10:
        return('4H')
    elif x[a] == 0x20:
        return('N')
    elif x[a] == 0x40:
        return('4L')
    elif x[a] == 0x80:
        return('XX')
    else:
        return('??')

def steer(x,a,b):
    return(((x[a]<<8) + x[b]) - 0x1000)

def pstemp(x,a):
    return(round(((x[a] * (9 / 5)) + 32)))


# Display Functions
def full():
        print("full screen")
        global fsstate
        fsstate = not fsstate
        root.attributes("-fullscreen", fsstate)
        if fsstate == True:
            fullbutton.config(relief=SUNKEN, text="Small")
            fullbutton.pack()
        else:
            fullbutton.config(relief=RAISED, text="Full")
            fullbutton.pack()

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
      text1label.pack()

def newbattv(lbattv):
    if str(lbattv) != text2label["text"]:
      text2label["text"] = str(lbattv)
      text2label.pack()

def newgear(lgear):
    if str(lgear) != text3label["text"]:
        text3label["text"] = str(lgear)
        text3label.pack()

def newxfer(lxfer):
    if str(lxfer) != text4label["text"]:
        text4label["text"] = str(lxfer)
        text4label.pack()

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
      text7label.pack()
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
               ("Coolant",temp,newcoolant,1)]),
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
              [("PS Temp",pstemp,newpstemp,1)])
              ]


# Buttons
def canwakeup():
  wakeup = can.Message(data=[0x07, 0, 0, 0, 0, 0, 0, 0], is_extended_id=False, arbitration_id=0x2D3, channel=CanIHS)
  print(wakeup)
  bus.send(wakeup, timeout=1)

def radioreboot():
  radiorebootcmd = can.Message(data=[0x02, 0x11, 0x01, 0, 0, 0, 0, 0], is_extended_id=False, arbitration_id=0x7BF, channel=canIHS)
  bus.send(radiorebootcmd, timeout=1)

def maxac():
  maxaccmd = can.Message(data=[0x80, 0, 0, 0, 0, 0], is_extended_id=False, arbitration_id=0x342, channel=canIHS)
  bus.send(maxaccmd, timeout=1)

def synchvac():
  synchvaccmd = can.Message(data=[0, 0, 0, 0x04, 0], is_extended_id=False, arbitration_id=0x342, channel=canIHS)
  bus.send(synchvaccmd, timeout=1)

def blankscreen():
    subprocess.call(['xscreensaver-command', '-activate'])

def callback():
    topframe.quit()

def camera():
    global cam
    if cam:
        cam.terminate()
        cam = None
        frame.pack(side=TOP, fill="x")
    else:
        cam = subprocess.Popen(["raspivid", "-t", "0", "-v", "-w", "800", "-h", "480", "-op", "200", "-rot", "180"])
        camstatus = cam.poll()
        if camstatus is None:
                frame.pack_forget()

def button1():
    bigbutton1 = Button(
    topframe, text="CAMERA", fg="red", activeforeground="red", bg="black", activebackground="black", font=("Helvetica", "16"), height=2, width=7, command=camera)
    bigbutton1.pack(side=LEFT)
def button2():
    bigbutton2 = Button(
        topframe, text="Wake Up", fg="red", activeforeground="red", bg="black", activebackground="black", font=("Helvetica", "16"), height=2, width=7, command=canwakeup)
    bigbutton2.pack(side=LEFT)
def button3():
    maxacbutton = Button(
        topframe, text="MAX AC", fg="red", activeforeground="red", bg="black", activebackground="black", font=("Helvetica", "16"), height=2, width=7, command=maxac)
    maxacbutton.pack(side=LEFT)
def button4():
    synchvacbutton = Button(
        topframe, text="Sync", fg="red", activeforeground="red", bg="black", activebackground="black", font=("Helvetica", "16"), height=2, width=7, command=synchvac)
    synchvacbutton.pack(side=LEFT)
def button5():
     quitbutton = Button(
     topframe, text="QUIT", fg="red", activeforeground="red", bg="black", activebackground="black", font=("Helvetica", "16"), height=2, width=7, command=topframe.quit)
     quitbutton.pack(side=LEFT)
def button6():
    screenoffbutton = Button(
        topframe, text="Screen OFF", fg="red", activeforeground="red", bg="black", activebackground="black", font=("Helvetica", "16"), height=2, width=7, command=blankscreen)
    screenoffbutton.pack(side=LEFT)
def button7():
    radiorebootbutton = Button(
        topframe, text="Reboot", fg="red", activeforeground="red", bg="black", activebackground="black", font=("Helvetica", "16"), height=2, width=7, command=radioreboot)
    radiorebootbutton.pack(side=LEFT)


root = Tk()
root.geometry("800x480+0+0")
root.title("This is Root")
root.protocol("WM_DELETE_WINDOW", callback)
root.attributes("-fullscreen", fsstate)
root.configure(bg='black')

topframe=Frame(root)
topframe.configure(bg='black')
topframe.pack(side=BOTTOM, fill="x")
button1()
button2()
button3()
button4()
button5()
button6()

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

text10dsc = Label(textframe2, text="", font=("Helvetica", "16"))
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


frame = Frame(root)
frame.pack(side=TOP, fill="x")
frame.configure(bg='black')

coord = 0, 0, 200, 350 #define the size of the gaug
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
gauge4desc = gauge4.create_text(100,120, text="", font=("Helvetica", "16"))
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


# cheat
def wrapper(msg,name,func,output,*args):
    output(func(msg,*args))


# Process every single message received from the canbus
def newmsg(msg):
  for monitor in monitorlist:
   if msg.arbitration_id == monitor[0] and msg.channel == monitor[1]:
    for detail in monitor[2]:
     wrapper((msg.data),*detail)

# Build the can filter list
for monitor in monitorlist:
 # build out the can bus filtering list. only receive messages that we care about.
 canFilter.append({"can_id": monitor[0], "can_mask": 0xFFF, "can_channel": monitor[1]})


# define the can bus
bus = can.interface.Bus('', bustype='socketcan', filter=canFilter)
Notifier = can.Notifier(bus, [newmsg], loop=None)


root.mainloop()
bus.shutdown()
if cam:
    cam.terminate()


root.mainloop()
bus.shutdown()
if cam:
    cam.terminate()
