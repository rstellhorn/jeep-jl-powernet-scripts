#!/bin/sh

ip link add dev vcan0 type vcan
ip link add dev vcan1 type vcan
ip link set vcan0 up
ip link set vcan1 up
