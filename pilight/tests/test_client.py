''' So far nothing is really tested, besides the correct installation. Because testing
would require an installation / simulation of the pilight-daemon.
'''

import unittest
from pilight import pilight

class TestClient(unittest.TestCase):

    def test_client_connection_fail(self):
        with self.assertRaises(IOError):
            pilight.Client()

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestClient)
    unittest.TextTestRunner(verbosity=2).run(suite)
