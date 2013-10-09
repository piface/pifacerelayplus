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
    >>> pfr.input_pins[3].value  # check the logical status of switch 3
    0

    >>> pfr.relays.value = 0xAA  # set all the relays to be 0b10101010
    >>> pfr.relays.all_off()

    >>> pfr.input_pins.value     # get the logical value of all the input pins
    0

    >>> bin(pfr.input_port.value)  # fourth switch pressed (logical input port)
    '0b1000'

    >>> bin(pfr.gpiob.value)  # fourth switch pressed (physical input port)
    '0b11110111'

.. note: Values are active low on GPIO Port B. This is hidden in software
   unless you inspect the GPIOB register.


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
