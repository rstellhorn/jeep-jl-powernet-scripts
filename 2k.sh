#!/bin/bash

# No wakeup script necessary
# If the engine isn't running, this whole thing is useless anyhow.

# Diagnostic session (requesting more rights)
echo "10 92" |  isotpsend -s 7E0 -d 7E8 -p 00:00 -P a can1
sleep 0.25

# Tester is present - remain in diagnostic session
# This is probably redundant, but I'm leaving it here for now.
echo "3E 00" | isotpsend -s 7E0 -d 7E8 -p 00:00 -P a can1
sleep 0.25

# Set engine to 2K RPMs
echo "31 05 07 D0" | isotpsend -s 7E0 -d 7E8 -p 00:00 -P a can1

# Maintain current setting by continuing to tell the Wrangler
# that a testing device is still connected to it. As soon as we
# exit this script (CONTROL-C or a kill command), our
# messages to the module will stop, and when that happens,
# we'll exit out of diagnostic mode and the engine RPM
# command will automatically be cancelled.

while [ 1 ]
do
  sleep 0.25
  # Tester is present - remain in diagnostic session
  echo "3E 00" | isotpsend -s 7E0 -d 7E8 -p 00:00 -P a can1
done
