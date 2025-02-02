import client
import sys

server_host = "127.0.0.1"
server_port = 35689
server_sni_hostname = "www.company-b.com"

c = client.SSLClient(
    server_host, server_port, server_sni_hostname
)
c.connect()

for line in sys.stdin:
    c.send(line)   
     

c.close()

