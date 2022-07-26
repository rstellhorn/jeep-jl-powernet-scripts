#!/usr/bin/python3
# GUI Can data display using tkinter

from tkinter import *
import time
import can
import subprocess
try:
    camavail = True
    import cv2
    cap = cv2.VideoCapture(0)
    if cap is None or not cap.isOpened():
            camavail = False
except:
    camavail = False

# If using vcan for log playback, change the values in the quotes below
can0 = "can0"
can1 = "can1"

battv = None
rpm = None
mph = None
fsstate = True

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
    low_r = 0 # chart low range
    hi_r = 7000 # chart hi range
    if rpm == 65535:
      rpm = 0
    if str(rpm) != rpmlabel["text"]:
      rpmlabel["text"] = str(rpm)
      rpmlabel.pack()
      rpmangle = (120 * (hi_r - rpm) / (hi_r - low_r) + 30)
      rpmgauge.itemconfig(rpmneedle,start = rpmangle)
      rpmgauge.pack()

def newmph(mph):
    if str(mph) != mphlabel["text"]:
      mphlabel["text"] = str(mph)
      mphlabel.pack()

def newbattv(battv):
    if str(battv) != battvlabel["text"]:
      battvlabel["text"] = str(battv)
      battvlabel.pack()

def newpstemp(pstemp):
    low_r = 50 # chart low range
    hi_r = 250 # chart hi range
    if str(pstemp) != pstemplabel["text"]:
      pstemplabel["text"] = str(pstemp)
      pstemplabel.pack()
      pstempangle = (120 * (hi_r - pstemp) / (hi_r - low_r) + 30)
      pstempgauge.itemconfig(pstempneedle,start = pstempangle)
      pstempgauge.pack()

def newmsg(msg):
  if msg.arbitration_id == 0x2C2 and msg.channel == can0:
    newbattv(msg.data[2] / 10)
  if msg.arbitration_id == 0x322 and msg.channel == can0:
    newrpm((msg.data[0]<<8) +  msg.data[1])
    newmph(round(((msg.data[2]<<8) + msg.data[3]) / 200, 1))
  if msg.arbitration_id == 0x128 and msg.channel == can1:
    newpstemp(round(((msg.data[1]) * (9 / 5)) + 32))

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
 while(cap.isOpened()):
  ret, frame = cap.read()
  if ret == True:
    cv2.imshow('Frame',frame)
  else:
    break
 cap.release()

def button1():
    bigbutton1 = Button(
    topframe, text="CAMERA", fg="red", font=("Helvetica", "16"), height=2, width=7, command=camera)
    bigbutton1.pack(side=LEFT)
def button2():
    bigbutton2 = Button(
        topframe, text="Wake Up", fg="red", font=("Helvetica", "16"), height=2, width=7, command=canwakeup)
    bigbutton2.pack(side=LEFT)
def button3():
    maxacbutton = Button(
        topframe, text="MAX AC", fg="red", font=("Helvetica", "16"), height=2, width=7, command=maxac)
    maxacbutton.pack(side=LEFT)
def button4():
    synchvacbutton = Button(
        topframe, text="Sync", fg="red", font=("Helvetica", "16"), height=2, width=7, command=synchvac)
    synchvacbutton.pack(side=LEFT)
def button5():
     quitbutton = Button(
     topframe, text="QUIT", fg="red", font=("Helvetica", "16"), height=2, width=7, command=topframe.quit)
     quitbutton.pack(side=LEFT)
def button6():
    screenoffbutton = Button(
        topframe, text="Screen OFF", fg="red", font=("Helvetica", "16"), height=2, width=7, command=blankscreen)
    screenoffbutton.pack(side=LEFT)
def button7():
    radiorebootbutton = Button(
        topframe, text="Reboot", fg="red", font=("Helvetica", "16"), height=2, width=7, command=radioreboot)
    radiorebootbutton.pack(side=LEFT)


root = Tk()
root.geometry("800x480+0+0")
root.title("This is Root")
root.protocol("WM_DELETE_WINDOW", callback)
# root.attributes("-fullscreen", fsstate)
root.configure(bg='gray')

topframe=Frame(root)
topframe.pack(side=BOTTOM)
button1()
button2()
button3()
button4()
button5()
button6()
frame = Frame(root)
frame.pack(side=TOP)

blfr = Frame(frame)
bldsc = Label(blfr, text="Backlight", font=("Helvetica", "16"))
bldsc.pack(side=LEFT)
backlight = Scale(blfr, command=blchange, orient=HORIZONTAL, length = 400, to = 100)
backlight.pack(side=RIGHT)
blfr.pack()

battfr = Frame(frame)
battvdsc = Label(battfr, text="Batt V", font=("Helvetica", "16"))
battvdsc.pack(side=LEFT)
battvlabel = Label(battfr, font=("Helvetica", "16"))
battvlabel.pack(side=RIGHT)
battfr.pack()

rpmfr = Frame(frame)
rpmdsc = Label(rpmfr, text="RPM", font=("Helvetica", "16"))
rpmdsc.pack(side=LEFT)
rpmlabel = Label(rpmfr, font=("Helvetica", "16"))
rpmlabel.pack(side=LEFT)

rpmgauge = Canvas(rpmfr, width=200, height=150)
rpmgauge.pack(side=LEFT)
coord = 0, 0, 150, 150 #define the size of the gauge
rpmgauge.create_arc(coord, start=30, extent=120, fill="white",  width=2) 
rpmneedle = rpmgauge.create_arc(coord, start= 119, extent=1, width=7)

pstempdsc = Label(rpmfr, text="PSTemp", font=("Helvetica", "16"))
pstempdsc.pack(side=LEFT)
pstemplabel = Label(rpmfr, font=("Helvetica", "16"))
pstemplabel.pack(side=LEFT)

pstempgauge = Canvas(rpmfr, width=200, height=150)
pstempgauge.pack(side=LEFT)
pstempgauge.create_arc(coord, start=30, extent=120, fill="white",  width=2)
pstempneedle = pstempgauge.create_arc(coord, start= 119, extent=1, width=7)

rpmfr.pack()

mphfr = Frame(frame)
mphdr = Label(mphfr, text="MPH", font=("Helvetica", "16"))
mphdr.pack(side=LEFT)
mphlabel = Label(mphfr, font=("Helvetica", "16"))
mphlabel.pack(side=RIGHT)
mphfr.pack()


bus = can.interface.Bus('', bustype='socketcan',filter=[{"can_id": 0x2C2, "can_mask": 0xFFF},{"can_id": 0x322, "can_mask": 0xFFF}])
Notifier = can.Notifier(bus, [newmsg], loop=None)


root.mainloop()
bus.shutdown()

