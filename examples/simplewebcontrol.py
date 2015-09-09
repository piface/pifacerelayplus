"""
simplewebcontrol.py
Controls PiFace Relay Plus through a web browser. Returns the status of the
input port and the output port in a JSON string. Set the output with GET
variables.

Copyright (C) 2013 Thomas Preston <thomas.preston@openlx.org.uk>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import sys
import argparse
import subprocess
import http.server
import urllib.parse
import pifacerelayplus


JSON_FORMAT = "{{'relay_port': {relay_port}, 'x_port': {x_port}}}"
DEFAULT_PORT = 8000
RELAY_PORT_SET_STRING = "relay_port"
GET_IP_CMD = "hostname -I"


class PiFaceRelayPlusWebHandler(http.server.BaseHTTPRequestHandler):
    """Handles PiFace Relay Plus web control requests"""
    def do_GET(self):
        x_port_value = self.pfrp.x_port.value
        relay_port_value = self.pfrp.relay_port.value

        # parse the query string
        qs = urllib.parse.urlparse(self.path).query
        query_components = urllib.parse.parse_qs(qs)

        # set the output
        if RELAY_PORT_SET_STRING in query_components:
            new_relay_port_value = query_components[RELAY_PORT_SET_STRING][0]
            relay_port_value = self.set_relay_port(new_relay_port_value)

        # reply with JSON
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(bytes(JSON_FORMAT.format(
            x_port=x_port_value,
            relay_port=relay_port_value,
        ), 'UTF-8'))

    def set_relay_port(self, new_value):
        """Sets the relay port value to new_value."""
        print("Setting relay port port to {}.".format(new_value))
        port_value = self.pfrp.relay_port.value
        try:
            port_value = int(new_value)  # dec
        except ValueError:
            port_value = int(new_value, 16)  # hex
        finally:
            self.pfrp.relay_port.value = port_value
            return port_value  # returns actual port value


def get_my_ip():
    """Returns this computers IP address as a string."""
    ip = subprocess.check_output(GET_IP_CMD, shell=True).decode('utf-8')[:-1]
    return ip.strip()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port',
                        help='Port to use.',
                        default=DEFAULT_PORT)
    parser.add_argument('-nib', '--no_init_board',
                        dest='init_board',
                        action='store_false',
                        help="Do not initialise the board.")
    args = parser.parse_args()

    # set up PiFace Relay Plus
    PiFaceRelayPlusWebHandler.pfrp = pifacerelayplus.PiFaceRelayPlus(
        init_board=args.init_board)

    print("Starting simple PiFace web control at:\n\n"
          "\thttp://{addr}:{port}\n\n"
          "Change the relay_port with:\n\n"
          "\thttp://{addr}:{port}?relay_port=0xAA\n"
          .format(addr=get_my_ip(), port=args.port))

    # run the server
    server_address = ('', int(args.port))
    try:
        httpd = http.server.HTTPServer(server_address,
                                       PiFaceRelayPlusWebHandler)
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('^C received, shutting down server')
        httpd.socket.close()
