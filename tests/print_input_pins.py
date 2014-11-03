import os
import sys
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parentdir)
import pifacerelayplus


if __name__ == '__main__':
    pfrp = pifacerelayplus.PiFaceRelayPlus(pifacerelayplus.RELAY)
    print("Relay Plus x-input values:")
    for i in range(4):
        print("{} - {}".format(i, pfrp.x_pins[i].value))

    print("Relay Plus y-input values:")
    for i in range(4):
        print("{} - {}".format(i, pfrp.y_pins[i].value))
