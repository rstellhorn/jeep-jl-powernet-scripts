#!/bin/bash

touch /tmp/remote

# Do some quick WiFi Tuning (might produce errors, that's okay)
iwconfig wlan0 rate auto
iwconfig wlan0 rts 2304
iwconfig wlan0 frag 2304

# Monitors for *remote* door lock/unlock commands and uses
# those to disable/enable the Raspberry Pi's WiFi transmitter.
#
# Locked = WiFi Off (secure)
# Unlocked = WiFi On (less secure)

# Tunable variables:

# Name for the CAN-IHS interface (can0, can1, vcan0, etc)
CANIHS=can0
WIFIDEV=wlan0
DEBUG=false  # Values: true,false,raw
LOCKED=0

LASTREMOTE="1C0#FFFFFFFFFFFF"
sleep 5

candump -L $CANIHS,01C0:0FFFF | while read time bus REMOTE
do

[ $DEBUG == "raw" ] && echo CAN-IHS data: $REMOTE
HEADER="TIME  : $time $( date )\nDATA  : $REMOTE"

# LOCK COMMAND: WIFI TURNED OFF (SECURED)
if [ "$REMOTE" == "1C0#210000900000" ] ; then
  if [ "$REMOTE" != "$LASTREMOTE" ] ; then
    [ $DEBUG == "true" ] && echo -e "$HEADER"
    [ $DEBUG == "true" ] && echo "EVENT : KEYFOB LOCK COMMAND RECEIVED"
    [ $DEBUG == "true" ] && echo "ACTION: NONE"
    [ $DEBUG == "true" ] && echo ""
  fi
fi

# 1ST UNLOCK COMMAND: NO ACTION TAKEN
if [ $REMOTE == "1C0#230000900000" ] ; then
  if [ "$REMOTE" != "$LASTREMOTE" ] ; then
    [ $DEBUG == "true" ] && echo -e "$HEADER"
    [ $DEBUG == "true" ] && echo "EVENT : KEYFOB 1ST UNLOCK COMMAND RECEIVED"
    [ $DEBUG == "true" ] && echo "ACTION: NONE"
    [ $DEBUG == "true" ] && echo ""
  fi
fi

# 2ND UNLOCK COMMAND: WIFI TURNED ON (LESS SECURED)
if [ $REMOTE == "1C0#240000900000" ] ; then
  if [ "$REMOTE" != "$LASTREMOTE" ] ; then
    [ $DEBUG == "true" ] && echo -e "$HEADER"
    [ $DEBUG == "true" ] && echo "EVENT : KEYFOB 2ND UNLOCK COMMAND RECEIVED"

    # Flip between locked (LOCKED=1) and unlocked (LOCKED=0)
    LOCKED=$(( ! $LOCKED ))

    [ $LOCKED -eq 0 ] && {
      # ENABLING WIFI TRANSMITTER
      # All commands appear to be necessary even if they return errors.
      # Use extreme care when editing the following section.
      echo $(date) REMOTE: Turning on Wi-Fi Device
      iwconfig $WIFIDEV txpower on
      sleep 5
      iwconfig $WIFIDEV txpower auto
      sleep 2
      ifconfig $WIFIDEV up
    }

    [ $LOCKED -eq 1 ] && {
      # DISABLING WIFI TRANSMITTER
      echo $(date) REMOTE: Turning off Wi-Fi Device
      ifconfig $WIFIDEV down
      sleep 2
      iwconfig $WIFIDEV txpower off
    }

    [ $DEBUG == "true" ] && echo ""
  fi
fi

# IDLE (NO COMMANDS): NO ACTION
if [ $REMOTE == "1C0#000000800000" ] ; then
  if [ "$REMOTE" != "$LASTREMOTE" ] ; then
    [ $DEBUG == "true" ] && echo -e "$HEADER"
    [ $DEBUG == "true" ] && echo "EVENT : IDLE STATE (DEFAULT) HAS RESUMED"
    [ $DEBUG == "true" ] && echo "ACTION: NONE"
    [ $DEBUG == "true" ] && echo ""
  fi
fi

# KEEP TRACK OF WHAT THE PREVIOUS COMMAND WAS.
# THIS MAY BE USEFUL TO TRACK WHEN MONITORING OTHER CAN BUS IDs.
LASTREMOTE=$REMOTE

done
