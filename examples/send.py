"""Example how to to simply send RF commands.

A running pilight-daemon is needed.
"""

from pilight import pilight

# pylint: disable=C0103
if __name__ == '__main__':
    # Create new pilight connection that runs on localhost with port 5000
    pilight_client = pilight.Client(host='127.0.0.1', port=5000)

    # Send a good code. It is checked to be acknoledged by the piligt-daemon.
    # Data from https://manual.pilight.org/en/api
    pilight_client.send_code(data={"protocol": ["kaku_switch"],
                                   "id": 1,
                                   "unit": 0,
                                   "off": 1})

    # Send a wrong code that lead to an IO error since the pilight-daemon
    # rejects it. Data from https://manual.pilight.org/en/api
    pilight_client.send_code(data={"protocol": ["kaku_switch"],
                                   "id": 0,  # ID has to be > 0
                                   "unit": 0,
                                   "off": 1})
