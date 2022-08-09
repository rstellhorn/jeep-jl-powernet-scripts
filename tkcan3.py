#!/usr/bin/python3
# GUI Can data display using tkinter

from tkinter import *
import time
import can
import subprocess
import signal

# If using vcan for log playback, change the values in the quotes below
can0 = "vcan0"
can1 = "vcan1"

battv = None
rpm = None
mph = None
fsstate = True
cam = None
oldpstemp = None
oldrpm = None
oldtilt = None
oldroll = None

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

def blchange(bllevels):
        print("backlight changed")
        print(str(bllevels))

def tick():
        s = time.strftime('%I:%M:%S%p')
        if s != clock["text"]:
            clock["text"] = s
        clock.after(200, tick)

def goaway():
        bigbutton.config(text="Come Back", command=comeback)
        bigbutton.pack()
        frame.pack_forget()

def comeback():
        bigbutton.config(text="Go Away", command=goaway)
        bigbutton.pack()
        frame.pack(side=TOP)
        return "break"

def newrpm(rpm):
    global oldrpm
    low_r = 0 # chart low range
    hi_r = 7000 # chart hi range
    if rpm == 65535:
      rpm = 0
    if rpm != oldrpm:
      gauge1.itemconfig(gauge1label, text=str(rpm))
      rpmangle = (120 * (hi_r - rpm) / (hi_r - low_r) + 30)
      gauge1.itemconfig(gauge1needle,start = rpmangle)
      gauge1.grid()
      oldrpm = rpm

def newmph(mph):
    if str(mph) != mphlabel["text"]:
      mphlabel["text"] = str(mph)
      mphlabel.pack()

def newbattv(battv):
    if str(battv) != battvlabel["text"]:
      battvlabel["text"] = str(battv)
      battvlabel.pack()

def newpstemp(pstemp):
    global oldpstemp
    low_r = 50 # chart low range
    hi_r = 250 # chart hi range
    if pstemp != oldpstemp:
      gauge2.itemconfig(gauge2label, text=str(pstemp))
      pstempangle = (120 * (hi_r - pstemp) / (hi_r - low_r) + 30)
      gauge2.itemconfig(gauge2needle,start = pstempangle)
      gauge2.grid()
      oldpstemp = pstemp

def newtilt(tilt, roll):
    global oldtilt
    global oldroll
    if tilt != oldtilt:
       gauge7.itemconfig(gauge7label, text=str(tilt))
       gauge7.itemconfig(gauge7needle, start=tilt)
       gauge7.grid()
       oldtilt = tilt
       if tilt > 15:
               gauge7.itemconfig(gauge7needle, fill="yellow")
       if tilt > 25:
               gauge7.itemconfig(gauge7needle, fill="red")
       else:
               gauge7.itemconfig(gauge7needle, fill="green")
    if roll != oldroll:
       gauge8.itemconfig(gauge8label, text=str(roll))
       gauge8.itemconfig(gauge8needle, start=roll)
       gauge8.grid()
       oldroll = roll
       if roll > 15:
               gauge8.itemconfig(gauge8needle, fill="yellow")
       if roll > 25:
               gauge8.itemconfig(gauge8needle, fill="red")
       else:
               gauge8.itemconfig(gauge8needle, fill="green")

def newmsg(msg):
  if msg.arbitration_id == 0x2C2 and msg.channel == can0:
    newbattv(msg.data[2] / 10)
  if msg.arbitration_id == 0x322 and msg.channel == can0:
    newrpm((msg.data[0]<<8) +  msg.data[1])
    newmph(round(((msg.data[2]<<8) + msg.data[3]) / 200, 1))
  if msg.arbitration_id == 0x128 and msg.channel == can1:
    newpstemp(round(((msg.data[1]) * (9 / 5)) + 32))
  if msg.arbitration_id == 0x02B and msg.channel == can1:
    newtilt(round(((msg.data[0]<<8) + msg.data[1] - 2048) / 20)*2, round(((msg.data[2]<<8) + msg.data[3] - 2048) / 20)*2)

def canwakeup():
  wakeup = can.Message(data=[0x07, 0, 0, 0, 0, 0, 0, 0], is_extended_id=False, arbitration_id=0x2D3, channel=can0)
  print(wakeup)
  bus.send(wakeup, timeout=1)

def radioreboot():
  radiorebootcmd = can.Message(data=[0x02, 0x11, 0x01, 0, 0, 0, 0, 0], is_extended_id=False, arbitration_id=0x7BF, channel=can0)
  bus.send(radiorebootcmd, timeout=1)

def maxac():
  maxaccmd = can.Message(data=[0x80, 0, 0, 0, 0, 0], is_extended_id=False, arbitration_id=0x342, channel=can0)
  bus.send(maxaccmd, timeout=1)

def synchvac():
  synchvaccmd = can.Message(data=[0, 0, 0, 0x04, 0], is_extended_id=False, arbitration_id=0x342, channel=can0)
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

mphdr = Label(textframe, text="MPH", font=("Helvetica", "16"))
mphdr.pack(side=LEFT)
mphlabel = Label(textframe, font=("Helvetica", "16"))
mphlabel.pack(side=LEFT)

battvdsc = Label(textframe, text="Batt V", font=("Helvetica", "16"))
battvdsc.pack(side=LEFT)
battvlabel = Label(textframe, font=("Helvetica", "16"))
battvlabel.pack(side=LEFT)

frame = Frame(root)
frame.pack(side=TOP, fill="x")
frame.configure(bg='black')

coord = 0, 0, 200, 350 #define the size of the gaug
fullcoord = 0, 0, 175, 175

gauge1 = Canvas(frame, width=200, height=175)
gauge1.grid(row=1, column=1)
gauge1.create_arc(coord, start=30, extent=120, fill="white",  width=2)
gauge1desc = gauge1.create_text(100,120, text="RPM", font=("Helvetica", "16"))
gauge1label = gauge1.create_text(100,80, text="", font=("Helvetica", "16"))
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
gauge3desc = gauge3.create_text(100,120, text="GAUGE3", font=("Helvetica", "16"))
gauge3label = gauge3.create_text(100,80, text="", font=("Helvetica", "16"))
gauge3needle = gauge3.create_arc(coord, start= 150, extent=1, width=7)

gauge4 = Canvas(frame, width=200, height=175)
gauge4.grid(row=1, column=4)
gauge4.create_arc(coord, start=30, extent=120, fill="white",  width=2)
gauge4desc = gauge4.create_text(100,120, text="GAUGE4", font=("Helvetica", "16"))
gauge4label = gauge4.create_text(100,80, text="", font=("Helvetica", "16"))
gauge4needle = gauge4.create_arc(coord, start= 150, extent=1, width=7)

gauge5 = Canvas(frame, width=200, height=175)
gauge5.grid(row=2, column=1)
gauge5.create_arc(coord, start=30, extent=120, fill="white",  width=2)
gauge5desc = gauge5.create_text(100,120, text="GAUGE5", font=("Helvetica", "16"))
gauge5label = gauge5.create_text(100,80, text="", font=("Helvetica", "16"))
gauge5needle = gauge5.create_arc(coord, start= 150, extent=1, width=7)

gauge6 = Canvas(frame, width=200, height=175)
gauge6.grid(row=2, column=2)
gauge6.create_arc(coord, start=30, extent=120, fill="white",  width=2)
gauge6desc = gauge6.create_text(100,120, text="GAUGE6", font=("Helvetica", "16"))
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

bus = can.interface.Bus('', bustype='socketcan',filter=[{"can_id": 0x2C2, "can_mask": 0xFFF},{"can_id": 0x322, "can_mask": 0xFFF}])
Notifier = can.Notifier(bus, [newmsg], loop=None)


root.mainloop()
bus.shutdown()
if cam:
    cam.terminate()
