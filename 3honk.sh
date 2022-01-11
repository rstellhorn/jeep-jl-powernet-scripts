#!/bin/bash

echo "10 03" | isotpsend -s 620 -d 504 -p 00: -P a can1
for i in 1 2 3
do
echo HONK
echo "2F D0 AD 03 01" | isotpsend -s 620 -d 504 -p 00:00 -P a  can1
sleep 0.05
echo UNHONK
echo "2F D0 AD 03 00" | isotpsend -s 620 -d 504 -p 00:00 -P a  can1
sleep 0.1
done
