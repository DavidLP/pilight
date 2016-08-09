"""Example how to use the pilight python client asynchronously.

A running pilight-daemon is needed, otherwise nothing will be shown here.
"""

import time
from pilight import pilight


def handle_code(code):  # Simply print received data from pilight
    """Handle to just prints the received code."""
    print(code)

# pylint: disable=C0103
if __name__ == '__main__':
    # Suscribe receiver to core info to have something to receive
    # asynchrounosly. With std. settings the receiver calls the
    # data handle only on received codes!
    recv_ident = {
        "action": "identify",
        "options": {
            "core": 1,  # To get CPU load and RAM of pilight daemon
            "receiver": 1  # To receive the RF data received by pilight
        }
    }

    # Create new pilight connection that runs on localhost with port 5000
    # Turn off to print core info and send info of the pilight-daemon
    pilight_client = pilight.Client(host='127.0.0.1',
                                    port=5000,
                                    recv_ident=recv_ident,
                                    recv_codes_only=False)

    # Set a data handle that is called on received data
    pilight_client.set_callback(handle_code)
    pilight_client.start()  # Start the receiver

    # While the received data is handled you can also send commands
    # Data from https://manual.pilight.org/en/api
    data = {"protocol": ["kaku_switch"],
            "id": 1,
            "unit": 0,
            "off": 1}

    for i in range(5):
        data['id'] = i + 1  # ID > 0 for the kaku_switch protocoll
        time.sleep(2)
        # Will create a sender message received and printed by the receiver
        pilight_client.send_code(data)
