''' Example how to handle codes received by the pilight-daemon. A running pilight-daemon 
is needed that is receiving codes, otherwise nothing will be shown here.'''

from pilight import pilight
import time

def handle_code(code):  # Simply  print received data from pilight
    print(code)

if __name__ == '__main__':
    pilight_connection = pilight.Client(host='127.0.0.1', port=5000)  # Create new pilight connection that runs on localhost with port 5000

    pilight_connection.set_callback(handle_code)  # Set a data handle that is called on received data
    pilight_connection.start()  # Start the receiver
   
    time.sleep(10)  # You have 10 seconds to print all the data the pilight-daemon receives
    pilight_connection.stop()  # Stop the receiver
