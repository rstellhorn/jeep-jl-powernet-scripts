#!/usr/bin/python3
# jeep canbus live data display
# v2

# import libraries
import can
import time
from tkinter import *
try:
    camavail = True
    import cv2
    cap = cv2.VideoCapture(0)
    if cap is None or not cap.isOpened():
        camavail = False
except ImportError:
    camavail = False

canFilter = list()

# can bus variables, change these for vcan or can
canIHS = "vcan0"
canC = "vcan1"

gaugetotal = 8
gaugerow = 2
gauge = 0

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
        return('4x2H')
    elif x[a] == 0x02:
        return('N')
    elif x[a] == 0x10:
        return('4x4H')
    elif x[a] == 0x20:
        return('N')
    elif x[a] == 0x40:
        return('4x4L')
    elif x[a] == 0x80:
        return('Shifting')

def steer(x,a,b):
    return(((x[a]<<8) + x[b]) - 0x1000)

def pstemp(x,a):
    return(round(((x[a] * (9 / 5)) + 32)))

# End of types

# Cleanup on exit
def callback():
    bus.shutdown()
    print(bus.state)
    print("exit")
    raise

# setup gauges
def gaugesetup()
    gcount = 0
    maxline = 4
    for monitor in monitorlist:
        for detail in monitor[2]:
            rpmfr = Frame(frame)
            rpmdsc = Label(rpmfr, text="RPM", font=("Helvetica", "16"))
            rpmdsc.pack(side=TOP)
            rpmlabel = Label(rpmfr, font=("Helvetica", "16"))
            rpmlabel.pack()
            rpmgauge = Canvas(rpmfr, width=200, height=100)
            rpmgauge.pack()
            coord = 0, 0, 100, 200 #define the size of the gauge
            rpmgauge.create_arc(coord, start=30, extent=120, fill="black",  width=2) 
            rpmneedle = rpmgauge.create_arc(coord, start= 119, extent=1, width=7)

            

# Process messages as they are received
def wrapper(msg,name,func,output,gmin,gmax,dtype,*args):
    return(func(msg,*args))

def newmsg(msg):
  for monitor in monitorlist:
   if msg.arbitration_id == monitor[0] and msg.channel == monitor[1]:
    for detail in monitor[2]:
     detail[2]["text"] = wrapper(msg.data,*detail)
     detail[2].pack


# list of can ID's and details to monitor in this order:
# (ID, Channel, [("name", process, entity, min, max, type, byte1, byte2)])
monitorlist=[(0x2C2,
              canIHS,
              [("Batt V",volt,gauge0,11,15,str,2)]),
             (0x02B,
              canC,
              [("Roll",tilt,rollg,-30,30,str,0,1),
               ("Tilt",tilt,tiltg,-30,30,str,2,3),
               ("Yaw",tilt,yawg,-30,30,str,4,5)]),
             (0x127,
              canC,
              [("IAT",temp,gauge1,30,200,str,0),
               ("Coolant",temp,gauge2,150,300,str,1)]),
             (0x13D,
              canC,
              [("Oil Temp",temp,gauge3,150,300,str,3),
               ("Oil Pres",psi,gauge4,0,80,str,2)]),
             (0x093,
              canC,
              [("Gear",gear,text0,,,str,2)]),
             (0x277,
              canC,
              [("Transfer",xfer,text1,,,str,0)]),
             (0x023,
              canC,
              [("Steer Angl",steer,text2,,,str,0,1)]),
             (0x128,
              canC,
              [("PS Temp",pstemp,gauge5,50,300,str,1)])
              ]

# setup
while gauge < gaugetotal:
    


# define the can bus
bus = can.interface.Bus('', bustype='socketcan', filter=canFilter)
Notifier = can.Notifier(bus, [newmsg], loop=None)

# Process every single message received from the canbus
try:

  
except:
  bus.shutdown()
  curses.nocbreak()
  stdscr.keypad(0)
  curses.echo()
  curses.endwin()
  raise

