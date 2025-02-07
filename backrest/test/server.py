import socket
import ssl
from threading import Thread


class SSLServer:
    def __init__(
        self, host, port, server_cert, server_key, chunk_size=1024
    ):
        self.host = host
        self.port = port
        self.chunk_size = chunk_size
        self._context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        self._context.verify_mode = ssl.CERT_NONE
        self._context.load_cert_chain(server_cert, server_key)        

    def connect(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0) as sock:
            sock.bind((self.host, self.port))
            sock.listen(5)
            while True:                
                conn, _ = sock.accept()
                with self._context.wrap_socket(conn, server_side=True) as sconn:
                    self._recv(sconn)                    
                    

    def _recv(self, sock):
        while True:
            total_data = 0
            data = sock.recv(self.chunk_size)                      
            print(data)
            if data is not None:
                total_data += len(data)
                print(data.decode())                

            if total_data > 0 and len(data) < self.chunk_size:                
                sock.sendall(b"test1234")        
                print ("End of data")
                break
                                
                


class SSLServerThread(Thread):
    def __init__(self, server):
        super().__init__()
        self._server = server
        self.daemon = True

    def run(self):
        self._server.connect()