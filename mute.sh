#!/bin/bash

# The script either detects or modifies the radio's mute setting.

usage() {
  echo ""
  echo "USAGE: $(basename $0) [on/off]"
  echo ""
  exit 1
}

TRIES=0
MAXTRIES=3
DEBUG=false
DELAY=1.1
MUTEID=99
MUTEWANTED=$(echo $1 | tr '[:lower:]' '[:upper:]')
[ "$MUTEWANTED" == "" ]    && MUTEWANTED=XX
[ "$MUTEWANTED" == "ON" ]  && MUTEWANTED=03
[ "$MUTEWANTED" == "OFF" ] && MUTEWANTED=00
[ "$MUTEWANTED" != "00" ] && [ "$MUTEWANTED" != "03" ] && [ "$MUTEWANTED" != "XX" ] && usage

read_error() {
  echo "FAILURE: Could not read the mute status."
  echo ""
  # Exit with a failure result code
  exit 1
}

write_error() {
  echo "FAILURE: Could not change the mute status."
  echo ""
  # Exit with a failure result code
  exit 1
}

request_mute () {

  # Collect fourth byte of message ID $25D on CAN-C.
  # After $DELAY seconds, stop collecting.

  COMMAND="timeout -s 1 $DELAY /usr/bin/candump -L can1,025D:0FFF"

  # Only collect messages which are a direct response to our own query.
  # All other messages will be ignored.

  RESPONSE=$( $COMMAND | cut -d# -f2 | cut -c7-8 | tail -1)
}

# MAIN PROGRAM LOOP BEGINS HERE ------------------------------------------
# Read the mute status. If it isn't what we want,
# hit the mute button!

while [ $MUTEID != $MUTEWANTED ]
  do

    # See what our mute status is (no actual request, just listening)
    request_mute

    # If no response was found, try again.
    if [ "$RESPONSE" == "" ] ; then
      DELAY=1.6
      /home/pi/bin/wake
      request_mute
    fi

    # If no response was found, try again.
    if [ "$RESPONSE" == "" ] ; then
      DELAY=2.2
      request_mute
      # If no response AGAIN, then exit with an error.
      if [ "$RESPONSE" == "" ] ; then read_error; fi
    fi

    MUTEID=$RESPONSE

    [ "$MUTEWANTED" == "XX" ] && {
      [ "$MUTEID" == "03" ] && { echo ON; exit 0; }
      [ "$MUTEID" == "00" ] && { echo OFF; exit 0; }
      echo UNKNOWN ; exit 1
    }


    # If the mute status isn't what we want, hit the mute toggle button.

    [ "$DEBUG" == "true" ] && echo MUTEID: $MUTEID   MUTEWANTED: $MUTEWANTED
    [ "$MUTEID" != "$MUTEWANTED" ] && {
      # It isn't what we want. We're hitting the MUTE toggle button.
      [ "$DEBUG" == "true" ] && echo TOGGLING MUTE
      cansend can0 2D3#0700010000000000 ; sleep 0.21
    }

    # We're going to try up to FIVE times to change the mute status.
    # After that, exit with an error.

    TRIES=$(( $TRIES + 1 ))
    [ "$TRIES" -gt $MAXTRIES ] && write_error

  done

# A clean exit. Either we reported a value, made a change, or was requested
# to make a change but no change was necessary.

exit 0
