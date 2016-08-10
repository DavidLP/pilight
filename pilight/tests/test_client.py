"""Tests the pilight client.

Connects to a simulation of a pilight-daemon.
"""

import unittest
import socket
import threading
import time
import datetime
import json

import logging

from pilight import pilight

# Settings for the pilight-daemon simulation
HOST = '127.0.0.1'
PORT = 5000

SEND_DELAY = 0.1  # How often a fake code is send in seconds


class PilightDaemon(object):
    """Helper class to provice a pilight-daemon."""

    def __init__(self, host=HOST, port=PORT, send_codes=False):
        self.host = host
        self.port = port
        self.send_codes = send_codes
        self.pilight_daemon = PilightDeamonSim(
            self.host, self.port, self.send_codes)

    def __enter__(self):
        self.pilight_daemon.start()
        time.sleep(0.1)

    def __exit__(self, type, value, traceback):
        self.pilight_daemon.stop()
        time.sleep(0.1)


class PilightDeamonSim(threading.Thread):
    """Simulate the pilight-daemon API for testing.

    Of cause only a few important commands are supported.
    This is a very hackish synchronous daemon that is
    not an example for good sockets servers!"""

    def __init__(self, host, port, send_codes):
        self.send_codes = send_codes

        # Setup thread
        threading.Thread.__init__(self)
        self.daemon = True
        self._stop = threading.Event()
        self.lock = threading.Lock()

        # Setup server socket
        self.server_socket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM)

        time.sleep(0.1)
        self.server_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        time.sleep(0.1)
        self.server_socket.settimeout(0.01)  # Unset blocking
        self.server_socket.bind((host, port))

        self.server_socket.listen(2)  # Allow 2 connections
        self.client_sockets = []

    def run(self):
        """Simple infinite loop handling socket connections."""
        last_send = datetime.datetime.now()
        while not self._stop.wait(0.01):
            self._handle_client_connections()
            self._handle_client_data()
            if self.send_codes:
                if (((datetime.datetime.now() - last_send).total_seconds() >
                     SEND_DELAY)):
                    if len(self.client_sockets) > 0:
                        self.client_sockets[0].send(
                            json.dumps({"origin": "receiver",
                                        "repeats": 1,
                                        "message": {
                                            "protocol": ["kaku_switch"],
                                            "id": 0,
                                            "unit": 0,
                                            "off": 1}}).encode())

        # Close client connections
        for client_socket in self.client_sockets:
            client_socket.close()

    def _handle_client_connections(self):
        try:
            self.client_sockets.append(
                self._new_client(self.server_socket.accept()[0]))
        except socket.timeout:
            pass

    def _handle_client_data(self):
        for client_socket in self.client_sockets:  # Simple poll for data
            try:
                self._handle_message(client_socket)
            except socket.timeout:  # We poll, thus timeout for no data
                pass

    def _handle_message(self, client_socket):
        """Called in poll loop to handle messages."""
        messages = client_socket.recv(1024).splitlines()
        for message in messages:  # Loop over received messages
            if message:  # Can be empty due to splitlines
                message_dict = json.loads(message.decode())
                if message_dict["code"]["protocol"] == "daycom":
                    client_socket.send(
                        json.dumps({'status': 'success'}).encode())
                else:
                    client_socket.send(
                        json.dumps({'status': 'failure'}).encode())

    def _new_client(self, client_socket):
        """Handle new client connection.

        Fake pilight-daemon protocol by returning success on identifiy action.
        """
        def _acknowledge_connection(messages):
            for message in messages:  # Loop over received messages
                if message:  # Can be empty due to splitlines
                    message_dict = json.loads(message.decode())
                    if ("action" in message_dict and
                            message_dict["action"] == "identify"):
                        client_socket.send(
                            json.dumps({'status': 'success'}).encode())
                        break

        client_socket.settimeout(0.01)  # Unset blocking
        messages = client_socket.recv(1024).splitlines()
        _acknowledge_connection(messages)
        return client_socket

    def stop(self):
        """Called to stop the reveiver thread."""
        self._stop.set()


class TestClient(unittest.TestCase):
    """Initialize unit test case."""

    def test_client_connection(self):
        """Test for successfull pilight daemon connection."""
        with PilightDaemon():
            pilight.Client(host=HOST, port=PORT)

    def test_client_connection_fail(self):
        """Test for failing pilight daemon connection."""
        with PilightDaemon():
            with self.assertRaises(IOError):
                pilight.Client(host='8.8.8.8', port=0)

    def test_send_code(self):
        """Test for successfull code send."""
        with PilightDaemon():
            pilight_client = pilight.Client(host=HOST, port=PORT)
            pilight_client.send_code(data={'protocol': 'daycom'})

    def test_send_code_fail(self):
        """Tests for failed code send."""
        with PilightDaemon():
            pilight_client = pilight.Client(host=HOST, port=PORT)

            # Test 1: Use unknows protocol
            with self.assertRaises(IOError):
                pilight_client.send_code(data={'protocol': 'unknown'})

            # Test 2: Do not send protocoll info, thus Value Error expected
            with self.assertRaises(ValueError):
                pilight_client.send_code(data={'no_protocol': 'test'})

    def test_receive_code(self):
        """Test for successfull code received."""

        # Flag that is set when callback was called
        global received
        received = False

        def _callback(_):
            global received
            received = True

        with PilightDaemon(send_codes=True):
            pilight_client = pilight.Client(host=HOST, port=PORT)
            pilight_client.set_callback(_callback)
            pilight_client.start()
            time.sleep(1)

        self.assertTrue(received)

# pylint: disable=C0103
if __name__ == '__main__':

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - "
        "[%(levelname)-8s] (%(threadName)-10s) %(message)s")
    suite = unittest.TestLoader().loadTestsFromTestCase(TestClient)
    unittest.TextTestRunner(verbosity=2).run(suite)
