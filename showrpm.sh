

#!/bin/bash

# The message ID that we're listening for.
id=can0,0322:0FFF

# The starting position inside the message (1=the first hexadecimal digit)
pos=1

# How many hexadecimal digits we want to work with
# (1=nibble, 2=byte, 4=word, etc)
size=4

# How often we update the name of the page. It counts the number of times
# a new message (of the type selected above) has to appear on the CAN bus
# before we refresh the page title. (20=we update the title every
# time 20 new messages are received)
# MAKING THIS VALUE TOO LOW MAY INTRODUCE REFRESH LAG.
trate=20

# This is the name that we print on the bottom of the music info page.
tname="RPM"

# This controls how often we refresh the value that we're monitoring.
# It determines how many messages must appear appear on the CAN bus
# before we display the latest value. (1=always display the latest value,
# 2=display every other new value, 10=display every 10th new value)
# BE CAREFUL OF MESSAGES WITH QUICK UPDATES (like 1/100th of a second)
# YOU WILL CREATE LAG IF YOU REFRESH THOSE WITH A REFRESH RATE OF 1.
rate=1

# MAIN SCRIPT BEGINS HERE -------------------------------------------

# Adjusts our human-readable number into an actual offset. Do not modify.
pos=$(($pos+3))

# Read only our selected message from the CAN bus.
# Continually repeat this loop unless we haven't received any messages in
# a 10 second period (10000ms).
candump -T 10000 -L $id | \
( while read a b c
  do
    # Increment the message counter.
    n=$((n+1))

    # If the time is right, refresh the title.
    [ $(( $n % $trate )) -eq 0 ] && ./evic.sh 1 "$tname"

    # Extract the value we selected.
    value=${c:$pos:$size}

    # Create the text we're going to display.
    # We convert our hexadecimal value into a decimal number.
    text="$(printf "%d" "0x${value}")"

    # If the text is 65535 ($FFFF), print the word OFF instead.
    [ "$text" == "65535" ] && text=OFF

    # If the time is right, refresh with the latest text.
    [ $(( $n % $rate )) -eq 0 ] && ./evic.sh 3 "$text"
  done
)


