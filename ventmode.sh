

#!/bin/bash

# This script reads or modifies the currently selected HVAC mode.

usage() {
  echo ""
  echo "USAGE: $(basename $0) [vent id]"
  echo "  Possible IDs: 00=Defrost,     02=Defrost+Feet, 04=Feet,"
  echo "                06=Panel+Floor, 08=Panel,        0F=Auto"
  echo " "
  exit 1
}

TRIES=0
MAXTRIES=6
DEBUG=false
DELAY=0.6
VENTID=99
VENTWANTED=$(echo $1 | tr '[:lower:]' '[:upper:]')
[ "$VENTWANTED" == "-H" ] && usage
[ "$VENTWANTED" == "HELP" ] && usage
[ ${#VENTWANTED} -ne 2 ] && VENTWANTED="XX"

read_error() {
  echo "FAILURE: Could not read the vent mode from the HVAC Module."
  echo ""
  # Exit with a failure result code
  exit 1
}

write_error() {
  echo "FAILURE: Could not change the vent mode in the HVAC Module."
  echo ""
  # Exit with a failure result code
  exit 1
}

request_hvac_vent () {
  # In 0.1 second from now...
  # ...send a request to the HVAC Module asking for the vent mode status.

  ( sleep 0.1 ; cansend can0 783#0322029800000000 ) &

  # Collect all responses from the HVAC Module at ID $503 on CAN-IHS.
  # After $DELAY seconds, stop collecting.

  COMMAND="timeout -s 1 $DELAY /usr/bin/candump -L can0,0503:0FFF"

  # Only collect messages which are a direct response to our own query.
  # All other messages will be ignored.

  RESPONSE=$( $COMMAND | grep \#04620298 | cut -d# -f2 | cut -c9-10 | tail -1)
}

# MAIN PROGRAM LOOP BEGINS HERE ------------------------------------------
# Read the HVAC Vent Mode. If it isn't what we want,
# hit the HVAC Mode button. Lather, rinse, repeat.

while [ $VENTID != $VENTWANTED ]
  do

    # Ask the HVAC module for which vents have been selected.
    request_hvac_vent

    # If no response was found, try again.
    if [ "$RESPONSE" == "" ] ; then
      DELAY=1.2
      request_hvac_vent
    fi

    # If no response was found, try again.
    if [ "$RESPONSE" == "" ] ; then
      DELAY=1.8
      request_hvac_vent
      # If no response AGAIN, then exit with an error.
      if [ "$RESPONSE" == "" ] ; then read_error; fi
    fi

    VENTID=$RESPONSE

    [ "$VENTWANTED" == "XX" ] && {
      echo $VENTID
      exit 0
    }

    # If the current HVAC vent mode isn't the one we want,
    # then hit the appropriate HVAC control button.

    [ "$DEBUG" == "true" ] && echo VENTID: $VENTID   VENTWANTED: $VENTWANTED
    [ "$VENTID" != "$VENTWANTED" ] && {
      # If they wanted auto vents, let's just hit the auto button and exit.
      [ "$VENTWANTED" == "0F" ] && {
        # Turns on the automatic FAN and VENT control
        cansend can0 2D3#0700000000020000; sleep $DELAY
        exit 0
      }
      # If they wanted the front defroster, then hit the front
      # defroster button and exit.
      [ "$VENTWANTED" == "00" ] && {
        # Turns on the HVAC front defroster
        cansend can0 2D3#0700000000800000; sleep $DELAY
        exit 0
      }
      # Otherwise, hit HVAC Mode button to cycle the setting
      cansend can0 2D3#0700000000000800 ; sleep $DELAY
    }

    # We're going to try up to FIVE times to change the HVAC mode
    # to our desired selection. After that, exit with an error.

    TRIES=$(( $TRIES + 1 ))
    [ "$TRIES" -gt $MAXTRIES ] && write_error

  done

# A clean exit. Either we reported a value, made a change, or was requested
# to make a change but no change was necessary.

exit 0

