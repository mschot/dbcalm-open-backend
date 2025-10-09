#!/usr/bin/env python3

import json
import socket
import stat
import threading
import time
from pathlib import Path
from select import select

from dbcalm.config.config import Config
from dbcalm.config.config_factory import config_factory
from dbcalm.config.validator import Validator as ConfigValidator
from dbcalm.handler.process_queue_handler import ProcessQueueHandler
from dbcalm.logger.logger_factory import logger_factory
from dbcalm_mariadb_cmd.adapter.adapter_factory import adapter_factory
from dbcalm_mariadb_cmd.command.validator import VALID_REQUEST
from dbcalm_mariadb_cmd.command.validator import Validator as CommandValidator

config = config_factory()
validator = ConfigValidator(config)
validator.validate()
validator.validate_backup_path()

logger = logger_factory()

def process_data(data: bytes) -> dict:
    command_data = json.loads(data.decode())

    validator = CommandValidator()
    response_code, message = validator.validate(command_data)
    if(response_code != VALID_REQUEST):
        logger.error(
            "%s, command: %s ,arguments: %s",
            message, command_data["cmd"], command_data["args"])

        return {"code": response_code, "status": message }

    adapter = adapter_factory()
    # get the method from the adapter based on command called
    method = getattr(adapter, command_data["cmd"])
    # unpack arguments and call commands
    process, queue = method(*command_data["args"].values())

    queue_hander = ProcessQueueHandler(queue)

    # Start a thread to process the queue
    threading.Thread(target=queue_hander.handle, daemon=False).start()

    command_id = (process[0].command_id
                 if isinstance(process, list)
                 else process.command_id)

    return {"code": 202, "status": "Accepted", "id": command_id }


def apply_parent_permissions(file_path: Path) -> None:
    parent_dir = file_path.parent  # Get parent directory
    # Get the parent directory's mode (permissions)
    parent_stat = parent_dir.stat()
    parent_mode = stat.S_IMODE(parent_stat.st_mode)  # Extract permission bits

    # Set the file to have the same permissions as the parent directory
    Path.chmod(file_path, parent_mode)

def unlink_socket(count: int = 0) -> bool:
    socket_path = Path(Config.MARIADB_CMD_SOCKET_PATH)
    if not socket_path.exists():
        return True
    try:
        socket_path.unlink()
    except OSError:
        if socket_path.exists():
            time.sleep(0.2)
            try_for = 10
            if count < try_for:
                unlink_socket(count + 1)
            else:
                return False
    return True

def start_server() -> dict:
    if not unlink_socket():
        logger.error("Could not unlink socket %s", Config.MARIADB_CMD_SOCKET_PATH)
        return {"code": 500, "status": "error"}

    # Create a UDS socket
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    socket_path = Path(Config.MARIADB_CMD_SOCKET_PATH)
    socket_path.parent.mkdir(parents=True, exist_ok=True)

    sock.bind(Config.MARIADB_CMD_SOCKET_PATH)
    # apply parent folder permission (set in systemd unit file)
    # to socket so client can write to it as user will be different
    apply_parent_permissions(Path(Config.MARIADB_CMD_SOCKET_PATH))

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
