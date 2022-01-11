#!/bin/bash

# Wake up the CAN bus.
cansend can0 2D3#0700000000000000
sleep 2

# 2 byte message: Enter Diagnostic Session Control
# Subtype: Extended Diagnostic Session
cansend can1 620#0210030000000000

sleep 1

# Perform an infinite loop

while [ 1 ]
do

# 5 byte message: Input/Output Control by Identifier
# Identifier $D1BE, option $0301 (overhead courtesy light on)
echo Third brake light on
cansend can1 620#052FD1BE03010000
sleep 0.5

# 5 byte message: Input/Output Control by Identifier
# Identifier $D1BE, option $0300 (overhead courtesy light off)
echo Third brake light off
cansend can1 620#052FD1BE03000000
sleep 0.5

done
