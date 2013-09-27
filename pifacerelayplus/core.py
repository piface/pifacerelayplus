import subprocess
import time
import pifacecommon

# /dev/spidev<bus>.<chipselect>
DEFAULT_SPI_BUS = 0
DEFAULT_SPI_CHIP_SELECT = 0

# some easier to remember/read values
# OUTPUT_PORT = pifacecommon.core.GPIOA
# INPUT_PORT = pifacecommon.core.GPIOB
INPUT_PULLUP = pifacecommon.core.GPPUB

MOTOR_FORWARD_BITS = (0, 0)  # (pin_num1, pin_num2)
MOTOR_BACK_BITS = (0, 1)
MOTOR_STOP_BITS = (1, 0)
MOTOR_COAST_BITS = (1, 1)


class InitError(Exception):
    pass


class NoPiFaceRelayPlusDetectedError(Exception):
    pass


class Relay(pifacecommon.core.DigitalOutputItem):
    """A relay on a PiFace Digital board. Inherits
    :class:`pifacecommon.core.DigitalOutputItem`.
    """
    def __init__(self, relay_num, board_num=0):
        if relay_num < 0 or relay_num > 8:
            raise pifacecommon.core.RangeError(
                "Specified relay index (%d) out of range." % relay_num)
        else:
            super(Relay, self).__init__(relay_num, pifacecommon.core.GPIOA,
                                        board_num, toggle_mask=0)
            # Toggle mask is supposed to be 1 according to schematic


class Motor(object):
    """A motor attached to a PiFace Relay Plus."""
    def __init__(self, pin_num1, pin_num2, port, board_num=0, toggle_mask=0):
        self.pin_num1 = pin_num1
        self.pin_num2 = pin_num2
        self.port = port
        self.board_num = board_num
        self.toggle_mask = toggle_mask

    @property
    def handler(self):
        """The module that handles this port (can be useful for
        emulator/testing).
        """
        return sys.modules[__name__]

    def forward(self):
        """Sets the motor so that it is moving forward."""
        self.set_pins(MOTOR_FORWARD_BITS[0], MOTOR_FORWARD_BITS[1])

    def back(self):
        """Sets the motor so that it is moving backwards."""
        self.set_pins(MOTOR_BACK_BITS[0], MOTOR_BACK_BITS[1])

    def stop(self):
        """Stop the motor."""
        self.set_pins(MOTOR_STOP_BITS[0], MOTOR_STOP_BITS[1])

    def coast(self):
        """Sets the motor so that it is coasting."""
        self.set_pins(MOTOR_COAST_BITS[0], MOTOR_COAST_BITS[1])

    def set_pins(self, pin1, pin2):
        port_value = self.handler.read(self.port, self.board_num)
        # clear the bits owned by this motor
        mask = 0xFF ^ (0 << self.pin_num1) ^ (0 << self.pin_num2)
        port_value &= mask
        # set the bits for this motor
        port_value ^= \
            ((self.toggle_mask ^ pin1) << self.pin_num1) ^ \
            ((self.toggle_mask ^ pin2) << self.pin_num2)
        self.handler.write(port_value, self.port, self.board_num)


class PiFaceRelayPlus(object):
    """A PiFace Relay Plus board.

    :attribute: board_num -- The board number.
    :attribute: input_port1 -- See :class:`pifacecommon.core.DigitalInputPort`.
    :attribute: input_pins -- list containing
        :class:`pifacecommon.core.DigitalInputPin`.
    :attribute: relays -- list containing :class:`Relay`.
    :attribute: motors -- list containing :class:`Motor`.

    Example:

    >>> prp = pifacerelayplus.PiFaceRelayPlus()
    >>> prp.input_port.value
    0
    >>> prp.relays[3].turn_on()
    >>> prp.motor[2].forward()
    """
    def __init__(self, board_num=0):
        self.board_num = board_num

        self.input_port = pifacecommon.core.DigitalInputPort(
            port=pifacecommon.core.GPIOB,
            board_num=self.board_num,
            bit_mask=0x0F,
            toggle_mask=0x00)
        self.input_pins = [
            pifacecommon.core.DigitalInputItem(
                pin_num=i,
                port=pifacecommon.core.GPIOB,
                board_num=self.board_num,
                toggle_mask=0)
            for i in range(4, 8)
        ]

        #self.relays = [Relay(i, board_num) for i in range(4)]

        #self.relays_plus = [Relay(i, board_num) for i in range(4, 8)]
        # don't seperate (let the user access relay 5 even if motor is on)

        # make these dependant on init
        # init(motors=True)
        # init(relays=True)
        # init(some_other_addon=True)
        self.relays = [Relay(i, board_num) for i in range(8)]

        self.motors = [
            Motor(pin_num1=4,
                  pin_num2=5,
                  port=pifacecommon.core.GPIOA,
                  board_num=self.board_num,
                  toggle_mask=1),
            Motor(pin_num1=6,
                  pin_num2=7,
                  port=pifacecommon.core.GPIOA,
                  board_num=self.board_num,
                  toggle_mask=1),
            Motor(pin_num1=3,
                  pin_num2=2,
                  port=pifacecommon.core.GPIOB,
                  board_num=self.board_num,
                  toggle_mask=0),
            Motor(pin_num1=1,
                  pin_num2=0,
                  port=pifacecommon.core.GPIOB,
                  board_num=self.board_num,
                  toggle_mask=0)
        ]


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
    def __init__(self, board_num=0):
        super(InputEventListener, self).__init__(INPUT_PORT, board_num)


def init(init_board=True,
         bus=DEFAULT_SPI_BUS,
         chip_select=DEFAULT_SPI_CHIP_SELECT):
    """Initialises all PiFace Relay Plus boards.

    :param init_board: Initialise each board (default: True)
    :type init_board: boolean
    :param bus: SPI bus /dev/spidev<bus>.<chipselect> (default: {bus})
    :type bus: int
    :param chip_select: SPI bus /dev/spidev<bus>.<chipselect> (default: {chip})
    :type chip_select: int
    :raises: :class:`NoPiFaceRelayPlusDetectedError`
    """.format(bus=DEFAULT_SPI_BUS, chip=DEFAULT_SPI_CHIP_SELECT)

    pifacecommon.core.init(bus, chip_select)

    if init_board:
         # set up each board
        ioconfig = (
            pifacecommon.core.BANK_OFF |
            pifacecommon.core.INT_MIRROR_OFF |
            pifacecommon.core.SEQOP_OFF |
            pifacecommon.core.DISSLW_OFF |
            pifacecommon.core.HAEN_ON |
            pifacecommon.core.ODR_OFF |
            pifacecommon.core.INTPOL_LOW
        )

        pfrp_detected = False

        for board_index in range(pifacecommon.core.MAX_BOARDS):
            pifacecommon.core.write(
                ioconfig, pifacecommon.core.IOCON, board_index)

            if not pfrp_detected:
                pfioconf = pifacecommon.core.read(
                    pifacecommon.core.IOCON, board_index)
                if pfioconf == ioconfig:
                    pfrp_detected = True

            # clear port A and set it as an output
            pifacecommon.core.write(0, pifacecommon.core.GPIOA, board_index)
            pifacecommon.core.write(0, pifacecommon.core.IODIRA, board_index)

            # set port B upper nibble as input, lower nibble as input
            pifacecommon.core.write(
                0x0f, pifacecommon.core.IODIRB, board_index)

            ################# !!!!!!!!!!!!!!!!!!!!!! #################
            # turn pullups on, ask Andrew about this
            pifacecommon.core.write(0xff, pifacecommon.core.GPPUB, board_index)
            ################# !!!!!!!!!!!!!!!!!!!!!! #################

        if not pfrp_detected:
            raise NoPiFaceRelayPlusDetectedError(
                "No PiFace Relay Plus board detected!")
        else:
            pifacecommon.interrupts.enable_interrupts(
                port=pifacecommon.core.GPIOB, pin_map=0x0f)


def deinit():
    """Deinitialises all PiFace Relay Plus boards."""
    pifacecommon.interrupts.disable_interrupts(pifacecommon.core.GPIOB)
    pifacecommon.core.deinit()


# wrapper functions for backwards compatibility
# def digital_read(pin_num, board_num=0):
#     """Returns the value of the input pin specified.

#     .. note:: This function is for familiarality with users of other types of
#        IO board. Consider using :func:`pifacecommon.core.read_bit` instead.

#        >>> pifacecommon.core.read_bit(pin_num, INPUT_PORT, board_num)

#     :param pin_num: The pin number to read.
#     :type pin_num: int
#     :param board_num: The board to read from (default: 0)
#     :type board_num: int
#     :returns: int -- value of the pin
#     """
#     return pifacecommon.core.read_bit(pin_num, INPUT_PORT, board_num) ^ 1


# def digital_write(pin_num, value, board_num=0):
#     """Writes the value to the input pin specified.

#     .. note:: This function is for familiarality with users of other types of
#        IO board. Consider using :func:`pifacecommon.core.write_bit` instead.

#        >>> pifacecommon.core.write_bit(
#        ...     value, pin_num, OUTPUT_PORT, board_num)

#     :param pin_num: The pin number to write to.
#     :type pin_num: int
#     :param value: The value to write.
#     :type value: int
#     :param board_num: The board to read from (default: 0)
#     :type board_num: int
#     """
#     pifacecommon.core.write_bit(value, pin_num, OUTPUT_PORT, board_num)


# def digital_read_pullup(pin_num, board_num=0):
#     """Returns the value of the input pullup specified.

#     .. note:: This function is for familiarality with users of other types of
#        IO board. Consider using :func:`pifacecommon.core.read_bit` instead.

#        >>> pifacecommon.core.read_bit(pin_num, INPUT_PULLUP, board_num)

#     :param pin_num: The pin number to read.
#     :type pin_num: int
#     :param board_num: The board to read from (default: 0)
#     :type board_num: int
#     :returns: int -- value of the pin
#     """
#     return pifacecommon.core.read_bit(pin_num, INPUT_PULLUP, board_num)


# def digital_write_pullup(pin_num, value, board_num=0):
#     """Writes the value to the input pullup specified.

#     .. note:: This function is for familiarality with users of other types of
#        IO board. Consider using :func:`pifacecommon.core.write_bit` instead.

#        >>> pifacecommon.core.write_bit(
#        ...     value, pin_num, INPUT_PULLUP, board_num)

#     :param pin_num: The pin number to write to.
#     :type pin_num: int
#     :param value: The value to write.
#     :type value: int
#     :param board_num: The board to read from (default: 0)
#     :type board_num: int
#     """
#     pifacecommon.core.write_bit(value, pin_num, INPUT_PULLUP, board_num)
