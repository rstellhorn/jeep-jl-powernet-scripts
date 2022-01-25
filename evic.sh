

#!/bin/bash

# This script turns text into an EVIC dash message
# STRING TIPS: https://linuxhandbook.com/bash-string-length/
# ARRAY  TIPS: https://www.shell-tips.com/bash/arrays/

[ "$2" == "" ] && {
  echo "USAGE: $(basename $0) [line] [text]"
  echo "  Displays [text] on the EVIC music information page"
  echo "  Valid line numbers are: 2 (artist), 3 (title) 1 (input name)"
  echo ""
  exit 1
}

FUNCTION=$1
shift
declare -a message
string="$@"
length=${#string}
remainder=$(( ( 3 - ( $length % 3 ) ) % 3 ))
POSITION=1
for i in $( seq 1 $length)
do
  message[$POSITION]='00'
  POSITION=$(( $POSITION + 1 ))
  message[$POSITION]=$(printf "%02X" "'${string:$(( i - 1 )):1}'")
  POSITION=$(( $POSITION + 1 ))
done
for i in $( seq 1 $remainder )
do
  message[$POSITION]=00
  POSITION=$(( $POSITION + 1 ))
  message[$POSITION]=00
  POSITION=$(( $POSITION + 1 ))
  length=$(( $length + 1 ))
done
lines=$(( $length / 3 ))
[ "$DEBUG" == "true" ] && echo "FUNCTION: $function"
[ "$DEBUG" == "true" ] && echo "STRING  : $string"
[ "$DEBUG" == "true" ] && echo "LENGTH  : $length characters ($lines lines)"
[ "$DEBUG" == "true" ] && echo "ENCODED : ${message[*]}"

POSITION=1;INIT=4
for i in $( seq $(( $lines -1 )) -1 0 )
do
  LINE=$(printf "%x" $i)
  COMMAND="cansend can0 328#${LINE}0.${INIT}${FUNCTION}"
  for j in 1 2 3 4 5 6
  do
    COMMAND="$COMMAND.${message[$POSITION]}"
    POSITION=$(( $POSITION + 1 ))
  done
  $COMMAND ; sleep 0.002
  INIT=0
done
cansend can0 328#00.00.00.00.00.00.00.00
sleep 0.005


