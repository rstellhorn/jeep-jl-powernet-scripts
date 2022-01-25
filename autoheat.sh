

#!/bin/bash

STARTED=$( date +%s )

# Sets HVAC preferences when vehicle has been remotely started.
echo "$(date) AUTOHEAT: Initializing."

procs="$( ps -eaf | grep autoheat | grep -v grep | grep -v " $$ " | wc -l )"
if [ $procs -gt 0 ]
  then
    echo "$(date) AUTOHEAT: ERROR - more than one process running! Exiting."
    exit 1
  fi

# If the blower motor is off, turn on the HVAC system.
FANSPEED=$( /home/pi/bin/fanspeed )
[ "$FANSPEED" == "0" ] && {
  echo "$(date) AUTOHEAT: turning on HVAC system"
  cansend can0 2D3#0700000000010000
  sleep 4.1
}

# Store settings
VENTMODE=$(/home/pi/bin/ventmode)
FANSPEED=$(/home/pi/bin/fanspeed)
echo "$(date) AUTOHEAT: Current VENT: $VENTMODE and SPEED: $FANSPEED"

# Mute the stereo
echo "$(date) AUTOHEAT: Muting the radio"
/home/pi/bin/mute ON  ; sleep 0.31

# Turn the fan all the way up
echo "$(date) AUTOHEAT: setting fan to MAX"
/home/pi/bin/fanspeed 7

# Turn on the HVAC front defroster
# This also turns OFF the air conditioner and turns OFF air recirculation.
echo "$(date) AUTOHEAT: clearing modes via the front defroster"
/home/pi/bin/ventmode 00 ; sleep 1.12

# Select a vent combination of windshield and floor
echo "$(date) AUTOHEAT: directing air to windshield and floor"
ventmode 02 ; sleep 1.12

# Turn on air recirculation.
# This automatically causes the A/C to engage, so we'll need to undo that.
echo "$(date) AUTOHEAT: recirculating air"
cansend can0 2D3#0700000000000200
sleep 1.1

# Start setting the driver side to maximum heat setting
# Just 8 steps at first.
for i in `seq 1 8`
do
  cansend can0 2D3#0700000000040000
  sleep 0.36
done
sleep 0.6

echo "$(date) AUTOHEAT: turning OFF the AC system"
# Turn off the A/C cooling (was turned on with recirculate mode)
cansend can0 2D3#0700000000000100
sleep 0.6

echo "$(date) AUTOHEAT: setting temperature to MAX"
# Finish setting the driver side to maximum heat setting
# Now 18 more steps.
for i in `seq 1 18`
do
  cansend can0 2D3#0700000000040000
  sleep 0.36
done
sleep 0.6

# Alter the passenger temperature up and down to break any temperature sync
echo "$(date) AUTOHEAT: Syncing driver/passenger settings"
cansend can0 2D3#0700000000100000
sleep 0.36
cansend can0 2D3#0700000000200000
sleep 1.93

# Engage the Driver / Passenger temperature Sync
  cansend can0 342#0000000400
  sleep 1.61

echo "$(date) AUTOHEAT: exiting normally."


