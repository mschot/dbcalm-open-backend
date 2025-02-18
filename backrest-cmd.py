#!/usr/bin/env python3

import json
import socket
import stat
import threading
import time
from pathlib import Path
from select import select

from backrest.config.config import Config
from backrest.config.config_factory import config_factory
from backrest.config.validator import Validator as ConfigValidator
from backrest.handler.process_queue_handler import ProcessQueueHandler
from backrest.logger.logger_factory import logger_factory
from backrest_cmd.adapter.adapter_factory import adapter_factory
from backrest_cmd.command.validator import Validator as CommandValidator

config = config_factory()
validator = ConfigValidator(config)
validator.validate()
validator.validate_backup_path()

logger = logger_factory()

def process_data(data: bytes) -> dict:
    command_data = json.loads(data.decode())

    validator = CommandValidator()
    valid, message = validator.validate(command_data)
    if(not valid):
        logger.error(
            "%s, command: %s ,arguments: %s",
            message, command_data["cmd"], command_data["args"])

        return {"code": 403, "status": message }

    adapter = adapter_factory()
    # get the method from the adapter based on command called
    method = getattr(adapter, command_data["cmd"])
    # unpack arguments and call commands
    process, queue = method(*command_data["args"].values())

    queue_hander = ProcessQueueHandler(queue)

    # Start a thread to process the queue
    threading.Thread(target=queue_hander.handle).start()

    return {"code": 202, "status": "Accepted", "pid": process.pid,
            "created_at": process.start_time.strftime("%Y%m%d%H%M%S") }

def apply_parent_permissions(file_path: Path) -> None:
    parent_dir = file_path.parent  # Get parent directory
    # Get the parent directory's mode (permissions)
    parent_stat = parent_dir.stat()
    parent_mode = stat.S_IMODE(parent_stat.st_mode)  # Extract permission bits

    # Set the file to have the same permissions as the parent directory
    Path.chmod(file_path, parent_mode)

def unlink_socket(count: int = 0) -> bool:
    try:
        Path.unlink(Config.CMD_SOCKET_PATH)
    except OSError:
        if Path.exists(Config.CMD_SOCKET_PATH):
            time.sleep(0.2)
            try_for = 10
            if count < try_for:
                unlink_socket(count + 1)
            else:
                return False
    return True

def start_server() -> dict:
    if not unlink_socket():
        logger.error("Could not unlink socket %s", Config.CMD_SOCKET_PATH)
        return {"code": 500, "status": "error"}

    # Create a UDS socket
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    sock.bind(Config.CMD_SOCKET_PATH)
    # apply parent folder permission (set in systemd unit file)
    # to socket so client can write to it as user will be different
    apply_parent_permissions(Path(Config.CMD_SOCKET_PATH))

    # Listen for incoming connections
    sock.listen(1)

    while True:
        # Wait for a connection
        connection, _ = sock.accept()
        try:

            # Receive the data in small chunks and retransmit it
            all_data = str.encode("")
            while True:
                # Check if there is data to read from the socket
                # with a timeout of 0.2 seconds
                r, _, _ = select([connection],[],[], 0.2)
                if r:
                    data = connection.recv(16)
                    all_data += data
                elif(len(all_data)):
                    response = process_data(all_data)
                    connection.sendall(json.dumps(response).encode("utf-8"))
                    break

        except Exception:
            response = {"code": 500, "status": "error"}
            connection.sendall(json.dumps(response).encode("utf-8"))
            logger.exception("Error processing data")

        finally:
            # Clean up the connection
            connection.close()
            start_server()

start_server()
