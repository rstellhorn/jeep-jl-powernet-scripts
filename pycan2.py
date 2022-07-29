#!/usr/bin/python3
# jeep canbus live data display
# v2

# import libraries
import can
import curses

canFilter = list()

# can bus variables, change these for vcan or can
canIHS = "can0"
canC = "can1"

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

def wrapper(msg,name,func,output,colum,*args):
    return(func(msg,*args))

def pstemp(x,a):
    return(round(((x[a] * (9 / 5)) + 32)))

# list of can ID's and details to monitor in this order:
# (ID, Channel, [("name", process, type, colum, byte1, byte2)])
monitorlist=[(0x2C2,
              canIHS,
              [("Batt V",volt,str,0,2),
               ("Batt ?",raw8,hex,0,0)]),
             (0x02B,
              canC,
              [("Roll",tilt,str,0,0,1),
               ("Tilt",tilt,str,0,2,3),
               ("Yaw",tilt,str,0,4,5)]),
             (0x322,
              canIHS,
              [("RPM",rpm,str,0,0,1),
               ("MPH",mph,str,0,2,3)]),
             (0x127,
              canC,
              [("IAT",temp,str,0,0),
               ("Coolant",temp,str,0,1)]),
             (0x13D,
              canC,
              [("Oil Temp",temp,str,0,3),
               ("Oil Pres",psi,str,0,2)]),
             (0x093,
              canC,
              [("Gear",gear,str,0,2)]),
             (0x277,
              canC,
              [("Transfer",xfer,str,0,0)]),
             (0x023,
              canC,
              [("Steer Angl",steer,str,0,0,1),
               ("Rate",steer,str,0,2,3)]),
             (0x128,
              canC,
              [("PS Temp",pstemp,str,0,1),
               ("PS PSI",raw8,str,0,2),
               ("PS UNK 3",raw8,str,0,3)]),
             (0x13F,
              canC,
              [("0x13F 2",raw8,str,0,1),
               ("0x13F 2 3",raw16,str,0,2,3),
               ("0x13F 4 5",raw16,str,0,4,5)])
              ]

stdscr = curses.initscr()

# setup
for monitor in monitorlist:
 # build out the can bus filtering list. only receive messages that we care about.
 canFilter.append({"can_id": monitor[0], "can_mask": 0xFFF, "can_channel": monitor[1]})
 for detail in monitor[2]:
  # place item titles, according to how they appear in the list
  stdscr.addstr(monitorlist.index(monitor),(monitor[2].index(detail) * 30),detail[0])

stdscr.refresh()

# define the can bus
bus = can.interface.Bus('', bustype='socketcan', filter=canFilter)

# Process every single message received from the canbus
try:
 for msg in bus:
  for monitor in monitorlist:
   if msg.arbitration_id == monitor[0] and msg.channel == monitor[1]:
    for detail in monitor[2]:
     stdscr.addstr(monitorlist.index(monitor),((monitor[2].index(detail) * 30) + 15), '%-5s' % detail[2](wrapper((msg.data),*detail)))
     stdscr.refresh()
  
except:
  bus.shutdown()
  curses.nocbreak()
  stdscr.keypad(0)
  curses.echo()
  curses.endwin()
  raise

