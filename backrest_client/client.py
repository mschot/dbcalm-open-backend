import socket
import json
from backrest.config.config import Config
from select import select

class Client:    
    def connect(self) -> socket.socket | None:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        # Connect the socket to the port where the server is listening
        server_address = Config.CMD_SOCKET_PATH        
        try:
            sock.connect(server_address)
        except OSError:            
            return None
                    
        return sock
    
    def response(self, sock) -> str:
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
                        return all_data                                                  



    def command(self, cmd, args) -> dict:
        # Create a UDS socket
        
        sock = self.connect()
        if sock is None:            
            return {'code': 500, 'status': 'Error connecting to command socket'}
                
        message = {'cmd': cmd, 'args': args}            
        
        response = ''
        try:                        
            sock.sendall(
                json.dumps(message).encode('utf-8')
            )
            response = self.response(sock)
                        
        finally:            
            sock.close()
            return json.loads(response)

        