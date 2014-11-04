import time
from pifacerelayplus import (PiFaceRelayPlus, RELAY)


DIRECTION_INDEX = 0
GRIP_INDEX = 1
ELBOW_INDEX = 2
WRIST_INDEX = 3
SHOULDER_INDEX = 4
BASE_INDEX = 5
LIGHT_INDEX = 6


class RobotArm(object):
    """Robot Arm controlled by PiFace Relay Plus."""

    def __init__(self):
        self.pfrp = PiFaceRelayPlus(RELAY)

    def set_direction(self, direction):
        self.pfrp.relays[DIRECTION_INDEX].value = direction

    def set_relay_for_period(self, index, delay, direction):
        self.set_direction(direction)
        self.pfrp.relays[index].turn_on()
        time.sleep(delay)
        self.pfrp.relays[index].turn_off()

    def move_base(self, delay, direction=0):
        self.set_relay_for_period(BASE_INDEX, delay, direction)

    def move_shoulder(self, delay, direction=0):
        self.set_relay_for_period(SHOULDER_INDEX, delay, direction)

    def move_elbow(self, delay, direction=0):
        self.set_relay_for_period(ELBOW_INDEX, delay, direction)

    def move_wrist(self, delay, direction=0):
        self.set_relay_for_period(WRIST_INDEX, delay, direction)

    def move_grip(self, delay, direction=0):
        self.set_relay_for_period(GRIP_INDEX, delay, direction)

    def set_light(self, state):
        self.set_direction(0)
        self.pfrp.relays[LIGHT_INDEX].value = state
