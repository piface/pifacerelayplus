import pifacecommon.interrupts
import pifacecommon.mcp23s17
import time


# /dev/spidev<bus>.<chipselect>
DEFAULT_SPI_BUS = 0
DEFAULT_SPI_CHIP_SELECT = 0

# Datasheet says coast is 0, 0 and bake is 1, 1. I think it's wrong.
# (pin_num1, pin_num2)
MOTOR_DC_COAST_BITS = (1, 1)  # Z, Z
MOTOR_DC_REVERSE_BITS = (0, 1)  # L, H
MOTOR_DC_FORWARD_BITS = (1, 0)  # H, L
MOTOR_DC_BRAKE_BITS = (0, 0)  # L, L

# Plus boards
# Motor board IC datasheet: http://www.ti.com/lit/ds/symlink/drv8835.pdf
# RELAY, MOTOR_DC, MOTOR_STEPPER = range(3)
RELAY, MOTOR_DC, BUTTON = range(3)

DEFAULT_GPIOA_CONF = {'value': 0, 'direction': 0, 'pullup': 0}
DEFAULT_GPIOB_CONF = {'value': 0, 'direction': 0xff, 'pullup': 0xff}

# You cannot make two motor controls within this time window (feel free
# to adjust this for your power supply)
MOTOR_CONTROL_WINDOW = 0.150 # 150ms
_motor_last_control_time = 0


class NoPiFaceRelayPlusDetectedError(Exception):
    pass


class MotorForwardReverseError(Exception):
    """Too much current flows when instantly reversing motor direction."""

    def __init__(self, state_into, state_from):
        super().__init__(
            "Cannot move into state `{}` from state `{}`. Must call "
            "`brake` or `coast` first.".format(state_into, state_from))


class MotorTooSoonError(Exception):
    """This exception is thrown when more than one motor is turned on
    within a small time window as it will draw too much current and
    reset the Raspberry Pi.
    """
    pass


class MotorDC(object):
    """A motor driver attached to a PiFace Relay Plus. Uses DRV8835."""

    def __init__(self, pin1, pin2):
        self.pin1 = pin1
        self.pin2 = pin2
        self._current_state = 'brake'

    def _check_time(self):
        global _motor_last_control_time
        if time.time() > _motor_last_control_time + MOTOR_CONTROL_WINDOW:
            # past the window - we can control the motor
            _motor_last_control_time = time.time()
        else:
            raise MotorTooSoonError()

    def coast(self):
        """Sets the motor so that it is coasting."""
        self._check_time()
        self.pin1.value = MOTOR_DC_COAST_BITS[0]
        self.pin2.value = MOTOR_DC_COAST_BITS[1]
        self._current_state = 'coast'

    def reverse(self):
        """Sets the motor so that it is moving in reverse."""
        if self._current_state == 'forward':
            raise MotorForwardReverseError('reverse', self._current_state)
        else:
            self._check_time()
            self.pin1.value = MOTOR_DC_REVERSE_BITS[0]
            self.pin2.value = MOTOR_DC_REVERSE_BITS[1]
            self._current_state = 'reverse'

    def forward(self):
        """Sets the motor so that it is moving forward."""
        if self._current_state == 'reverse':
            raise MotorForwardReverseError('forward', self._current_state)
        else:
            self._check_time()
            self.pin1.value = MOTOR_DC_FORWARD_BITS[0]
            self.pin2.value = MOTOR_DC_FORWARD_BITS[1]
            self._current_state = 'forward'

    def brake(self):
        """Stop the motor."""
        self._check_time()
        self.pin1.value = MOTOR_DC_BRAKE_BITS[0]
        self.pin2.value = MOTOR_DC_BRAKE_BITS[1]
        self._current_state = 'brake'


# class MotorStepper(object):
#     """A stepper motor driver attached to a PiFace Relay Plus. Uses DRV8835."""

#     step_states = (0xa, 0x2, 0x6, 0x4, 0x5, 0x1, 0x9, 0x8)

#     def __init__(self, index, chip):
#         self.chip = chip
#         if index == 0:
#             self.set_stepper = self._set_stepper0
#         else:
#             self.set_stepper = self._set_stepper1

#     def _set_stepper0(self, value):
#         """GPIOB lower nibble, polarity reversed."""
#         gpiob = self.chip.gpiob.value & 0xf0
#         self.chip.gpiob.value = gpiob | ((value & 0xf) ^ 0xf)

#     def _set_stepper1(self, value):
#         """GPIOA upper nibble, normal polarity."""
#         gpioa = self.chip.gpioa.value & 0x0f
#         self.chip.gpioa.value = gpioa | ((value & 0xf) << 4)

#     def _send_steps(self, step_states, steps, step_delay):
#         for i in range(steps):
#             step_index = i % len(step_states)
#             self.set_stepper(step_states[step_index])
#             time.sleep(step_delay)

#     def coast(self):
#         """Sets the motor so that it is coasting."""
#         self.set_stepper(0x0)

#     def reverse(self, steps, step_delay):
#         """Sets the motor so that it is moving in reverse."""
#         self._send_steps(reversed(self.step_states), steps, step_delay)

#     def forward(self, steps, step_delay):
#         """Sets the motor so that it is moving forward."""
#         self._send_steps(self.step_states, steps, step_delay)

#     def brake(self):
#         """Stop the motor."""
#         self.set_stepper(0xf)


class PiFaceRelayPlus(pifacecommon.mcp23s17.MCP23S17,
                      pifacecommon.interrupts.GPIOInterruptDevice):
    """A PiFace Relay Plus board.

    Example:

    >>> pfrp = pifacerelayplus.PiFaceRelayPlus(pifacerelayplus.MOTOR)
    >>> pfrp.inputs[2].value
    0
    >>> pfrp.relays[3].turn_on()
    >>> pfrp.motor[2].forward()
    """

    def __init__(self,
                 plus_board=None,
                 hardware_addr=0,
                 bus=DEFAULT_SPI_BUS,
                 chip_select=DEFAULT_SPI_CHIP_SELECT,
                 init_board=True):
        super(PiFaceRelayPlus, self).__init__(hardware_addr, bus, chip_select)

        pcmcp = pifacecommon.mcp23s17

        # input_pins are always the upper nibble of GPIOB
        self.x_pins = [pcmcp.MCP23S17RegisterBitNeg(i, pcmcp.GPIOB, self)
                           for i in range(4, 8)]
        self.x_port = pcmcp.MCP23S17RegisterNibbleNeg(pcmcp.UPPER_NIBBLE,
                                                      pcmcp.GPIOB,
                                                      self)

        # self.relay_port = pcmcp.MCP23S17Register(pcmcp.GPIOA, self)
        self.relay_port = pcmcp.MCP23S17RegisterNibble(pcmcp.LOWER_NIBBLE,
                                                       pcmcp.GPIOA,
                                                       self)


        # Relays are always lower nibble of GPIOA, order is reversed
        self.relays = list(reversed([pcmcp.MCP23S17RegisterBit(i,
                                                               pcmcp.GPIOA,
                                                               self)
                                     for i in range(0, 4)]))

        if plus_board == RELAY:
            # append 4 relays
            self.relays.extend([pcmcp.MCP23S17RegisterBit(i, pcmcp.GPIOA, self)
                                for i in range(4, 8)])

            self.relay_port = pcmcp.MCP23S17Register(pcmcp.GPIOA, self)

            # add the y port
            self.y_pins = [pcmcp.MCP23S17RegisterBitNeg(i, pcmcp.GPIOB, self)
                           for i in range(4)]
            self.y_port = pcmcp.MCP23S17RegisterNibbleNeg(pcmcp.LOWER_NIBBLE,
                                                          pcmcp.GPIOB,
                                                          self)
            gpioa_conf = {'value': 0, 'direction': 0, 'pullup': 0}
            gpiob_conf = {'value': 0, 'direction': 0xff, 'pullup': 0xff}

        elif plus_board == MOTOR_DC:
            self.motors = [
                MotorDC(
                    pin1=pcmcp.MCP23S17RegisterBitNeg(3, pcmcp.GPIOB, self),
                    pin2=pcmcp.MCP23S17RegisterBitNeg(2, pcmcp.GPIOB, self)),
                MotorDC(
                    pin1=pcmcp.MCP23S17RegisterBitNeg(1, pcmcp.GPIOB, self),
                    pin2=pcmcp.MCP23S17RegisterBitNeg(0, pcmcp.GPIOB, self)),
                MotorDC(pin1=pcmcp.MCP23S17RegisterBit(4, pcmcp.GPIOA, self),
                        pin2=pcmcp.MCP23S17RegisterBit(5, pcmcp.GPIOA, self)),
                MotorDC(pin1=pcmcp.MCP23S17RegisterBit(6, pcmcp.GPIOA, self),
                        pin2=pcmcp.MCP23S17RegisterBit(7, pcmcp.GPIOA, self)),
            ]
            gpioa_conf = {'value': 0, 'direction': 0, 'pullup': 0}
            gpiob_conf = {'value': 0, 'direction': 0, 'pullup': 0}

        # elif plus_board == MOTOR_STEPPER:
        #     self.motors = [MotorStepper(i, self) for i in range(2)]
        #     gpioa_conf = {'value': 0, 'direction': 0, 'pullup': 0}
        #     gpiob_conf = {'value': 0, 'direction': 0, 'pullup': 0}

        elif plus_board == BUTTON:
            # append 4 LEDs
            self.leds = [pcmcp.MCP23S17RegisterBit(i, pcmcp.GPIOA, self)
                         for i in range(4, 8)]
            self.led_port = pcmcp.MCP23S17RegisterNibble(pcmcp.UPPER_NIBBLE,
                                                         pcmcp.GPIOA,
                                                         self)
            # add the buttons
            self.buttons = [pcmcp.MCP23S17RegisterBitNeg(i, pcmcp.GPIOB, self)
                            for i in range(4)]
            self.button_port = pcmcp.MCP23S17RegisterNibbleNeg(pcmcp.LOWER_NIBBLE,
                                                               pcmcp.GPIOB,
                                                               self)
            gpioa_conf = {'value': 0, 'direction': 0, 'pullup': 0}
            gpiob_conf = {'value': 0, 'direction': 0xff, 'pullup': 0xff}

        else:
            gpioa_conf = DEFAULT_GPIOA_CONF
            gpiob_conf = DEFAULT_GPIOB_CONF

        if init_board:
            self.init_board(gpioa_conf, gpiob_conf)

    def enable_interrupts(self):
        """Enables interrupts."""
        self.gpintenb.value = 0xF0
        self.gpio_interrupts_enable()

    def disable_interrupts(self):
        """Disables interrupts."""
        self.gpintenb.value = 0x00
        self.gpio_interrupts_disable()

    def init_board(self,
                   gpioa_conf=DEFAULT_GPIOA_CONF,
                   gpiob_conf=DEFAULT_GPIOB_CONF):
        """Initialise the board with given GPIO configurations."""
        ioconfig = (pifacecommon.mcp23s17.BANK_OFF |
                    pifacecommon.mcp23s17.INT_MIRROR_OFF |
                    pifacecommon.mcp23s17.SEQOP_OFF |
                    pifacecommon.mcp23s17.DISSLW_OFF |
                    pifacecommon.mcp23s17.HAEN_ON |
                    pifacecommon.mcp23s17.ODR_OFF |
                    pifacecommon.mcp23s17.INTPOL_LOW)
        self.iocon.value = ioconfig
        if self.iocon.value != ioconfig:
            raise NoPiFaceRelayPlusDetectedError(
                "No PiFace Relay Plus board detected (hardware_addr={h}, "
                "bus={b}, chip_select={c}).".format(h=self.hardware_addr,
                                                    b=self.bus,
                                                    c=self.chip_select))
        else:
            # finish configuring the board
            # GPIOA
            self.gpioa.value = gpioa_conf['value']
            self.iodira.value = gpioa_conf['direction']
            self.gppua.value = gpioa_conf['pullup']
            # GPIOB
            self.gpiob.value = gpiob_conf['value']
            self.iodirb.value = gpiob_conf['direction']
            self.gppub.value = gpiob_conf['pullup']

            self.enable_interrupts()


class InputEventListener(pifacecommon.interrupts.PortEventListener):
    """Listens for events on the input port and calls the mapped callback
    functions.

    >>> def print_flag(event):
    ...     print(event.interrupt_flag)
    ...
    >>> listener = pifacerelayplus.InputEventListener()
    >>> listener.register(0, pifacerelayplus.IODIR_ON, print_flag)
    >>> listener.activate()
    """
    def __init__(self, chip):
        super(InputEventListener, self).__init__(pifacecommon.mcp23s17.GPIOB,
                                                 chip)
