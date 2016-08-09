"""Example how to handle codes received by the pilight-daemon.

A running pilight-daemon is neededed.
"""

import time
from pilight import pilight


def handle_code(code):  # Simply  print received data from pilight
    """Handle to just prints the received code."""
    print(code)

# pylint: disable=C0103
if __name__ == '__main__':
    # Create new pilight connection that runs on localhost with port 5000
    pilight_client = pilight.Client(host='127.0.0.1', port=5000)

    # Set a data handle that is called on received data
    pilight_client.set_callback(handle_code)
    pilight_client.start()  # Start the receiver

    # You have 10 seconds to print all the data the pilight-daemon receives
    time.sleep(10)
    pilight_client.stop()  # Stop the receiver
