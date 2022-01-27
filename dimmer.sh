#!/bin/bash
# Raspberry Pi Backlight control via
# Jeep wrangler JL canbus

LAST=77777
LASTDIM=199

# Watch the canbus for packets from the light switch
COMMAND="/usr/bin/candump -L can1,0291:0FFF"
$COMMAND | while read TIME BUS MESSAGE
do
  NOW=$SECONDS
  # Run just once per second to save CPU
  [ "$NOW" != "$LAST" ] && {
    #Pick out just the data bits that we need
    DATA=${MESSAGE:4}
    RUNL=${DATA:5:1}
    DIML=${DATA:12:2}
    # Only change the dimmer if the running lights are on
    if [[ "$RUNL" == "3" || "$RUNL" == "1" ]]
    then
      # change hex into decimal
      DIMRAW="$(printf "%d" 0x$DIML)"
      # scale the 22-200 input to 0-53
      DIMCALC="`bc <<< $((DIMRAW - 22))*.3`"
      # drop the floating point and add 7 to meet the screen minimum
      DIMLEVEL="$(($(printf %.0f $DIMCALC)+7))"
    else
      # full brightness if lights are off
      DIMLEVEL=199
    fi
    # only change the screen brightness if there is a change
    if [ "$DIMLEVEL" != "$LASTDIM" ]
    then
      echo "Dimming to $DIMLEVEL / 200"
      # update the screen brightness
      echo $DIMLEVEL > /sys/class/backlight/rpi_backlight/brightness
      LASTDIM=$DIMLEVEL
    fi
    LAST=$NOW
  }
done

