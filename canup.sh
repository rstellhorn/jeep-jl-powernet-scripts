#!/bin/sh
ip link set can1 up type can bitrate 500000
ip link set can0 up type can bitrate 125000
ifconfig can0 txqueuelen 65536
ifconfig can1 txqueuelen 65536
