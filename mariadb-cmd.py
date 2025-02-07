from backrest.config import config_factory
from backrest.config.validator import Validator
from backrest_cmd.adapter.adapter_factory import adapter_factory
from backrest.config.config import Config
import socket
import os
import threading
from queue import Queue
from select import select
import json

config = config_factory('yaml')
Validator(config).validate()

if config.value('db_type') != 'mariadb':
    raise Exception('MariaDB is not set as db_type in ' + Config.config_path +' , exiting!!')

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
    #@TODO save pid info in writer (db/api)
    #cd @TODO save output in writer (db/api)
    #@TODO write error to writer (db/api) 
    while True:
        try:
            output = queue.get(block=True)  # Waits for an item
            pid = output["pid"]
            print(f"PID {pid} Finished: Return Code: {output['returncode']}")
            print(f"STDOUT:\n{output['stdout']}")
            print(f"STDERR:\n{output['stderr']}")   
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

    adapter = adapter_factory(config)
    # get the method from the adapter based on command called
    method = getattr(adapter, command_data['cmd'])        
    # unpack arguments and call commands
    queue = method(*command_data['args'].values())

    #start listening to process changing
    queue_listener = threading.Thread(target=process_queue, args=(queue,), daemon=True)
    queue_listener.start()

    return {'code': 202, 'status': 'Accepted' }

def start_server():
    #todo create folder on startup and set permissions to mysql:backrest
    server_address = '/var/run/backrest/mariadb_socket'

    try:
        os.unlink(server_address)
    except OSError:
        if os.path.exists(server_address):
            raise

    # Create a UDS socket
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    print('starting up on %s' % server_address)
    sock.bind(server_address)

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
                        
        except Exception:
            print("Exception")
            # @TODO log exception  and let it continue finally will close connextion and restart server.
            pass            
                    
        finally:
            # Clean up the connection         
            connection.close()
            start_server()            
            break
            

start_server()