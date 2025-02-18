from __future__ import annotations

import json
import socket
from select import select

from backrest.config.config import Config
from backrest.logger.logger_factory import logger_factory


class Client:
    def __init__(self) -> None:
        self.logger = logger_factory()

    def connect(self) -> socket.socket | None:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        # Connect the socket to the port where the server is listening
        server_address = Config.CMD_SOCKET_PATH
        try:
            sock.connect(server_address)
        except OSError:
            self.logger.exception("error connecting to socket %s", server_address)
            return None

        return sock

    def response(self, sock: socket.socket) -> str:
        ##do some things here to actually look at response from server
        all_data = str.encode("")
        while True:
                r, _, _ = select([sock], [], [], 0.2)
                data = None
                if r:
                    data = sock.recv(16)
                if r and data:
                    all_data += data
                elif(len(all_data)):
                    return all_data



    def command(self, cmd: str, args: dict) -> dict:
        # Connect to UDS socket
        sock = self.connect()
        if sock is None:
            return {"code": 500, "status": "Error connecting to command socket"}

        message = {"cmd": cmd, "args": args}

        response = ""

        sock.sendall(
            json.dumps(message).encode("utf-8"),
        )
        response = self.response(sock)
        sock.close()
        return json.loads(response)

