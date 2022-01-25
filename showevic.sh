#!/bin/bash
candump can0,328:0fff | ( while read a b c d e f g h i j k
  do
    [ "$e" -gt 39 ] && echo -n "Line ${e:1:1}: "
    [ "$f$g$h$i$j$k" == "000000000000" ] && echo ""
    printf "%b" "\x${f}\x${g}\x${h}\x${i}\x${j}\x${k}"
    done
)
