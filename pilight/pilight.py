"""This module implements a client to interface the pilight-daemon.

More information about pilight is here: https://www.pilight.org/.
"""

import threading
import socket
import json
import logging
import time


class Client(threading.Thread):

    """This client interfaces with the pilight-daemon (https://www.pilight.org/).

    Sending and receiving codes is implemented in an asychronous way.
    A callback function can be defined that reacts on received data.

    All pilight-send commands can be used by this client. Documentation
    can be found here https://wiki.pilight.org/doku.php/psend.
    Also check https://manual.pilight.org/en/api.

    :param host: Address where the pilight-daemon intance runs
    :param port: Port of the pilight-daemon on the host
    :param timeout: Time until a time out exception is raised when connecting
    :param recv_ident: The identification of the receiver to sucribe
    to the pilight-daemon topics (https://manual.pilight.org/en/api)
    :param recv_codes_only: If True: only call the callback function when the
    pilight-daemon received a code, not for status messages etc.
    :param veto_repeats: If True: only call the callback function when the
    pilight-daemon received a new code, not the same code repeated.
    Repeated codes happen quickly when a button is pressed.
    """

    # pylint: disable=too-many-arguments, too-many-instance-attributes

    # How many seconds to wait before trying to reconnect
    RECONNECT_WAIT_SEC = 1

    def __init__(self, host='127.0.0.1', port=5000, timeout=1,
                 recv_ident=None, recv_codes_only=True, veto_repeats=True):
        """Initialize the pilight client.

        The readout thread is not started automatically.
        """
        threading.Thread.__init__(self)
        self.daemon = True
        self._stop_thread = threading.Event()
        self._lock = threading.Lock()
        self.recv_ident = recv_ident
        self.recv_codes_only = recv_codes_only
        self.veto_repeats = veto_repeats

        self.host = host
        self.port = port
        self.timeout = timeout

        # Open 2 socket connections, one for sending one for receiving data
        # That is the simplest approach to allow asynchronus communication with
        # the pilight daemon
        self.connect_sender()
        self.connect_receiver()

        # Timeout to allow receiver thread termination and to restrict blocking
        # connection time
        self.callback = None

    def connect_receiver(self):
        if self.recv_ident:
            client_identification_receiver = self.recv_ident
        else:
            client_identification_receiver = {
                "action": "identify",
                "options": {
                    "core": 0,  # To get CPU load and RAM of pilight daemon
                    # To receive the RF data received by pilight
                    "receiver": 1,
                    "config": 0,
                    "forward": 0
                }
            }

        self.receive_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.receive_socket.settimeout(self.timeout)
        self.receive_socket.connect((self.host, self.port))
        # Identify this clients sockets at the pilight-deamon
        self.receive_socket.send(
            json.dumps(client_identification_receiver).encode())
        answer = json.loads(self.receive_socket.recv(1024).decode())
        # Check connections are acknowledged
        if ('success' not in answer['status']):
            raise IOError(
                'Connection to the pilight daemon failed. Reply %s',
                answer)

    def connect_sender(self):
        # Identify client (https://manual.pilight.org/en/api)
        client_identification_sender = {
            "action": "identify",
            "options": {
                # To get CPU load and RAM of pilight daemon, is neverless
                # ignored by daemon ...
                "core": 0,
                "receiver": 0,  # To receive the RF data received by pilight
                "config": 0
            }
        }

        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.send_socket.settimeout(self.timeout)
        self.send_socket.connect((self.host, self.port))
        self.send_socket.send(
            json.dumps(client_identification_sender).encode())
        answer = json.loads(self.send_socket.recv(1024).decode())
        if ('success' not in answer['status']):
            raise IOError(
                'Connection to the pilight daemon failed. Reply %s',
                answer)

   
    def set_callback(self, function):
        """Function to be called when data is received."""
        self.callback = function

    def stop(self):
        """Called to stop the reveiver thread."""
        self._stop_thread.set()
        # f you want to close the connection in a timely fashion,
        # call shutdown() before close().
        with self._lock:  # Receive thread might use the socket
            self.receive_socket.shutdown(socket.SHUT_RDWR)
            self.receive_socket.close()

        self.send_socket.shutdown(socket.SHUT_RDWR)
        self.send_socket.close()

    def run(self):
        # "Watchdog" thread
        watchdog_thread = threading.Thread(target=self._watchdog, name="watchdog")
        try:
            watchdog_thread.start()
            self._run()
        finally:
            self._stop_thread.set()
            watchdog_thread.join()
        return 0

    def try_sendall_with_reconnect(self, message):
        try:
            self.send_socket.sendall(message)
        except(socket.error):
            time.sleep(self.RECONNECT_WAIT_SEC)
            self.connect_sender()
            self.send_socket.send(message)

    def _watchdog(self):
        # check pilight connection every 100ms
        while True:
            time.sleep(0.100)
            self.try_sendall_with_reconnect('HEART\n'.encode())
            answer = self.send_socket.recv(1024).decode()
            if not (answer.startswith('BEAT')):
                logging.debug('Heartbeat lost, reconnecting...')
                time.sleep(self.RECONNECT_WAIT_SEC)
                self.connect_sender()
                self.connect_receiver()

    def _run(self): # Thread for receiving data from pilight
        """Receiver thread function called on Client.start()."""
        logging.debug('Pilight receiver thread started')
        if not self.callback:
            raise RuntimeError('No callback function set, cancel readout thread')

        def handle_messages(messages):
            """Call callback on each receive message."""
            for message in messages:  # Loop over received  messages
                if message:  # Can be empty due to splitlines
                    message_dict = json.loads(message.decode())
                    if self.recv_codes_only:
                        # Filter: Only use receiver messages
                        if 'receiver' in message_dict['origin']:
                            if self.veto_repeats:
                                if message_dict['repeats'] == 1:
                                    self.callback(message_dict)
                            else:
                                self.callback(message_dict)
                    else:
                        self.callback(message_dict)

        while not self._stop_thread.isSet():
            try:  # Read socket in a non blocking call and interpret data
                # Sometimes more than one JSON object is in the stream thus
                # split at \n
                with self._lock:
                    messages = self.receive_socket.recv(1024).splitlines()
                    handle_messages(messages)
            # FIXME handle lost connection -> reconnect
            except (socket.timeout, ValueError):  # No data
                pass
        logging.debug('Pilight receiver thread stopped')

    def send_code(self, data, acknowledge=True):
        """Send a RF code known to the pilight-daemon.

        For protocols look at https://manual.pilight.org/en/api.
        When acknowledge is set, it is checked if the code was issued.
        :param data: Dictionary with the data
        :param acknowledge: Raise IO exception if the code is not
        send by the pilight-deamon
        """
        if "protocol" not in data:
            raise ValueError(
                'Pilight data to send does not contain a protocol info. '
                'Check the pilight-send doku!', str(data))

        # Create message to send
        message = {
            "action": "send",  # Tell pilight daemon to send the data
            "code": data,
        }

        # If connection is closed IOError is raised
        self.try_sendall_with_reconnect(json.dumps(message).encode())
        
        if acknowledge:  # Check if command is acknowledged by pilight daemon
            messages = self.send_socket.recv(1024).splitlines()
            received = False
            for message in messages:  # Loop over received messages
                if message:  # Can be empty due to splitlines
                    acknowledge_message = json.loads(message.decode())
                    # Filter correct message
                    if ('status' in acknowledge_message and
                            acknowledge_message['status'] == 'success'):
                        received = True
            if not received:
                raise IOError('Send code failed. Code: %s', str(data))
