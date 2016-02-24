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
import json
import argparse
import subprocess
import http.server
import urllib.parse
from pifacerelayplus import PiFaceRelayPlus, RELAY


DEFAULT_PORT = 8000
RELAY_PORT_SET = "b{board_index}_relay_port"
RELAY_PORT_AND = "b{board_index}_relay_port__and"
RELAY_PORT_OR = "b{board_index}_relay_port__or"
GET_IP_CMD = "hostname -I"


class PiFaceRelayPlusWebHandler(http.server.BaseHTTPRequestHandler):
    """Handles PiFace Relay Plus web control requests"""

    # List of PiFace Relay Plus boards
    pfrps = []

    def do_GET(self):
        statuses = []
        for i, board in enumerate(self.pfrps):
            # get the board status
            status = self.get_status(board)
            self.update_relay_port(board, i, status)
            statuses.append(status)

        # reply with JSON
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        # for access from other sources
        self.send_header("Access-Control-Allow-Origin", "*");
        self.send_header("Access-Control-Expose-Headers",
                         "Access-Control-Allow-Origin");
        self.send_header("Access-Control-Allow-Headers",
                         "Origin, X-Requested-With, Content-Type, Accept");
        self.end_headers()
        self.wfile.write(bytes(json.dumps(statuses), 'utf-8'))

    def get_status(self, board):
        return {"x_port": board.x_port.value,
                "relay_port": board.relay_port.value}

    def update_relay_port(self, board, index, status):
        # parse the query string
        qs = urllib.parse.urlparse(self.path).query
        qcomponents = urllib.parse.parse_qs(qs)
        # set the output
        key_set = RELAY_PORT_SET.format(board_index=index)
        key_and = RELAY_PORT_AND.format(board_index=index)
        key_or = RELAY_PORT_OR.format(board_index=index)
        # SET
        if key_set in qcomponents:
            value = self.parse_query_value(qcomponents[key_set][0])
            board.relay_port.value = value
            status['relay_port'] = value
        # AND
        elif key_and in qcomponents:
            mask = self.parse_query_value(qcomponents[key_and][0])
            value = board.relay_port.value & mask
            board.relay_port.value = value
            status['relay_port'] = value
        # OR
        elif key_or in qcomponents:
            mask = self.parse_query_value(qcomponents[key_or][0])
            value = board.relay_port.value | mask
            board.relay_port.value = value
            status['relay_port'] = value

    def parse_query_value(self, query_value):
        try:
            return int(query_value)  # dec
        except ValueError:
            return int(query_value, 16)  # hex


def get_my_ip():
    """Returns this computers IP address as a string."""
    output = subprocess.check_output(GET_IP_CMD, shell=True).decode('utf-8')
    ips = output.split(' ')
    return ips[0].strip()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port',
                        help='Port to use.',
                        default=DEFAULT_PORT)
    parser.add_argument('-nib', '--no_init_board',
                        dest='init_board',
                        action='store_false',
                        help="Do not initialise the board.")
    parser.add_argument('-n', '--num-boards',
                        help='Number of PiFace Relay Plus boards attached.',
                        default=1,
                        type=int)
    args = parser.parse_args()

    # set up a list of PiFace Relay Plus boards (with 'relay' plus-board)
    PiFaceRelayPlusWebHandler.pfrps =[]
    for hardware_addr in range(args.num_boards):
        try:
            pfrp = PiFaceRelayPlus(plus_board=RELAY,
                                   init_board=args.init_board,
                                   hardware_addr=hardware_addr)
        except:
            pass
        else:
            PiFaceRelayPlusWebHandler.pfrps.append(pfrp)

    print("""Starting simple PiFace web control ({n}x PiFace Relay Plus) at:

    http://{addr}:{port}

Change the relay_port with:

    http://{addr}:{port}?{relay_port_set_string}=0xAA

""".format(n=len(PiFaceRelayPlusWebHandler.pfrps),
           addr=get_my_ip(),
           port=args.port,
           relay_port_set_string=RELAY_PORT_SET.format(board_index=0)))

    # run the server
    server_address = ('', int(args.port))
    try:
        httpd = http.server.HTTPServer(server_address,
                                       PiFaceRelayPlusWebHandler)
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('^C received, shutting down server')
        httpd.socket.close()
