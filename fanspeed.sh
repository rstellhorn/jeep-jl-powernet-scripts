#!/bin/bash

# This script reads or sets the HVAC fan speed.

usage() {
  echo ""
  echo "USAGE: $(basename $0) [speed]"
  echo "  When setting values: 01 (low) through 07 (max)"
  echo "  When reading values: 00 (off), 01 (low) through 07 (max)"
  echo " "
  exit 1
}

TRIES=0
MAXTRIES=5
DEBUG=false
DELAY=1.1
SPEEDID=99
SPEEDWANTED="$1"

SHOWUSAGE=1
[ $SPEEDWANTED -gt 0 ] 2>/dev/null && [ $SPEEDWANTED -lt 8 ] 2>/dev/null && SHOWUSAGE=0
[ "$SPEEDWANTED" == "" ] && { SPEEDWANTED="XX"; SHOWUSAGE=0; }

[ $SHOWUSAGE -eq 1 ] && usage

read_error() {
  echo "FAILURE: Could not read a valid fan speed message."
  echo ""
  # Exit with a failure result code
  exit 1
}

write_error() {
  echo "FAILURE: Could not change the fan speed to the desired value."
  echo ""
  # Exit with a failure result code
  exit 1
}

request_fan_speed () {

  # Collect fan speed from message ID $2B1 on CAN-C
  # This message repeats one time per second.
  # After $DELAY seconds, stop collecting.

  COMMAND="timeout -s 1 $DELAY /usr/bin/candump -L can1,02B1:0FFF"

  # Only collect messages which are a direct response to our own query.
  # All other messages will be ignored.

  RESPONSE=$( $COMMAND | cut -d# -f2 | cut -c1-2 | tail -1)
}

# MAIN PROGRAM LOOP BEGINS HERE ------------------------------------------
# Read the HVAC fan speed. If it isn't what we want, hit the "FAN +" or
# the "FAN -" as many times as neeeded. Lather, rinse, repeat. Delays are
# introduced into each of these loops in order to avoid hysteresis.

while [ $SPEEDID != $SPEEDWANTED ]
  do

    # Read the HVAC fan speed from the CAN bus
    request_fan_speed

    # If no response was found, send a wakeup packet. Try again.
    if [ "$RESPONSE" == "" ] ; then
      DELAY=1.1
      /home/pi/bin/wake ; sleep 0.5
      request_fan_speed
    fi

    # If no response was found, send a wakeup packet. Try again.
    if [ "$RESPONSE" == "" ] ; then
      DELAY=1.8
      /home/pi/bin/wake
      request_fan_speed

      # If no response AGAIN, then exit with an error.
      if [ "$RESPONSE" == "" ] ; then read_error; fi
    fi

    SPEEDID=$( printf "%d" 0x$RESPONSE )
    # A speed of "127" means offline, so we'll treat it as fan speed 0.
    [ $SPEEDID -eq 127 ] && SPEEDID=0
    [ $SPEEDID -gt 7 ] && read_error

    # If the user supplied no arguments, print the fan speed and exit.
    [ "$SPEEDWANTED" == "XX" ] && {
      echo $SPEEDID
      exit 0
    }

    # If the current HVAC fan speed isn't what we want, then hit the
    # appropriate fan speed buttons to increase or decrease it.

    [ "$DEBUG" == "true" ] && echo SPEED: $SPEEDID   DESIRED: $SPEEDWANTED

    [ "$SPEEDID" -lt "$SPEEDWANTED" ] && {
        for i in $( seq $SPEEDID $(( $SPEEDWANTED -1 )) )
        do
          # Increase the fan speed
          # Use a larger delay to compensate for fan spin-up time
          [ "$DEBUG" == "true" ] && echo REQUESTING FAN SPEED INCREASE
          cansend can0 273#0000050000000000; sleep 0.73
        done
        # exit 0
      }
    [ "$SPEEDID" -gt "$SPEEDWANTED" ] && {
        for i in $( seq $SPEEDWANTED $(( $SPEEDID -1 )) )
        do
          # Decrease the fan speed
          # Use a short delay because fans wind-down quickly.
          [ "$DEBUG" == "true" ] && echo REQUESTING FAN SPEED DECREASE
          cansend can0 273#00000A0000000000; sleep 0.23
        done
        # exit 0
      }

    [ "$SPEEDID" -eq "$SPEEDWANTED" ] && exit 0

    # We're going to try up to FIVE times to change the HVAC fan speed.
    # After that, exit with an error.

    TRIES=$(( $TRIES + 1 ))
    [ "$TRIES" -gt $MAXTRIES ] && write_error

  done

# A clean exit. Either we reported a value, made a change, or was requested
# to make a change but no change was necessary.

exit 0
