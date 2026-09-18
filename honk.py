#!/usr/bin/python3

import time
import can
import isotp
import logging
from can.interfaces.socketcan import SocketcanBus

canIHS = "can0"
canC = "can1"

diag = [0x10, 0x03]
tester = [0x3E, 0x00]
honkon = [0x2F, 0xD0, 0xAD, 0x03, 0x01]
nohonk = [0x2F, 0xD0, 0xAD, 0x03, 0x00]
wakeup = can.Message(data=[0x07, 0, 0, 0, 0, 0, 0, 0], is_extended_id=False, arbitration_id=0x2D3, channel="can1")


def my_error_handler(error):
    # Called from a different thread, needs to be thread safe
    logging.warning('IsoTp error happened : %s - %s' % (error.__class__.__name__, str(error)))

bus = can.interface.Bus('can1', interface='socketcan')
notifier = can.Notifier(bus, [])
addr = isotp.Address(isotp.AddressingMode.Normal_11bits, rxid=0x504, txid=0x620)
params = {
     'tx_data_min_length' : 8,
     'tx_padding' : 0x00,
     'stmin' : 0xF1
}
stack = isotp.NotifierBasedCanStack(
    bus,
    notifier,
    address=addr,
    error_handler=my_error_handler,
    params=params
    )

def cantpmsg(x):
    stack.send(x,0,1)
    while stack.transmitting():
            time.sleep(0.005)
    return(stack.recv(block=True, timeout=5.0))

def honk(times=1):
    while times > 0:
        print("Honk")
        print(cantpmsg(bytes(honkon)))
        #time.sleep(.05)
        print(cantpmsg(bytes(nohonk)))
        times -= 1
        if times > 0:
            time.sleep(.2)
            print("Tester Present")
            print(cantpmsg(bytes(tester)))

try:
    bus.send(wakeup, timeout=1)
    time.sleep(.2)
    stack.start()
    print("Diagnostics Mode")
    print(cantpmsg(bytes(diag)))
    honk(3)
    print("Payload transmission successfully completed.")
except isotp.BlockingSendFailure:
    print("Send failed")
finally:
    stack.stop()
    bus.shutdown()
