#!/usr/bin/env python3
import time
import unittest
import pifacerelayplus


class TestPiFaceRelayPlusEMC(unittest.TestCase):
    def setUp(self):
        self.pfrp = pifacerelayplus.PiFaceRelayPlus(pifacerelayplus.MOTOR)

    def test_interrupt(self):
        while True:
            print("forward")
            self.pfrp.motors[0].forward()
            time.sleep(1)

            print("coast")
            self.pfrp.motors[0].coast()
            time.sleep(1)

            print("reverse")
            self.pfrp.motors[0].reverse()
            time.sleep(1)

            print("brake")
            self.pfrp.motors[0].brake()
            time.sleep(1)


if __name__ == "__main__":
    unittest.main()
