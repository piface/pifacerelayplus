#!/usr/bin/env python3
import os
import sys
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parentdir)
import time
import pifacerelayplus


if __name__ == '__main__':
    pf = pifacerelayplus.PiFaceRelayPlus(pifacerelayplus.RELAY)
    while True:
        pf.relay_port.value = 0xaa
        time.sleep(0.25)
        pf.relay_port.value = 0x55
        time.sleep(0.25)
