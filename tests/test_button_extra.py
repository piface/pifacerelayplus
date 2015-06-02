import time
import unittest
import pifacerelayplus


class TestButtonExtraBoard(unittest.TestCase):

    def setUp(self):
        self.pfrp = pifacerelayplus.PiFaceRelayPlus(
            plus_board=pifacerelayplus.BUTTON)

    # def test_turn_on_relays(self):
    #     time.sleep(1)
    #     for i in range(4):
    #         print("turning on relay {}".format(i))
    #         self.pfrp.relays[i].turn_on()
    #         time.sleep(1)

    def test_turn_on_leds(self):
        # for i in range(4):
        #     self.assertEqual(self.pfrp.leds[i].value, 0)

        # for i in range(4):
        #     self.pfrp.leds[i].turn_on()
        #     self.assertEqual(self.pfrp.leds[i].value, 1)

        for i in range(4):
            self.pfrp.leds[i].turn_on()
            self.pfrp.relays[i].turn_on()
        # self.pfrp.leds[1].turn_on()
        # self.pfrp.leds[2].turn_on()
        # self.pfrp.leds[3].turn_on()

    def test_button_extra(self):
        for i in range(4):
            print("Button {} is: {}".format(i, self.pfrp.buttons[i].value))


if __name__ == "__main__":
    unittest.main()
