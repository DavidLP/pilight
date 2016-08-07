''' Example to show how to use the pilight python client to simply send some RF commands'''

from pilight import pilight

if __name__ == '__main__':
    pilight_connection = pilight.Client(host='127.0.0.1', port=5000)  # Create new pilight connection that runs on localhost with port 5000 

    # Send a good code. It is checked to be acknoledged by the piligt-daemon
    pilight_connection.send_code(data={"protocol": [ "kaku_switch" ],  # from https://manual.pilight.org/en/api
                                        "id": 1,
                                        "unit": 0,
                                        "off": 1
                                        })
    
    # Send a wrong code that lead to an IO error since the pilight-daemon rejects it
    pilight_connection.send_code(data={"protocol": [ "kaku_switch" ],  # from https://manual.pilight.org/en/api
                                    "id": 0,  # ID has to be > 0
                                    "unit": 0,
                                    "off": 1
                                    })
