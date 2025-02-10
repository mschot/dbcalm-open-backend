from backrest.config.config_factory import config_factory
from backrest.config.validator import Validator
from backrest_cmd.adapter.adapter_factory import adapter_factory
from backrest.config.config import Config
from backrest.data.adapter.adapter_factory import adapter_factory as data_adapter_factory
import socket
import os
import stat
import threading
from queue import Queue
from select import select
import json

config = config_factory()
command_runner = True
Validator(config, command_runner).validate()

if config.value('db_type') != 'mariadb':
    raise Exception('MariaDB is not set as db_type in ' + Config.CONFIG_PATH +' , exiting!!')

commands = {
    'full_backup': [
        'identifier'
    ],
    'incremental_backup': [
        'identifier',
        'from_identifier'
    ]
}

def process_queue(queue: Queue):        
    while True:
        try:
            _process = queue.get(block=True)  
            # we can do something here with the process if needed            
            queue.task_done()         
        except Exception as e:
            print("Error processing queue:", e)

def process_data(data: bytes):
    command_data = json.loads(data.decode())
    if(command_data['cmd'] not in commands.keys()):
        raise Exception('invalid command:' + command_data['cmd'])
    
    
    expected_args_len = len(commands[command_data['cmd']])
    args_len = len(command_data['args'])
    if(expected_args_len != args_len):
        raise Exception(
            'command %s expected %d arguments but received %d ' % 
            (command_data['cmd'], expected_args_len, args_len)
        )
    
    print('going to process:' + data.decode())

    adapter = adapter_factory()
    # get the method from the adapter based on command called
    method = getattr(adapter, command_data['cmd'])        
    # unpack arguments and call commands
    queue = method(*command_data['args'].values())

    #start listening to process changing
    queue_listener = threading.Thread(target=process_queue, args=(queue,), daemon=True)
    queue_listener.start()

    return {'code': 202, 'status': 'Accepted' }

def apply_parent_permissions(file_path):    
    parent_dir = os.path.dirname(file_path)  # Get parent directory

    # Get the parent directory's mode (permissions)
    parent_stat = os.stat(parent_dir)
    parent_mode = stat.S_IMODE(parent_stat.st_mode)  # Extract permission bits

    print(f"Parent directory permissions: {oct(parent_mode)}")
    # Set the file to have the same permissions as the parent directory
    os.chmod(file_path, parent_mode)

    print(f"Applied permissions {oct(parent_mode)} to {file_path}")

def start_server():       
    server_address = Config.CMD_SOCKET_PATH

    try:
        os.unlink(server_address)
    except OSError:
        if os.path.exists(server_address):
            raise

    # Create a UDS socket
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    
    print('starting up on %s' % server_address)
    sock.bind(server_address)
    # apply parent folder permission (set in systemd unit file)
    # to socket so client can write to it
    apply_parent_permissions(server_address)

    # Listen for incoming connections
    sock.listen(1)

    while True:
        # Wait for a connection
        print('waiting for a connection')
        connection, client_address = sock.accept()
        try:
            print('connection from', client_address)

            # Receive the data in small chunks and retransmit it
            all_data = str.encode('')
            while True:                
                r, _, _ = select([connection],[],[], 0.2)
                if r:
                    data = connection.recv(16)                                
                    all_data += data                
                else:
                    if(len(all_data)):
                        print('going to process data')
                        response = process_data(all_data)
                        connection.sendall(json.dumps(response).encode('utf-8'))
                        break                    
                        
        except Exception as e:
            response = {'code': 500, 'status': 'error'}
            connection.sendall(json.dumps(response).encode('utf-8'))
            print("Exception" + str(e))
            # @TODO log exception  and let it continue finally will close connextion and restart server.
            pass            
                    
        finally:
            # Clean up the connection         
            connection.close()
            start_server()            
            break
            

start_server()