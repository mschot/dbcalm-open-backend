import client, server
from os import path
from time import sleep

server_host = "127.0.0.1"
server_port = 35689
server_sni_hostname = "www.company-b.com"
server_cert = path.join(path.dirname(__file__), "server.crt")
server_key = path.join(path.dirname(__file__), "server.key")

s = server.SSLServer(server_host, server_port, server_cert, server_key)
s_thread = server.SSLServerThread(s)
s_thread.run()

