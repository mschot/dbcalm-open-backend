from backrest.config.config_factory import config_factory
from backrest.config.validator import Validator
from backrest_cmd.adapter.adapter_factory import adapter_factory
from backrest.config.config import Config
import socket
import os
import stat
from select import select
import json
import time

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

def process_data(data: bytes):
    command_data = json.loads(data.decode())
    if(command_data['cmd'] not in commands.keys()):
        return {'code': 403, 'status': 'Invalid command' }
                
    expected_args_len = len(commands[command_data['cmd']])
    args_len = len(command_data['args'])
    if(expected_args_len != args_len):
        return {'code': 403, 'status': 'command %s expected %d arguments but received %d ' % 
            (command_data['cmd'], expected_args_len, args_len) }                

    adapter = adapter_factory()
    # get the method from the adapter based on command called
    method = getattr(adapter, command_data['cmd'])        
    # unpack arguments and call commands
    process = method(*command_data['args'].values())
    
    return {'code': 202, 'status': 'Accepted', 'pid': process.pid, 'created_at': process.start_time.strftime("%Y%m%d%H%M%S") }

def apply_parent_permissions(file_path):    
    parent_dir = os.path.dirname(file_path)  # Get parent directory

    # Get the parent directory's mode (permissions)
    parent_stat = os.stat(parent_dir)
    parent_mode = stat.S_IMODE(parent_stat.st_mode)  # Extract permission bits

    print(f"Parent directory permissions: {oct(parent_mode)}")
    # Set the file to have the same permissions as the parent directory
    os.chmod(file_path, parent_mode)

    print(f"Applied permissions {oct(parent_mode)} to {file_path}")


def unlink_socket(count = 0):
    try:
        os.unlink(Config.CMD_SOCKET_PATH)
    except OSError:
        if os.path.exists(Config.CMD_SOCKET_PATH):
            time.sleep(0.2)
            if count < 10:
                unlink_socket(count + 1)
            else:
                return False
    return True

def start_server():               
    if not unlink_socket():     
        #TODO log error of not removing socket
        return {'code': 500, 'status': 'error'}

    # Create a UDS socket
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    
    sock.bind(Config.CMD_SOCKET_PATH)
    # apply parent folder permission (set in systemd unit file)
    # to socket so client can write to it
    apply_parent_permissions(Config.CMD_SOCKET_PATH)

    # Listen for incoming connections
    sock.listen(1)

    while True:
        # Wait for a connection        
        connection, _ = sock.accept()
        try:
            
            # Receive the data in small chunks and retransmit it
            all_data = str.encode('')
            while True:            
                # Check if there is data to read from the socket with a timeout of 0.2 seconds    
                r, _, _ = select([connection],[],[], 0.2)
                if r:
                    data = connection.recv(16)                                
                    all_data += data                
                else:
                    if(len(all_data)):
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