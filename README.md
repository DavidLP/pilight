# A pure python client to connect to a pilight daemon to send and receive RF commands asynchronously.
[![Build Status](https://travis-ci.org/DavidLP/pilight.svg?branch=master)](https://travis-ci.org/DavidLP/pilight)
[![Coverage Status](https://coveralls.io/repos/DavidLP/pilight/badge.svg?branch=master&service=github)](https://coveralls.io/github/DavidLP/pilight?branch=master)

This client interfaces with the pilight-daemon to send and receive RF codes (https://www.pilight.org/).

Sending and receiving is implemented in an asychronous way. A callback function can be defined 
that reacts on received data.

All pilight-send commands can be used by this client (https://wiki.pilight.org/doku.php/psend). 
Also check https://manual.pilight.org/en/api.

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

