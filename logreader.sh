#!/bin/bash
TMPDIR=/run/tmpfiles.d

# Set only one of these to 1, the rest to 0
UPDATE_SECONDS=1
UPDATE_TENTHS=0
UPDATE_HUNDREDTHS=0

# Enable if you want some alternate values displayed (where available)
SHOW_ALTERNATES=0

flag="02B"
flag2="08B"
flag3="027"

echo "00000000" > /$TMPDIR/0AB
echo "023#FFFF" > /$TMPDIR/023
echo "F" > /$TMPDIR/358
echo "000001" > /$TMPDIR/3D2
echo "00" > /$TMPDIR/232
echo "0000000000000000" > /$TMPDIR/$flag
echo "FFFFFFFFFFFFFFFF" > /$TMPDIR/$flag2
echo "000000000" > /$TMPDIR/07B
echo "000" > /$TMPDIR/079
echo "0000000000000000" > /$TMPDIR/$flag3
echo "000000000000" > /$TMPDIR/322

GO=0
cat $1 | egrep " 023#| 079#| 07B#| $flag3#| 232#| 340#| 358#| 3D2#| 322#| 122#| 0AB#| $flag#| $flag2#" | while read a b c
do

case "$c" in

$flag3#*) echo "${c:4:16}" > /$TMPDIR/$flag3 ;;
$flag2#*) echo "${c:4:16}" > /$TMPDIR/$flag2 ;;
$flag#*)  echo "${c:4:16}" > /$TMPDIR/$flag ;;
079#*)    echo "${c:5:9}"  > /$TMPDIR/079 ;;
07B#*)    echo "${c:5:9}"  > /$TMPDIR/07B ;;
232#*)    echo "${c:6:2}"  > /$TMPDIR/232 ;;
358#*)    echo "${c:5:1}"  > /$TMPDIR/358  ;;
3D2#*)    echo "${c:4:6}"  >  /$TMPDIR/3D2 ;;
0AB#*)    echo "${c:8:4}"  > /$TMPDIR/0AB ;;
122#*)    echo "${c:4:4}"  > /$TMPDIR/122 ;;


023#*)
[ "$UPDATE_HUNDREDTHS" == "1" ] && GO=1
echo "$c" > /$TMPDIR/023
;;

322#*)
echo "${c:4:12}" > /$TMPDIR/322
[ "$UPDATE_TENTHS" == "1" ] && GO=1
;;

# CASE 340
340#*)
echo "$c" | cut -c9-10,19,20 > /$TMPDIR/340
[ "$UPDATE_SECONDS" == "1" ] && GO=1
;;
esac

if [ "$GO" == "1" ]
then

trans=`cat /$TMPDIR/340`
speed="${trans:2:2}"

# The date is done here
time="${a:6:13}"
echo -n "$time  "

rawkey=`cat /$TMPDIR/122`
key="Unk${rawkey} "
case "$rawkey" in
  0301) key="Kill" ;;
  0302) key="Kill" ;;
  0502) key="Acc " ;;
  1502) key="Acc " ;;
  0000) key="Off " ;;
  0001) key="Off " ;;
  4501) key="Strt" ;;
  5D01) key="Crnk" ;;
  4401)
    key="RRun"
    [ "$rpm1" == "0.0k" ] && key="RAcc"
    ;;
  0402) key="Run " ;;
esac
echo -n "KEY: $key  "

BRAKE=`cat /$TMPDIR/079 | cut -c1-3`
BRAKE=$(printf "%d" 0x$BRAKE)
BRAKE=`echo "0k $BRAKE 22.5 / p" | dc`
[ "$BRAKE" -gt 100 ] && BRAKE=100
[ "$BRAKE" -lt 100 ] && BRAKE=" $BRAKE"
[ "$BRAKE" -lt 10 ] && BRAKE=" $BRAKE"
echo -n "BRK:$BRAKE%"

ACC="$(cat /$TMPDIR/07B)"
ACCEL="$(printf "%d" 0x${ACC:0:3})"
ACCEL2="$(printf "%d" 0x${ACC:6:3})"
[ $ACCEL2 -lt 2000 ] && ACCEL2=2000
ACCEL2=`echo "0k $ACCEL2 2000 - 18 / p" | dc`
ACCEL2=`printf "%2d" $ACCEL2`
[ "$ACCEL" -lt 1900 ] && ACCEL=1900
ACCEL=`echo "0k $ACCEL 1990 - 100 * 2000 / p" | dc`
[ "$ACCEL" -lt 0 ] && ACCEL=0
[ "$ACCEL" -lt 100 ] && ACCEL=" $ACCEL"
[ "$ACCEL" -lt 10 ] && ACCEL=" $ACCEL"
echo -n "  ACCL:$ACCEL% (VALVE $ACCEL2%) "

rpm1=`cat /$TMPDIR/322 | cut -c1-4`
#rpm2=`cat /$TMPDIR/322 | cut -c5-8`
rpm1="$(printf "%d" 0x$rpm1)"
[ $rpm1 = 65535 ] && rpm1="0"
#rpm1=`echo "1 k $rpm1 1000 / p" | dc`
#rpm1=`printf "%.1f" $rpm1`"k"
printf "RPM: %4d  " $rpm1
#echo -n "RPM: $rpm1  "

STEER=`cat /$TMPDIR/023 | cut -c5-8`
STEER="$(printf "%d" 0x$STEER)"
STEERSIGN="R "
[[ $STEER -gt 4096  ]] && STEERSIGN="L "
STEER=`echo "4096 $STEER -p" | dc | cut -d- -f2`
STEER=`echo "2k $STEER 200 / 100 * p" | dc | cut -d. -f1`
STEER=`printf "%3d\n" ${STEER}`
SYMBOL="°"
[ "$STEER" -lt  2 ]    && STEERSIGN="  " && STEER="  0"
[ "$STEER" -gt  1000 ] && STEERSIGN="IN" && STEER="VAL" && SYMBOL="D"
echo -n "WHEEL: ${STEERSIGN}${STEER}${SYMBOL}  "

[ "$speed" == "FF" ] && speed="00"
speed="$(printf "%d" 0x$speed)"

gear=`echo $trans | cut -c2`
[ "$gear" == "F" ] && gear="NA"
[ "$gear" == "B" ] && gear="R " && speed="-$speed"
[ "$gear" == "D" ] && gear="P "
if [[ "$gear" =~ ^[1-9]+$ ]]
then gear="D$gear"
fi
[ "$gear" == "0" ] && gear="N "

mph=`cat /$TMPDIR/322 | cut -c5-8`
mph="$( printf "%d" 0x$mph)"
[ $mph == 65535 ] && mph="0"
[ $gear == "R " ] && mph="-$mph"
mph=`echo "2 k $mph 200 / p" | dc`
mph=`printf "%2.2f" $mph`

compass=`cat /$TMPDIR/358`
case "$compass" in
F) compass="??" ;;
0) compass="N " ;;
1) compass="NE" ;;
2) compass=" E" ;;
3) compass="SE" ;;
4) compass="S " ;;
5) compass="SW" ;;
6) compass=" W" ;;
7) compass="NW" ;;
esac
echo -n "DIR: $compass "

echo -n " GEAR: $gear  "

echo -n "(`cat /$TMPDIR/0AB`)  "
echo -n "ODOM: "
odometer=`cat /$TMPDIR/3D2`
odometer="$(printf "%d" 0x$odometer)"
odometer=`echo " $odometer * 50 / 8 " | bc`
if [ "$odometer" == "6" ]
       then
         odometer="0"
         echo -n "??????.?mi  "
       else
        printf '%8.1f' `echo "$odometer / 100" | bc -l`
        echo -n "mi  "
fi

printf "MPH: %5s  " $mph

value=`cat /$TMPDIR/$flag2`
value1=$(( 0x${value:0:4} ))
value2=$(( 0x${value:4:4} ))
value3=$(( 0x${value:8:4} ))
value4=$(( 0x${value:12:4} ))
[ $value1 -eq  49152 ] && value1=0; # Initialization values
[ $value2 -eq  49152 ] && value2=0; # Initialization values
[ $value3 -eq  49152 ] && value3=0; # Initialization values
[ $value4 -eq  49152 ] && value4=0; # Initialization values
[ $value1 -gt  32767 ] && value1="$(( - $value1  + 0x7FFF ))"
[ $value2 -gt  32767 ] && value2="$(( - $value2  + 0x7FFF ))"
[ $value3 -gt  32767 ] && value3="$(( - $value3  + 0x7FFF ))"
[ $value4 -gt  32767 ] && value4="$(( - $value4  + 0x7FFF ))"
[ $value1 -gt  16383 ] && value1="$(( $value1  - 0x3FFF ))"
[ $value2 -gt  16383 ] && value2="$(( $value2  - 0x3FFF ))"
[ $value3 -gt  16383 ] && value3="$(( $value3  - 0x3FFF ))"
[ $value4 -gt  16383 ] && value4="$(( $value4  - 0x3FFF ))"
value1=$(echo "scale=2 ; $value1 / 20" | bc)
value2=$(echo "scale=2 ; $value2 / 20" | bc)
value3=$(echo "scale=2 ; $value3 / 20" | bc)
value4=$(echo "scale=2 ; $value4 / 20" | bc)

# By uncommenting this section, we will display RELATIVE tire speed
# instead of individual tire speed. Useful for watching the balance
# between individual tires throughout a drive.
[ $value1 == "0" ] && value1="0.001"
[ $value2 == "0" ] && value2="0.001"
[ $value3 == "0" ] && value3="0.001"
[ $value4 == "0" ] && value4="0.001"
tirea=$(echo "scale=3 ; ($value2 + $value3 + $value4) / 3" | bc)
tireb=$(echo "scale=3 ; ($value1 + $value3 + $value4) / 3" | bc)
tirec=$(echo "scale=3 ; ($value1 + $value2 + $value4) / 3" | bc)
tired=$(echo "scale=3 ; ($value1 + $value2 + $value3) / 3" | bc)
value1=$(echo "scale=2 ; $value1 / $tirea" | bc)
value2=$(echo "scale=2 ; $value2 / $tireb" | bc)
value3=$(echo "scale=2 ; $value3 / $tirec" | bc)
value4=$(echo "scale=2 ; $value4 / $tired" | bc)
printf "Wheels: [%4s %4s] [%4s %4s]  " $value1 $value2 $value3 $value4

# If the section above is commented, uncomment this.
# If the section above is uncommented, comment this.
# This adjusts the scale used to print tire speeds.
# printf "MPHx4: [%1.2f %1.2f] [%1.2f %1.2f]  " $value1 $value2 $value3 $value4

temp=`cat /$TMPDIR/232`
temp="$(printf "%d" 0x$temp)"
temp=`echo $temp | cut -d" " -f2`
#temp=`echo " $temp * 1.8 + 32 " | bc`
[ "$temp" -lt 100 ] && temp=" $temp"
[ "$temp" -lt 10 ] && temp=" $temp"
[ "$temp" == "255" ] && temp=" ??"
echo -n " RADIO: ${temp} F  "

echo ""
GO=0
fi

done
