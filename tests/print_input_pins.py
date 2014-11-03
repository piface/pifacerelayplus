import os
import sys
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parentdir)
import pifacerelayplus


if __name__ == '__main__':
    pfrp = pifacerelayplus.PiFaceRelayPlus(pifacerelayplus.RELAY)
    print("Relay Plus input values:")
    for i in range(8):
        print("{} - {}".format(i, pfrp.input_port[i].value))
