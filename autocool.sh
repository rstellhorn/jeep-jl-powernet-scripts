

#!/bin/bash

STARTED=$( date +%s )

# Sets HVAC preferences when vehicle has been remotely started.
echo "$(date) AUTOCOOL: Initializing."

procs="$( ps -eaf | grep autoheat | grep -v grep | grep -v " $$ " | wc -l )"
if [ $procs -gt 0 ]
  then
    echo "$(date) AUTOCOOL: ERROR - more than one process running! Exiting."
    exit 1
  fi

# ALL PREFLIGHT CHECKS HAVE ALREADY BEEN DONE.
# WE CAN BEGIN OUR WORK IMMEDIATELY.

# If the blower motor is off, turn on the HVAC system.
FANSPEED=$( /home/pi/bin/fanspeed )
[ "$FANSPEED" == "0" ] && {
   echo "$(date) AUTOCOOL: turning on HVAC system"
   cansend can0 2D3#0700000000010000
   sleep 4.1
}

# Store settings
VENTMODE=$(/home/pi/bin/ventmode)
FANSPEED=$(/home/pi/bin/fanspeed)
echo "$(date) AUTOCOOL: Active VENT $VENTMODE and SPEED $FANSPEED"

# Mute the stereo
echo "$(date) AUTOCOOL: Muting the radio"
/home/pi/bin/mute ON  ; sleep 0.31

# Set the fan speed to maximum
echo "$(date) AUTOCOOL: setting fan to MAX"
/home/pi/bin/fanspeed 7

# Set the front defroster (which deactivates recirculation mode and AC mode)
echo "$(date) AUTOCOOL: clearing modes with front defroster"
/home/pi/bin/ventmode 00
sleep 1.12

# Now, select the exact blower we want (the main vents)
echo "$(date) AUTOCOOL: directing air to panel vents"
ventmode 08

# Start setting the driver side to maximum cool setting
# Just 8 steps at first.
for i in `seq 1 8`
do
  cansend can0 2D3#0700000000080000
  sleep 0.36
done
sleep 0.6

# Turn on the A/C cooling (turns on with recirculate mode)
echo "$(date) AUTOCOOL: Turning on AC system"
cansend can0 2D3#0700000000000100
sleep 0.6

echo "$(date) AUTOCOOL: setting temperature to LOW"
# Finish setting the driver side to maximum cool setting
# Now 18 more steps.
for i in `seq 1 18`
do
  cansend can0 2D3#0700000000080000
  sleep 0.36
done
sleep 0.6

# Turn OFF air recirculation (which came on with the AC)
echo "$(date) AUTOCOOL: Turning OFF air recirculation"
cansend can0 2D3#0700000000000200

echo "$(date) AUTOCOOL: Syncing driver/passenger settings"
# Alter the passenger temperature down and up to break any
# existing temperature sync
  cansend can0 2D3#0700000000200000
  sleep 0.36
  cansend can0 2D3#0700000000100000
  sleep 0.63

sleep 1.3

## Sync the driver/passenger HVAC controls
cansend can0 342#0000000400
sleep 0.61

echo "$(date) AUTOCOOL: exiting normally."


