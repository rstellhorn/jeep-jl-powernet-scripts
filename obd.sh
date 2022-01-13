#!/bin/bash

# NOTE: This script sends an OBD-II command and returns
#       with the response string.

error() {
  # Exit with a message and a failure result code
  echo "NO RESPONSE"
  exit 1
}

initialize () {
  # 1/10th of a second from now, send the OBD-II query with the
  # user-provided PID.

  ( sleep 0.1 ; cansend can1 7E0#0201${PID}0000000000 ) &

  # Collect any messages on CAN-C which have an ID of $7E8.
  # After a predefined number of seconds, stop collecting.

  COMMAND="timeout -s 1 $WAIT /usr/bin/candump -L can1,7E8:0FFF"

  # Only look for messages which are a successful response to our
  # particular OBD-II query.
  # UDS query. If we received more than one response, only use
  # the last one. And isolate the output so it only contains the
  # byte that we're looking for.

  RESPONSE=$( $COMMAND | egrep "\#..41${PID}|\#10..41${PID}" | cut -d# -f2 | head -1)
  DATA=${RESPONSE:6}
  # As long as we receive data, continue evaluating the output.
  [ "$DATA" != "" ] && {
    LENGTH=${RESPONSE:0:2}
    # If the length is 10 (HEX) then we have a response longer than
    # we can process, and in a different format. We'll have to adjust
    # things slightly so that we can read the first four characters.
    [ $LENGTH == "10" ] && {
      LENGTH=${RESPONSE:2:2}
      DATA=${DATA:2}
    }
    # Extract the message length and message data.
    LENGTH=$( printf "%d" 0x$LENGTH ) 2>/dev/null
    LENGTH=$(( $LENGTH - 2 )) >> /dev/null 2>/dev/null
    DATA=${DATA:0:$(( LENGTH * 2 ))} 2>/dev/null
  }
}

# MAIN CODE BEGINS HERE ---------------------------------------------------

# Take the user-provded OBD-II PID and convert it to uppercase.
# If they did not provide a pid, print a help message and exit.

PID=$( echo $1 | tr '[:lower:]' '[:upper:]' )
if [ "$PID" == "" ] ; then
  echo "USAGE: `basename $0` [XX]"
  echo ""
  exit 1
fi

# If they provided a single hex digit, then prepend it with a 0.
if [ $(echo ${#PID}) -eq 1 ] ; then
  PID="0$PID"
fi

# Test to see if it is a hex number. If not, print an error and exit.
printf "%d" 0x$PID > /dev/null 2>&1
if [ $? -ne 0 ] ; then
  echo "ERROR: $PID is not a valid hexadecimal value"
  echo ""
  exit 2
fi

# Send the OBD-II query to the BCM.
# NOTE: This REQUIIRES the vehicle to be running.
WAIT=0.2
initialize

# If there was no response, we could have missed the message. Or it
# could have taken too long to reply. Try again, this time waiting
# up to 0.5 seconds for a reply.
if [ "$LENGTH" == "" ] ; then
  WAIT=0.5
  initialize
  if [ "$LENGTH" == "" ] ; then error; fi
fi

# Print the response as individual decimal numbers.
# They will need to be reassembled via the published OBD-II formulas.
for i in $(echo $DATA | fold -w2 | paste -sd' ')
do
  printf "%d " 0x$i
done
echo ""
