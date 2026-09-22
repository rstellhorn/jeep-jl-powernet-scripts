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
vin = [0x22, 0xF1, 0x90]
dtccount = [0x19, 0x01, 0x0D]
dtclist = [0x19, 0x02, 0x0D]
wakeup = can.Message(data=[0x07, 0, 0, 0, 0, 0, 0, 0], is_extended_id=False, arbitration_id=0x2D3, channel="can1")


def my_error_handler(error):
    # Called from a different thread, needs to be thread safe
    logging.warning('IsoTp error happened : %s - %s' % (error.__class__.__name__, str(error)))

bus = can.interface.Bus('can1', interface='socketcan')

modules = [
    ("bcm", isotp.Address(isotp.AddressingMode.Normal_11bits, rxid=0x504, txid=0x620)),
    ("pcm", isotp.Address(isotp.AddressingMode.Normal_11bits, rxid=0x7E8, txid=0x7E0)),
    ("tcm", isotp.Address(isotp.AddressingMode.Normal_11bits, rxid=0x7E9, txid=0x7E1)),
    ("bpcm", isotp.Address(isotp.AddressingMode.Normal_11bits, rxid=0x7EC, txid=0x7E4)),
    ("radio", isotp.Address(isotp.AddressingMode.Normal_11bits, rxid=0x53F, txid=0x7BF))]

params = {
     'tx_data_min_length' : 8,
     'tx_padding' : 0x00,
     'stmin' : 0xF1,
     'blocking_send' : True
}
stack = isotp.CanStack(
    bus,
    address=modules[0][1],
    error_handler=my_error_handler,
    params=params
    )

def parse_dtc(response: bytearray) -> list:
    if len(response) < 3:
        return
    if response[0] != 0x59 or response[1] != 0x02:
        if response[0] == 0x7F:
            return
    dtc_list = []
    prefixes = {0x00: 'P', 0x40: 'C', 0x80: 'B', 0xC0: 'U'}
    for i in range(3, len(response), 4):
        if i + 4 > len(response):
            break
        dtc_bytes = response[i : i + 3]
        prefix_bits = dtc_bytes[0] & 0xC0
        prefix = prefixes.get(prefix_bits, 'Unknown')
        status_byte = response[i + 3]
        body = f"{(dtc_bytes[0] & 0x3F):02X}{dtc_bytes[1]:02X}{dtc_bytes[2]:02X}"
        dtc_hex = f"{prefix}{body}"
        status_hex = f"{status_byte:02X}"
        
        dtc_list.append({
            "dtc": dtc_hex,
            "status": status_hex
        })
    return dtc_list

def cantpmsg(x):
    stack.send(x,0,1)
    return(stack.recv(block=True, timeout=5.0))
    

try:
    bus.send(wakeup, timeout=1)
    time.sleep(.2)
    stack.start()
except:
    print("Not good")

for mod in modules:
    try:
        stack.set_address(mod[1])
        print(mod[0])
        print("Diagnostics Mode")
        print(cantpmsg(bytes(diag)).hex(' '))
        print("DTC Count:")
        dtccount = int.from_bytes(cantpmsg(bytes(dtccount))[4:6], byteorder='big')
        print(dtccount)
        if dtccount > 0:
            print("DTC List:")
            dtclist = parse_dtc(cantpmsg(bytes(dtclist)))
            for item in dtclist:
                print(f"DTC: {item['dtc']} | Status: 0x{item['status']}")
    except:
        print("No Response")
    
        
stack.stop()
bus.shutdown()
