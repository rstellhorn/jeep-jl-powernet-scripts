#!/bin/bash

error() {
  echo "ERROR: Is the vehicle off? Battery voltage data not found."
  echo "DEBUG: A valid ID 2C2 message was not seen on CAN-IHS within 2 seconds."
  echo " "
  # Exit with a failure result code
  exit 1
}

COMMAND="timeout -s 9 2 /usr/bin/candump -L can0,02C2:0fff"
can2C2=$( $COMMAND | tail -1 )

if [ "$can2C2" == "" ] ; then error; fi
if [ "$( echo "$can2C2" | cut -c30-43 )" == "FFFFFFFFFFFFFF" ] ; then error; fi
temp="$( echo "$can2C2" | cut -c34-35 )"
temp="$( printf "%d" 0x$temp )"
temp="$( echo "1 k $temp 10 / p" | dc )"

echo $temp vdc
