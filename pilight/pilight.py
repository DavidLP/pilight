import threading
import socket
import logging
import json

class Client(threading.Thread):
    """
    This client interfaces with the pilight-daemon to send and receive codes (https://www.pilight.org/).

    Sending and receiving is implemented in an asychronous way. A callback function can be defined 
    that reacts on received data.
    
    All pilight-send commands can be used by this client (https://wiki.pilight.org/doku.php/psend). 
    Also check https://manual.pilight.org/en/api.
    
    :param host: Address where the pilight-daemon intance runs
    :param port: Port of the pilight-daemon on the host
    :param timeout: Time until a time out exception is raised when connecting
    :param recv_ident: The identification of the receiver to sucribe to the pilight-daemon topics (https://manual.pilight.org/en/api)
    :param recv_codes_only: If True only call the callback function when the pilight-daemon received a code, not for status messages etc.
    See 
    
    """
 
    def __init__(self, host='127.0.0.1', port=5000, timeout=1, recv_ident=None, recv_codes_only=True):
        threading.Thread.__init__(self)
        self.daemon = True
        self._stop = threading.Event()
        self.lock = threading.Lock()
        self.recv_codes_only = recv_codes_only
         
        # Identify client (https://manual.pilight.org/en/api)
        client_identification_sender = {
            "action": "identify",
            "options": {
                "core": 0,  # To get CPU load and RAM of pilight daemon, is neverless ignored by daemon ...
                "receiver": 0,  # To receive the RF data received by pilight
                "config": 0
            }
        }
        
        if recv_ident:
            client_identification_receiver = recv_ident
        else:
            client_identification_receiver = {
                "action": "identify",
                "options": {
                    "core": 0,  # To get CPU load and RAM of pilight daemon
                    "receiver": 1,  # To receive the RF data received by pilight
                    "config": 0,
                    "forward": 0
                }
            }
         
        # Open 2 socket connections, one for sending one for receiving data
        # That is the simplest approach to allow asynchronus communication with the pilight daemon
        self.receive_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Timeout to allow receiver thread termination and to restrict blocking connection time
        self.receive_socket.settimeout(timeout)  
        self.send_socket.settimeout(timeout)

        self.receive_socket.connect((host, port))
        self.send_socket.connect((host, port))
 
        # Identify this clients sockets at the pilight-deamon
        self.receive_socket.send(json.dumps(client_identification_receiver).encode())
        answer_1 = json.loads(self.receive_socket.recv(1024).decode())
        self.send_socket.send(json.dumps(client_identification_sender).encode())
        answer_2 = json.loads(self.send_socket.recv(1024).decode())
        
        # Check connections are acknowledged
        if not 'success' in answer_1['status'] or not 'success' in answer_2['status']:
            raise IOError('Connection to the pilight daemon failed. Reply %s, %s', answer_1, answer_2)
            
        self.callback = None
            
    def set_callback(self, function):
        """ Define a function to be called when data is received from the pilight daemon
        """
        self.callback = function
        
    def stop(self):
        """ Called to stop the reveiver thread.
        """
        self._stop.set()
 
    def run(self):  # Thread for receiving data from pilight
        logging.debug('Pilight receiver thread started')
        if not self.callback:
            logging.warning('No callback function set, stopping readout thread')
            return 

        while not self._stop.isSet():
            try:  # Read socket in a non blocking call and interpret data
                messages = self.receive_socket.recv(1024).splitlines()  # Sometimes more than one JSON object is in the stream thus split at \n
                for message in messages:  # Loop over received  messages
                    if message:  # Can be empty due to splitlines
                        message_dict = json.loads(message.decode())
                        if self.recv_codes_only:
                            if 'receiver' in message_dict['origin']:  # Filter: Only use receiver messages
                                self.callback(message_dict)
                        else:
                            self.callback(message_dict)
            except (socket.timeout, ValueError):  # No data
                pass
        logging.debug('Pilight receiver thread stopped')
        
    def send_code(self, data, acknowledge=True):
        ''' Send a RF code known to the pilight-daemon (https://manual.pilight.org/en/api). 
        When acknowledge is set, it is checked if the code was issued.
        :param data: Dictionary with the data
        :param acknowledge: Raise IO exception if the code is not send by the pilight-deamon
        '''

        if not "protocol" in data:
            raise ValueError('Pilight data to send does not contain a protocol info. Check the pilight-send doku!', str(data))
        
        # Create message to send
        message = {
            "action": "send",  # Tell pilight daemon to send the data
            "code": data,
        }
        
        self.send_socket.sendall(json.dumps(message).encode())  # If connection is closed IOError is raised
        
        if acknowledge:  # Check if command is acknowledged by pilight daemon
            messages = self.send_socket.recv(1024).splitlines()
            received = False
            for message in messages:  # Loop over received messages
                if message:  # Can be empty due to splitlines
                    acknowledge_message = json.loads(message.decode())
                    if 'status' in acknowledge_message and acknowledge_message['status'] == 'success':  # Filter correct message
                        received = True
            if not received:
                raise IOError('Send code failed. Code: %s', str(data))