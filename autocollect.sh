#!/bin/bash

# AUTOCOLLECT: This script monitors the state of the engine, launching
# independent functions when vehicle is powered on, the engine is running,
# every minute the engine is running, every 10 minutes the engine is
# running, every hour the engine is running, and when the engine has been
# shut down.

# HERE ARE THE FUNCTIONS YOU MAY POPULATE AS NEEDED ------------------

# Called when the vehicle has been powered up (TIP button or remote start)

vehiclepoweredon () {
  echo "$(date) AUTOCOLLECT: Vehicle power-on items go here."
}

# Called when the engine was just started and is stable

enginestarted () {
  echo "$(date) AUTOCOLLECT: Post engine-start items go here."
}

# Called in one minute intervals after the engine is running.

oneminute() {
  echo "$(date) AUTOCOLLECT: One minute items go here."
}

# Called in ten minute intervals after the engine is running.

tenminute() {
  echo "$(date) AUTOCOLLECT: Ten minute items go here."
}

# Called in one hour intervals after the engine is running.

onehour() {
  echo "$(date) AUTOCOLLECT: One hour items go here."
}

# Called when the engine is shutting down or has been shut down.

engineshutdown () {
  echo "$(date) AUTOCOLLECT: Engine shutdown items go here."

  # Flush out any cached/pending IO activity (like to the SD card).
  sync ; sync ; sleep 5 ; sync ; sync

}

# THE MAIN SCRIPT BEGINS HERE ---------------------------------------

echo "$(date) AUTOCOLLECT: Script started, waiting for events."

# Set some flags that we'll use later.

VEHICLEON=0
STARTED=0
LAST=77777

# THE ENGINE MONITORING LOOP BEGINS HERE ----------------------------

COMMAND="/usr/bin/candump -T 1000 -L can1,0077:0FFF"
$COMMAND | while read TIME BUS MESSAGE
do

  # Regardless of what rate we receive messages at, we will analyze
  # them only once per second. (Conserves CPU.)

  NOW=$SECONDS
  [ "$NOW" != "$LAST" ] && {
    DATA=${MESSAGE:4}
    STATE=${DATA:0:4}

    # A work-around for hexadecimal digits during remote start.

    [ "$STATE" == "5D21" ] && STATE=5555

    # Determine when the engine is running.

    if [ "$STATE" == "0422" -o "$STATE" == "4421" ]
      then

        [ $STARTED -eq 0 ] && enginestarted &
        STARTED=1

        # Call the oneminute function once per minute.
        [ $(( $SECONDS % 60 )) -eq 45 ] && oneminute &

        # Call the tenminute function once per ten minutes.
        [ $(( $SECONDS % 600 )) -eq 599 ] && tenminute &

        # Call the onehour function once per hour.
        [ $(( $SECONDS % 36000 )) -eq 35970 ] && onehour &
       fi

    # Determine when the vehicle has been powered up.

    if [ "$STATE" -gt "0399" ]
      then
        # Vehicle is on. Engine may or may not be running.
        [ $VEHICLEON -eq 0 ] && vehiclepoweredon &
        VEHICLEON=1
      fi

    # Determine when the engine is no longer running.

    if [ "$STATE" -lt "0400" ]
      then

        # Engine has just shut down or is shutting down right now.

        [ $STARTED -eq 1 ] && {
          engineshutdown &
          break 2
          break
          exit 0
        }
        STARTED=0
        VEHICLEON=0
      fi
  }
  LAST=$NOW
done

# THIS LAST PART HAPPENS WHEN ALL BUS TRAFFIC HAS DIED DOWN ---------

echo $(date) AUTOCOLLECT: No bus traffic, script ending.
