Simple Web Control
==================

You can control PiFace Relay Plus from a web browser (or any network enabled
device) using the `simplewebcontrol.py` tool.

You can start the tool by running the following command on your Raspberry Pi::

    $ python3 /usr/share/doc/python3-pifacerelayplus/examples/simplewebcontrol.py

This will start a simple web server on port 8000 which you can access using
a web browser.

Type the following into the address bar of a browser on any machine in the
local network::

    http://192.168.1.3:8000

.. note:: Relace ``192.168.1.3`` with the IP address of your Raspberry Pi.

It will return a `JSON object <http://www.json.org/>`_ describing the current
state of PiFace Relay Plus::

    {"relay_port": 0, "x_port": 0}


Controlling Relays
------------------
You can set the relay port (on board 0) using the URL::

    http://192.168.1.61:8000/?b0_relay_port=0xaa


Changing Port
-------------
You can specify which port you would like ``simplewebcontrol.py`` to use with::

    $ python3 /usr/share/doc/python3-pifacedigitalio/examples/simplewebcontrol.py --port 12345


Board Initialisation
--------------------
The web controller automatically initialises the board. If this does not suit
your application then you can try the `no_init_board` flag::

    $ python3 /usr/share/doc/python3-pifacedigitalio/examples/simplewebcontrol.py --no_init_board


Multiple Boards
---------------
You can specify multiple boards with the `num-boards` flag::

    $ python3 /usr/share/doc/python3-pifacedigitalio/examples/simplewebcontrol.py --num-boards=3

Control them like so::

    http://192.168.1.61:8000/?b0_relay_port=0xaa&b1_relay_port=0xaa&b2_relay_port=0xaa


Masks
-----
Instead of setting the relay port values you can send in bit-masks. This can
be useful if you only want to set individual relays without having to
read/write::

    http://192.168.1.61:8000/?b0_relay_port__and=0x0f
    http://192.168.1.61:8000/?b0_relay_port__or=0x11
