from __future__ import annotations

import json
import socket
import time
from select import select

from dbcalm.config.config import Config
from dbcalm.logger.logger_factory import logger_factory


class Client:
    def __init__(self, timeout: int | None = None) -> None:
        self.logger = logger_factory()
        # Use longer timeout in development mode
        if timeout is not None:
            self.timeout = timeout  # Use custom timeout if provided
        elif Config.DEV_MODE:
            self.timeout = Config.DEV_TIMEOUT
        else:
            self.timeout = Config.DEFAULT_TIMEOUT

    def connect(self) -> socket.socket | None:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        # Connect the socket to the port where the server is listening
        server_address = Config.MARIADB_CMD_SOCKET_PATH
        try:
            sock.connect(server_address)
        except OSError:
            self.logger.exception("error connecting to socket %s", server_address)
            return None

        return sock

    def response(self, sock: socket.socket) -> str:
        ##do some things here to actually look at response from server
        all_data = str.encode("")
        start_time = time.time()

        while True:
            # Check if we've exceeded the timeout
            if time.time() - start_time > self.timeout:
                self.logger.warning(
                    "Socket response timed out after %s seconds",
                    self.timeout,
                )
                return json.dumps({
                    "code": 503,
                    "status": "Service unavailable - command timed out",
                }).encode("utf-8")

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

