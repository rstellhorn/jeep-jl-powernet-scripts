!/bin/bash

error() {
  echo "N/A"
  # Exit with a failure result code
  exit 1
}

initialize () {
  # Issue a "Get Data By Identifier" command to the specified module
  # and wait (with timeout) for a response.

  ( sleep 0.04 ; \
    echo "22 $ID" | /usr/bin/isotpsend -s $SOURCE -d $DEST -p 00:00 -P l $BUS ) &

  # Collect the response. If no response in 8 seconds, abort.
  # NOTE: Most of the time, 8 seconds is excessive. But some Identifiers
  #       will actually take this much time, if not more.

  COMMAND="timeout -s 1 8 /usr/bin/isotprecv -s $SOURCE -d $DEST -p 00:00 -P l $BUS"

  RESPONSE="$( $COMMAND )"

# Get rid of the last character (trailing space)
  RESPONSE=${RESPONSE}

  # We could get rid of ALL SPACING between hexadecimal numbers,
  # but let's not do that. Code left here in case it is useful elsewhere.
  # DATA=$( echo ${RESPONSE:9} | tr -d "[:blank:]" )

  # POPULATE A FEW VARIABLES WE'LL USE BELOW

  DATA=$( echo ${RESPONSE:9} )
  RID="${RESPONSE:0:2}"
  SID="22"
  SUCCESS="$( printf "%X" $(( 0x$SID + 0x40 )) )"
  OK=99

  if [ "$RID" == "$SUCCESS" ] ; then
    OK=0
    echo "SUCCESS"
    echo "${RESPONSE:9}"

    # We need a better solution, but for now, we're storing data as
    # FILENAMES under the /home/pi/modules/ directory. This works
    # up until the point we have a lot of data to store, then the
    # filename becomes too big. In that case, instead of storing the
    # data as a filename, it creates a file called FILE and stores
    # the data in there. Yuck, yuck, yuck!

    if [ ! -d /home/pi/modules/$MODULE/$OPERATION/${ID:0:2}${ID:3:2} ] ; then
      mkdir -p /home/pi/modules/$MODULE/$OPERATION/${ID:0:2}${ID:3:2}
    fi
    touch /home/pi/modules/$MODULE/$OPERATION/${ID:0:2}${ID:3:2}/"${DATA}"
    if [ $? -ne 0 ] ; then
        echo $DATA | cat > /home/pi/modules/$MODULE/$OPERATION/${ID:0:2}${ID:3:2}/FILE
    fi
  fi

  if [ "$RID" == "7F" ] ; then
    OK=1
    echo "NEGATIVE RESPONSE"
    echo "$RESPONSE"
  fi

  if [ "$OK" == "99" ]
    then
      echo "UNKNOWN RESPONSE"
      echo ${RESPONSE}
    fi

exit $OK

}

# MAIN CODE BEGINS HERE

MODULE=$( echo $1 | tr '[:upper:]' '[:lower:]' )
OPERATION=rid
OK=0

# In this section, we translate module names into the concrete variables
# we need to use. We're doing these as if...then statements when we should
# probably be working with arrays. But this is a product of figuring things
# out when you go along and quickly putting a solution in place because you
# need something here and now. This needs to be revisited.

if [ "$MODULE" == "bcm" ] ; then
    OK=1
    SOURCE=620
    DEST=504
    BUS=can1 # CAN-C
fi

if [ "$MODULE" == "sccm" ] ; then
    OK=1
    # INVALID INFORMATION - NEEDS CORRECTED
    SOURCE=763
    DEST=4E3
    BUS=can1 # CAN-C
fi

if [ "$MODULE" == "radio" ] ; then
    OK=1
    SOURCE=7BF
    DEST=53F
    BUS=can0 # CAN-IHS
fi

   [ "$MODULE" == "ipc" ] && MODULE="ipcm"
if [ "$MODULE" == "ipcm" -o "$MODULE" == "evic" ] ; then
    OK=1
    MODULE="ipcm" # Standardizing on Instrument Panel Cluster Module
    SOURCE=742
    DEST=4C2
    BUS=can1 # CAN-C
fi

if [ "$MODULE" == "sccm" ] ; then
    OK=1
    SOURCE=123
    DEST=321
    BUS=can0 # CAN-IHS
fi

if [ "$MODULE" == "hvac" ] ; then
    OK=1
    SOURCE=783
    DEST=503
    BUS=can0 # CAN-IHS
fi

# echo "MODULE: $MODULE  BUS: $BUS  SOURCE: $SOURCE  DEST: $DEST"

if [ $OK -ne 1 ] ; then
    echo "INVALID MODULE SPECIFIED: $MODULE"
    exit 99
fi

shift 1

INPUT=$( printf "%04X" 0x$@ 2>/dev/null )
if [ $? -ne 0 ]
  then
     echo "INVALID IDENTIFIER SPECIFIED: $@"
     exit 1
  fi

ID="${INPUT:0:2} ${INPUT:2:2}"
# echo "INPUT: $INPUT   ID: $ID"

# Send our UDS request and store the response.
initialize
