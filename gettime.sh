

#!/bin/bash

# This script reads the current date and time from the CAN-IHS bus
# and returns the output.

# If we run into an error, this fuction displays a generic error message and exits.
error() {
  echo "ERROR: Is the vehicle off? Current time and date not found."
  echo "DEBUG: A valid ID 350 message was not seen on CAN-IHS within 3 seconds."
  echo " "
  # Exit with a failure result code
  exit 1
}

initialize () {
# The method we use to read any CAN-IHS message with an ID of 350 is stored in $COMMAND.
# The "timeout" command limits how long we're willing to wait to only one second.
COMMAND="timeout -s 9 1.1 /usr/bin/candump -L can0,0350:0fff"

# We begin by grabbing out message.
# If we got lucky and received two, we only keep the last one.
can350=$( $COMMAND | tail -1 )
}

initialize
# Retry if no message received.
if [ "$can350" == "" ] ; then
  # Wake the CAN bus and try again.
  cansend can0 2D3#0700000000000000 ; sleep 1.1
  initialize
  # Display an error and exit if no messages were received.
  [ "$can350" == "" ] && error
fi

# Display an error and exit if the clock has not been initialized.
if [ "$( echo "$can350" | cut -c30-43 )" == "FFFFFFFFFFFFFF" ] ; then error; fi

# Extract the hexadecimal numbers from the message.
rawtime="$( echo "$can350" | cut -d# -f2 )"

# Reformat the numbers as hexadecimal bytes with spaces in between them.
rawtime="$( echo "$rawtime" | fold -w2 | paste -sd' ' )"

# Change year so that it is represented as one word instead of two bytes.
rawtime="$( echo "$rawtime" | cut -c1-11,13-20 )"

# Read the six hexadecimal fields as: seconds minutes hours year month day
# Convert to decimal, Reformat as: day/month/year hours:minutes:seconds
time="$( echo $rawtime | { read seconds minutes hours year month day ; \
  printf "%d/%d/%d %02d:%02d:%02d\n" \
    0x$month 0x$day 0x$year 0x$hours 0x$minutes 0x$seconds ; } )"

# Print the result to the screen
echo "$time"

# Exit with a successful result code
exit 0

