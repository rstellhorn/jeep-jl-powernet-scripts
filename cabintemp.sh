#!/bin/bash

error() {
  echo "N/A"
  # Exit with a failure result code
  exit 1
}

# Just in case the CAN bus is asleep, wake it up with a fake button press.

cansend can0 2D3#0700000000000000 ; sleep 1

# 1/10th of a second from now, send the UDS query for Cabin Temperature
# NOTE: It currently responds with cabin temperature in Fahrenheit. It is
#       not known if there is a switch which might also make it output
#       instead of Celsius.

( sleep 0.1 ; cansend can0 783#0322D01E00000000 ) &

# Collect any messages on CAN-IHS which have an ID of 0503.
# After 0.5 seconds, stop collecting.

COMMAND="timeout -s 1 0.6 /usr/bin/candump -L can0,0503:0FFF"

# Only look for messages which are a successful response to our
# UDS query. If we received more than one response, only use
# the last one. And isolate the output so it only contains the
# byte that we're looking for.

RESPONSE=$( $COMMAND | tail -1 | grep \#100962D01E | cut -d# -f2 | cut -c15-16)

# If no response was found, exit gracefully with an error.

if [ "$RESPONSE" == "" ] ; then error; fi

# Convert out byte from hexadecimal to decimal.

RESPONSE=$( printf "%d" 0x$RESPONSE )

# Subtract 54 (an arbitrary magic number) from the response so that we have
# an accurate reading which can range from -54 to 201 degrees Fahrenheit.

RESPONSE=$( expr $RESPONSE - 54 )

# Print the temperature to standard output.

echo ${RESPONSE}F
