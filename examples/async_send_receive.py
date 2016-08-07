''' Example to show how to use the pilight python client to create an asynchrous connection to
the pilight-daemon'''

from pilight import pilight
import time

def handle_code(code):  # Simply  print received data from pilight
    print(code)

if __name__ == '__main__':
    # Suscribe receiver to core info to have something to receive asynchrounosly
    # With std. settings the receiver calls the data handle only on received codes! 
    recv_ident = {
        "action": "identify",
        "options": {
            "core": 1,  # To get CPU load and RAM of pilight daemon
            "receiver": 1  # To receive the RF data received by pilight
        }
    }

    pilight_connection = pilight.Client(host='127.0.0.1',  # Create new pilight connection that runs on localhost with port 5000 
                                       port=5000,
                                       recv_ident=recv_ident,
                                       recv_codes_only=False)  # Turn off to print core info and send info of the pilight-daemon  

    pilight_connection.set_callback(handle_code)  # Set a data handle that is called on received data
    pilight_connection.start()  # Start the receiver
   
    # While the received data is handled you can also send commands
    data = {"protocol": [ "kaku_switch" ],  # from https://manual.pilight.org/en/api
            "id": 1,
            "unit": 0,
            "off": 1}

    for i in range(5):
        data['id'] = i + 1  # ID > 0 for the kaku_switch protocoll
        time.sleep(2)
        pilight_connection.send_code(data)  # Will create a sender message received and printed by the receiver
