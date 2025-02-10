import socket
import sys
import json
from select import select
from backrest.config.config_factory import config_factory

config = config_factory()
QUEUED_CODE = 202
def process_data(data):
    response = json.loads(data.decode())
    if response['code'] == 202:
        print('queued')

def send_command():
    # Create a UDS socket
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    # Connect the socket to the port where the server is listening
    server_address = config.CMD_SOCKET_PATH
    print(sys.stderr, 'connecting to %s' % server_address)
    try:
        sock.connect(server_address)
    except OSError as msg:
        print(sys.stderr, msg)
        sys.exit(1)

    try:
        # Send data
        message = {'cmd': 'full_backup', 'args': {'identifier': 'test'}}
        print('sending "%s"' % message)
        sock.sendall(json.dumps(message).encode('utf-8'))

        ##do some things here to actually look at response from server
        all_data = str.encode('')
        while True:            
            r, _, _ = select([sock], [], [], 0.2)            
            data = None
            if r:
                data = sock.recv(16)            

            if r and data:                    
                all_data += data                
            else:
                if(len(all_data)):
                    print('processing alldata' + all_data.decode())
                    process_data(all_data)            
                    break         

    finally:
        print(all_data)
        print(sys.stderr, 'closing socket')
        sock.close()

send_command()

