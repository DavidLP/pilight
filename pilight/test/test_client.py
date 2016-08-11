"""Tests the pilight client.

Connects to a simulation of a pilight-daemon.
"""

import unittest
import time
from mock import patch, call

try:
    from StringIO import StringIO  # Python 2
except ImportError:
    from io import StringIO  # Python 3

from pilight import pilight
from pilight.test import pilight_daemon


def _callback(_):
    """"Function to be called in unit test."""
    pass


class TestClient(unittest.TestCase):

    """Initialize unit test case."""

    def test_client_connection(self):
        """Test for successfull pilight daemon connection."""
        with pilight_daemon.PilightDaemon():
            pilight.Client(host=pilight_daemon.HOST, port=pilight_daemon.PORT)

    def test_client_connection_fail(self):
        """Test for failing pilight daemon connection."""
        with pilight_daemon.PilightDaemon():
            with self.assertRaises(IOError):
                pilight.Client(host='8.8.8.8', port=0)

    def test_send_code(self):
        """Test for successfull code send."""
        with pilight_daemon.PilightDaemon() as my_daemon:
            pilight_client = pilight.Client(host=pilight_daemon.HOST, port=pilight_daemon.PORT)
            pilight_client.send_code(data={'protocol': 'daycom'})
            time.sleep(1)

        self.assertEqual(my_daemon.get_data()['code'], {'protocol': 'daycom'})

    def test_send_code_fail(self):
        """Tests for failed code send."""
        with pilight_daemon.PilightDaemon():
            pilight_client = pilight.Client(host=pilight_daemon.HOST, port=pilight_daemon.PORT)

            # Test 1: Use unknows protocol
            with self.assertRaises(IOError):
                pilight_client.send_code(data={'protocol': 'unknown'})

            # Test 2: Do not send protocoll info, thus Value Error expected
            with self.assertRaises(ValueError):
                pilight_client.send_code(data={'no_protocol': 'test'})

    def test_api(self):
        """Tests connection with different receiver filter and identification."""
        recv_ident = {
            "action": "identify",
            "options": {
                "core": 1,  # To get CPU load and RAM of pilight daemon
                "receiver": 1  # To receive the RF data received by pilight
            }
        }
        with pilight_daemon.PilightDaemon(send_codes=True):
            pilight_client = pilight.Client(host=pilight_daemon.HOST, port=pilight_daemon.PORT,
                                            recv_ident=recv_ident, recv_codes_only=False)
            pilight_client.set_callback(_callback)
            pilight_client.start()
            time.sleep(1)
        pilight_client.stop()

    @patch('pilight.test.test_client._callback')
    def test_receive_code(self, mock):
        """Test for successfull code received."""

        with pilight_daemon.PilightDaemon(send_codes=True):
            pilight_client = pilight.Client(host=pilight_daemon.HOST, port=pilight_daemon.PORT)
            pilight_client.set_callback(_callback)
            pilight_client.start()
            time.sleep(2)
        pilight_client.stop()

        # Check if callback was called several times with expected data
        mock.assert_has_calls([call(pilight_daemon.FAKE_DATA)] * 10)

    @patch('pilight.test.test_client._callback')
    def test_no_receive_filter(self, mock):
        """Test for successfull code received."""
        with pilight_daemon.PilightDaemon(send_codes=True):
            pilight_client = pilight.Client(host=pilight_daemon.HOST, port=pilight_daemon.PORT, veto_repeats=False)
            pilight_client.set_callback(_callback)
            pilight_client.start()
            time.sleep(2)
        pilight_client.stop()

        # Check if calls with repeats != 1 have been made
        calls = []
        for i in range(10):
            fake_data = pilight_daemon.FAKE_DATA.copy()
            fake_data['repeats'] = i + 1
            calls.append(call(fake_data))

        mock.assert_has_calls(calls)

    def test_invalid_identification(self):
        """Send an invalid identification and check for connection failure."""
        recv_ident = {
            "action": "invalid"
        }

        with self.assertRaises(IOError):
            with pilight_daemon.PilightDaemon(send_codes=True):
                pilight.Client(host=pilight_daemon.HOST, port=pilight_daemon.PORT, recv_ident=recv_ident)

    def test_no_callback(self):
        """Test for no callback defined."""
        with pilight_daemon.PilightDaemon(send_codes=True):
            pilight_client = pilight.Client(host=pilight_daemon.HOST, port=pilight_daemon.PORT)
            pilight_client.start()
            time.sleep(1)  # Give time to set thread status

        self.assertFalse(pilight_client.isAlive())
        pilight_client.stop()
