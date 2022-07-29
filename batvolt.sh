#!/bin/bash

error() {
  echo "ERROR: Is the vehicle off? Battery voltage data not found."
  echo "DEBUG: A valid ID 2C2 message was not seen on CAN-IHS within 2 seconds."
  echo " "
  # Exit with a failure result code
  exit 1
}

initialize () {
COMMAND="timeout -s 9 2 /usr/bin/candump -L can0,02C2:0fff"
can2C2=$( $COMMAND | tail -1 )
}

initialize
if [ "$can2C2" == "" ] ; then
  # Wake the CAN bus and try again.
  cansend can0 2D3#0700000000000000 ; sleep 1.1
  initialize
  # Display an error and exit if no messages were received.
  [ "$can2C2" == "" ] && error
fi

if [ "$( echo "$can2C2" | cut -c30-43 )" == "FFFFFFFFFFFFFF" ] ; then error; fi
temp="$( echo "$can2C2" | cut -c34-35 )"
temp="$( printf "%d" 0x$temp )"
temp="$( echo "1 k $temp 10 / p" | dc )"

echo $temp vdc
