import pifacecommon.interrupts
import pifacecommon.mcp23s17


# /dev/spidev<bus>.<chipselect>
DEFAULT_SPI_BUS = 0
DEFAULT_SPI_CHIP_SELECT = 0

# Datasheet says coast is 0, 0 and bake is 1, 1. I think it's wrong.
# (pin_num1, pin_num2)
MOTOR_COAST_BITS = (1, 1)  # Z, Z
MOTOR_REVERSE_BITS = (0, 1)  # L, H
MOTOR_FORWARD_BITS = (1, 0)  # H, L
MOTOR_BRAKE_BITS = (0, 0)  # L, L

# Plus boards
RELAY, MOTOR, DIGITAL = range(3)


class NoPiFaceRelayPlusDetectedError(Exception):
    pass


class Motor(object):
    """A motor driver attached to a PiFace Relay Plus. Uses DRV8835."""
    def __init__(self, pin1, pin2):
        self.pin1 = pin1
        self.pin2 = pin2
        self.brake()

    def coast(self):
        """Sets the motor so that it is coasting."""
        self.pin1.value = MOTOR_COAST_BITS[0]
        self.pin2.value = MOTOR_COAST_BITS[1]

    def reverse(self):
        """Sets the motor so that it is moving in reverse."""
        self.pin1.value = MOTOR_REVERSE_BITS[0]
        self.pin2.value = MOTOR_REVERSE_BITS[1]

    def forward(self):
        """Sets the motor so that it is moving forward."""
        self.pin1.value = MOTOR_FORWARD_BITS[0]
        self.pin2.value = MOTOR_FORWARD_BITS[1]

    def brake(self):
        """Stop the motor."""
        self.pin1.value = MOTOR_BRAKE_BITS[0]
        self.pin2.value = MOTOR_BRAKE_BITS[1]


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
                 plus_board,
                 hardware_addr=0,
                 bus=DEFAULT_SPI_BUS,
                 chip_select=DEFAULT_SPI_CHIP_SELECT,
                 init_board=True):
        super(PiFaceRelayPlus, self).__init__(hardware_addr, bus, chip_select)

        # input_pins are always the upper nibble of GPIOB
        self.input_pins = [pifacecommon.mcp23s17.MCP23S17RegisterBitNeg(
            i, pifacecommon.mcp23s17.GPIOB, self)
            for i in range(4, 8)]
        self.input_port = pifacecommon.mcp23s17.MCP23S17RegisterNibbleNeg(
            pifacecommon.mcp23s17.UPPER_NIBBLE,
            pifacecommon.mcp23s17.GPIOB,
            self)

        # Relays are always lower nibble of GPIOA, order is reversed
        self.relays = list(reversed([pifacecommon.mcp23s17.MCP23S17RegisterBit(
            i, pifacecommon.mcp23s17.GPIOA, self)
            for i in range(0, 4)]))

        if plus_board == RELAY:
            # append 4 relays
            self.relays.append = [pifacecommon.mcp23s17.MCP23S17RegisterBit(
                i, pifacecommon.mcp23s17.GPIOA, self)
                for i in range(4, 8)]

        elif plus_board == MOTOR:
            self.motors = [
                Motor(
                    pin1=pifacecommon.mcp23s17.MCP23S17RegisterBitNeg(
                        3, pifacecommon.mcp23s17.GPIOB, self),
                    pin2=pifacecommon.mcp23s17.MCP23S17RegisterBitNeg(
                        2, pifacecommon.mcp23s17.GPIOB, self)),
                Motor(
                    pin1=pifacecommon.mcp23s17.MCP23S17RegisterBitNeg(
                        1, pifacecommon.mcp23s17.GPIOB, self),
                    pin2=pifacecommon.mcp23s17.MCP23S17RegisterBitNeg(
                        0, pifacecommon.mcp23s17.GPIOB, self)),
                Motor(
                    pin1=pifacecommon.mcp23s17.MCP23S17RegisterBit(
                        4, pifacecommon.mcp23s17.GPIOA, self),
                    pin2=pifacecommon.mcp23s17.MCP23S17RegisterBit(
                        5, pifacecommon.mcp23s17.GPIOA, self)),
                Motor(
                    pin1=pifacecommon.mcp23s17.MCP23S17RegisterBit(
                        6, pifacecommon.mcp23s17.GPIOA, self),
                    pin2=pifacecommon.mcp23s17.MCP23S17RegisterBit(
                        7, pifacecommon.mcp23s17.GPIOA, self)),
            ]

        elif plus_board == DIGITAL:
            pass

        if init_board:
            self.init_board()

    def __del__(self):
        self.disable_interrupts()
        super(PiFaceRelayPlus, self).__del__()

    def enable_interrupts(self):
        self.gpintenb.value = 0xF0
        self.gpio_interrupts_enable()

    def disable_interrupts(self):
        self.gpintenb.value = 0x00
        self.gpio_interrupts_disable()

    def init_board(self):
        ioconfig = (
            pifacecommon.mcp23s17.BANK_OFF |
            pifacecommon.mcp23s17.INT_MIRROR_OFF |
            pifacecommon.mcp23s17.SEQOP_OFF |
            pifacecommon.mcp23s17.DISSLW_OFF |
            pifacecommon.mcp23s17.HAEN_ON |
            pifacecommon.mcp23s17.ODR_OFF |
            pifacecommon.mcp23s17.INTPOL_LOW
        )
        self.iocon.value = ioconfig
        if self.iocon.value != ioconfig:
            raise NoPiFaceRelayPlusDetectedError(
                "No PiFace Relay Plus board detected (hardware_addr={h}, "
                "bus={b}, chip_select={c}).".format(
                    h=self.hardware_addr, b=self.bus, c=self.chip_select))
        else:
            # finish configuring the board
            self.gpioa.value = 0
            self.iodira.value = 0  # GPIOA as outputs
            self.iodirb.value = 0xf0  # GPIOB lower nibble as outputs
            self.gppub.value = 0xf0
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
        super(InputEventListener, self).__init__(
            pifacecommon.mcp23s17.GPIOB, chip)
