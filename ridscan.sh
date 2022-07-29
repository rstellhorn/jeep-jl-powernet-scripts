#!/bin/bash
module=$1
shift 1
a=$(printf "%d" 0x$1)
if [ $? -ne 0 ] ; then a=0 ; fi
if [ "$a" == "" ] ; then a=0 ; fi
b=$(printf "%d" 0x$2)
if [ $? -ne 0 ] ; then b=65535 ; fi
if [ "$b" == "" ] ; then b=65535; fi

echo START: $a END: $b

for i in `seq $a $b`; do printf "%4x ------" $i ; rid $module $( printf %4x $i )
  while [ $? == 99 ] ; do
    echo "REDO:" ; rid $module $( printf %4x $i )
  done
done
