from time import sleep
import pifacerelayplus


DELAY = 1.0  # seconds


if __name__ == "__main__":
    pfr = pifacerelayplus.PiFaceRelayPlus(pifacerelayplus.RELAY)
    while True:
        pfr.relays[0].toggle()
        sleep(DELAY)
