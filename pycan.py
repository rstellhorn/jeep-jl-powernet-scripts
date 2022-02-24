#!/usr/bin/python3
# jeep canbus live data display

# import libraries
import can
import curses

canIHS = "vcan0"
canC = "vcan1"

# start curses screen management
stdscr = curses.initscr()

# lay out our plain text
stdscr.addstr(1,1,'Batt')
stdscr.addstr(1,11,'Vdc')
stdscr.addstr(2,1,'Roll')
stdscr.addstr(2,14,'Tilt')
stdscr.addstr(2,26,'Yaw')
stdscr.addstr(4,1,'RPM')
stdscr.addstr(4,14,'MPH')
stdscr.addstr(4,27,'Gear')
stdscr.addstr(4,40,'4x4')
stdscr.addstr(6,1,'Steering Angle')
stdscr.addstr(6,25,'Turn')
stdscr.addstr(6,40,'Temp')
stdscr.addstr(6,50,'Pres')
stdscr.addstr(8,1,'Tire psi')
stdscr.addstr(10,1,'Brake Act')
stdscr.addstr(10,18,'Pedal')
stdscr.addstr(10,30,'Motion')
stdscr.addstr(12,1,'Temps IAT')
stdscr.addstr(12,20,'Coolant')
stdscr.addstr(14,1,'Lights')
stdscr.addstr(18,1,'0x296')

# update the screen with the text
stdscr.refresh()

# startup the canbus interface and filter only the ids that we want
bus = can.interface.Bus('', bustype='socketcan',filter=[{"can_id": 0x2C2, "can_mask": 0xFFF},{"can_id": 0x02B, "can_mask": 0xFFF},{"can_id": 0x322, "can_mask": 0xFFF},{"can_id": 0x023, "can_mask": 0xFFF},{"can_id": 0x077, "can_mask": 0xFFF},{"can_id": 0x127, "can_mask": 0xFFF},{"can_id": 0x128, "can_mask": 0xFFF},{"can_id": 0x037, "can_mask": 0xFFF},{"can_id": 0x071, "can_mask": 0xFFF},{"can_id": 0x093, "can_mask": 0xFFF},{"can_id": 0x2FF, "can_mask": 0xFFF},{"can_id": 0x30A, "can_mask": 0xFFF},{"can_id": 0x277, "can_mask": 0xFFF},{"can_id": 0x128, "can_mask": 0xFFF},{"can_id": 0x291, "can_mask": 0xFFF},{"can_id": 0x079, "can_mask": 0xFFF},{"can_id": 0x296, "can_mask": 0xFFF},{"can_id": 0x12B, "can_mask": 0xFFF}])

# wrap everything in a try to catch exceptions cleanly
try:
  # iterate through all messages received
  for msg in bus:
    # match a can id and can bus
    if msg.arbitration_id == 0x2C2 and msg.channel == canIHS:
      # place data using str to convert float data to a string
      # this is using the 3rd hex word, deviding by 10
      stdscr.addstr(1,6,'%-5s' % str(msg.data[2] / 10))
      # once the message has been processes, refresh the screen with the data
      stdscr.addstr(1,20,'%-6s' % str(((msg.data[0]<<8) + msg.data[1]) / 100))
      stdscr.refresh()
    # match another message
    if msg.arbitration_id == 0x02B and msg.channel == canC:
      # place data, multiple words each in its own spot
      stdscr.addstr(2,6,'%-6s' % str(((msg.data[0]<<8) + msg.data[1] - 2048) / 10))
      stdscr.addstr(2,20,'%-6s' % str(((msg.data[2]<<8) + msg.data[3] - 2032) / 10))
      stdscr.addstr(2,30,'%-6s' % str(((msg.data[4]<<8) + msg.data[5] - 2048) / 10))
      # once the message has been processes, refresh the screen with the data
      stdscr.refresh()
    if msg.arbitration_id == 0x322 and msg.channel == canIHS:
      rpmstr =  str(((msg.data[0]<<8) +  msg.data[1]))
      if rpmstr == "65535":
        rpmstr = str(0)
      stdscr.addstr(4,6,'%-6s' % rpmstr)
      stdscr.addstr(4,20,'%-4s' % str(((msg.data[2]<<8) + msg.data[3]) / 200))
      # once the message has been processes, refresh the screen with the data
      stdscr.refresh()
    if msg.arbitration_id == 0x023 and msg.channel == canC:
      stdscr.addstr(6,16,'%-6s' % str(((msg.data[0]<<8) + msg.data[1]) - 0x1000))
      stdscr.addstr(6,32,'%-6s' % str(((msg.data[2]<<8) + msg.data[3]) - 0x1000))
      stdscr.refresh()
    if msg.arbitration_id == 0x079 and msg.channel == canC:
      stdscr.addstr(10,12,'%-5s' % str(((msg.data[0]<<8) + msg.data[1]) & 0x0FFF))
      stdscr.addstr(10,25,'%-5s' % str((msg.data[2]<<8) + msg.data[3]))
      if (msg.data[0] & 0xF0) == 0x80:
        movingstat = 'Stopped'
      elif (msg.data[0] & 0xF0) == 0x00:
        movingstat = 'Moving'
      else:
        movingstat = str(msg.data[0] & 0xF0) 
      stdscr.addstr(10,40,'%-10s' % movingstat)
      stdscr.refresh()
    if msg.arbitration_id == 0x127 and msg.channel == canC:
      stdscr.addstr(12,15,'%-3s' % str(round((((msg.data[0] - 40) * (9 / 5)) + 32))))
      stdscr.addstr(12,30,'%-3s' % str(round((((msg.data[1] - 40) * (9 / 5)) + 32))))
      stdscr.addstr(12,35,'%-3s' % hex(msg.data[2]))
      stdscr.addstr(12,40,'%-3s' % str(round((((msg.data[6] - 40) * (9 / 5)) + 32))))
      stdscr.refresh()
    if msg.arbitration_id == 0x291 and msg.channel == canC:
      stdscr.addstr(14,10,'%-3s' % str(msg.data[0]))
      stdscr.addstr(14,14,'%-3s' % str(msg.data[1]))
      stdscr.addstr(14,18,'%-3s' % str(msg.data[2]))
      stdscr.addstr(14,22,'%-3s' % str(msg.data[3]))
      stdscr.addstr(14,26,'%-3s' % str(msg.data[4]))
      stdscr.addstr(14,30,'%-3s' % str(msg.data[5]))
      stdscr.addstr(14,34,'%-3s' % str(msg.data[6]))
      stdscr.addstr(14,38,'%-3s' % str(msg.data[7]))
      stdscr.refresh()
    if msg.arbitration_id == 0x037 and msg.channel == canC:
      stdscr.addstr(16,50,'%-6s' % str((msg.data[0]<<8) + msg.data[1]))
      stdscr.addstr(16,60,'%-6s' % str(msg.data[5]))
      stdscr.refresh()
    if msg.arbitration_id == 0x071 and msg.channel == canC:
      stdscr.addstr(12,50,'%-6s' % str((msg.data[0]<<8) + msg.data[1]))
      stdscr.addstr(12,60,'%-6s' % str(msg.data[4]))
      stdscr.refresh()
    if msg.arbitration_id == 0x093 and msg.channel == canC:
      if msg.data[2] == 0x4E:
        mtstatus = 'N'
      elif msg.data[2] == 0x52:
        mtstatus = 'R'
      elif msg.data[2] == 0x31:
        mtstatus = '1'
      elif msg.data[2] == 0x32:
        mtstatus = '2'
      elif msg.data[2] == 0x33:
        mtstatus = '3'
      elif msg.data[2] == 0x34:
        mtstatus = '4'
      elif msg.data[2] == 0x35:
        mtstatus = '5'
      elif msg.data[2] == 0x36:
        mtstatus = '6'
      elif msg.data[2] == 0x50:
        mtstatus = 'P'
      elif msg.data[2] == 0x44:
        mtstatus = 'D'
      else:
        mtstatus = hex(msg.data[2])
      stdscr.addstr(4,33,'%-4s' % mtstatus)
      stdscr.refresh()
    if msg.arbitration_id == 0x277 and msg.channel == canC:
      if msg.data[1] == 0x02:
        mtstatus = 'N'
      elif msg.data[0] == 0x00:
        mtstatus = '2HI'
      elif msg.data[0] == 0x10:
        mtstatus = '4HI'
      elif msg.data[0] == 0x20:
        mtstatus = 'N'
      elif msg.data[0] == 0x40:
        mtstatus = '4LO'
      elif msg.data[0] == 0x80:
        mtstatus = 'SHIFT'
      else:
        mtstatus = msg.data[0]
      stdscr.addstr(4,45,'%-5s' % mtstatus)
      stdscr.refresh()
    if msg.arbitration_id == 0x277 and msg.channel == canC:
      stdscr.addstr(16,10,'%-6s' % str(msg.data[0]))
      stdscr.addstr(16,20,'%-6s' % str(msg.data[2]))
      stdscr.refresh()
    if msg.arbitration_id == 0x128 and msg.channel == canC:
      stdscr.addstr(6,45,'%-5s' % str(round((((msg.data[1]) * (9 / 5)) + 32))))
      stdscr.addstr(6,55,'%-5s' % str(msg.data[2]))
      stdscr.addstr(6,60,'%-5s' % str(msg.data[5]))
      stdscr.refresh()
    if msg.arbitration_id == 0x296 and msg.channel == canC:
      stdscr.addstr(8,15,'%-3s' % str(msg.data[3]))
      stdscr.addstr(8,20,'%-3s' % str(msg.data[4]))
      stdscr.addstr(8,25,'%-3s' % str(msg.data[5]))
      stdscr.addstr(8,30,'%-3s' % str(msg.data[6]))
    if msg.arbitration_id == 0x296 and msg.channel == canC:
      stdscr.addstr(18,10,'%-3s' % str(round((((msg.data[0] - 40) * (9 / 5)) + 32))))
      stdscr.addstr(18,16,'%-3s' % hex(msg.data[1]))
      stdscr.addstr(18,20,'%-3s' % hex(msg.data[2]))
      stdscr.addstr(18,24,'%-3s' % hex(msg.data[3]))
      stdscr.addstr(18,28,'%-3s' % hex(msg.data[4]))

# catch errors, display them, and exit cleanly
except:
  bus.shutdown()
  curses.nocbreak()
  stdscr.keypad(0)
  curses.echo()
  curses.endwin()
  raise
