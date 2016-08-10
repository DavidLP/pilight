# A pure python client to connect to a pilight daemon
[![Build Status](https://travis-ci.org/DavidLP/pilight.svg?branch=master)](https://travis-ci.org/DavidLP/pilight)
[![Coverage Status](https://coveralls.io/repos/github/DavidLP/pilight/badge.svg?branch=master)](https://coveralls.io/github/DavidLP/pilight?branch=master)

This client interfaces with the `pilight-daemon` to send and receive RF codes (https://www.pilight.org/).

Sending and receiving is implemented in an asychronous way. A callback function can be defined 
that reacts on received data. Automatic acknowledge if the send data was transmitted by the pilight-daemon
is implemented.

All `pilight-send` commands can be used by this client (https://wiki.pilight.org/doku.php/psend). 
The API is mentioned here: https://manual.pilight.org/en/api.

# Installation

The latest release is hosted on PyPi. Thus for installation type:
```
pip install pilight
```

Otherwise download the code and

```
python setup.py install
```

You can run the unit tests to check the installation

```
nosetests pilight
```

# Usage
```
from pilight import pilight
pilight_connection = pilight.Client()  # Connect to the pilight-daemon at localhost:5000
pilight_connection.send_code(data={"protocol": [ "kaku_switch" ],  #  https://manual.pilight.org/en/api
                                    "id": 1,
                                    "unit": 0,
                                    "off": 1
                                    })
```                         

Also check the examples folder.

