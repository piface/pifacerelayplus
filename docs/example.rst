########
Examples
########

Basic usage
===========

::

    >>> import pifacerelayplus

    >>> pfr = pifacerelayplus.PiFaceRelayPlus(pifacerelayplus.RELAY)

    >>> pfr.relays[0].set_high() # turn on/set high the first Relay/LED
    >>> pfr.relays[1].turn_on()  # turn on/set high the second Relay/LED
    >>> pfr.relays[2].value = 1  # turn on/set high the third relay
    >>> pfr.relays[6].toggle()   # toggle seventh LED

    >>> pfr.relay_port.value = 0xAA  # set all the relays to be 0b10101010
    >>> pfr.relay_port.all_off()

    >>> pfr.motors[0].forward()  # drive the motor forward
    >>> pfr.motors[0].coast()  # stop driving the motor and let it coast
    >>> pfr.motors[0].reverse()  # drive the motor in reverse
    >>> pfr.motors[0].brake()  # force the motor to stop

    >>> pfr.x_port.value  # get the value of all of the X-port pins
    0
    >>> pfr.x_pins[0].value  # get the value of one X-port pin
    0

    >>> pfr.y_pins[0].value  # get the value of one Y-port pin (Relay Extra)

    >>> bin(pfr.x_port.value)  # fourth pin activated
    '0b1000'


Interrupts
==========

Instead of polling for input we can use the :class:`InputEventListener` to
register actions that we wish to be called on certain input events.

    >>> import pifacerelayplus
    >>> def toggle_relay0(event):
    ...     event.chip.relays[0].toggle()
    ...
    >>> pfr = pifacerelayplus.PiFaceRelayPlus(pifacerelayplus.RELAY)
    >>> listener = pifacerelayplus.InputEventListener(chip=pfr)
    >>> listener.register(0, pifacerelayplus.IODIR_FALLING_EDGE, toggle_relay0)
    >>> listener.activate()

When input 0 is pressed, relay 0 will be toggled. To stop the listener, call it's
``deactivate`` method:

    >>> listener.deactivate()

The :class:`Event` object has some interesting attributes. You can access them
like so::

    >>> import pifacerelayplus
    >>> pfr = pifacerelayplus.PiFaceRelayPlus(pifacerelayplus.RELAY)
    >>> listener = pifacerelayplus.InputEventListener(chip=pfr)
    >>> listener.register(0, pifacerelayplus.IODIR_RISING_EDGE, print)
    >>> listener.activate()

This would print out the event informaion whenever you unpress switch 0::

    interrupt_flag:    0b1
    interrupt_capture: 0b11111111
    pin_num:           0
    direction:         1
    chip:              <pifacerelayplus.core.PiFaceRelayPlus object at 0xb682dab0>
    timestamp:         1380893579.447889
