#!/usr/bin/env python3

import json
import socket
import stat
import threading
import time
from pathlib import Path
from queue import Queue
from select import select

from backrest.config.config import Config
from backrest.config.config_factory import config_factory
from backrest.config.validator import Validator
from backrest.data.adapter.adapter_factory import (
   adapter_factory as data_adapter_factory,
)
from backrest.data.model.backup import Backup
from backrest.data.transformer.process_to_backup import process_to_backup
from backrest_cmd.adapter.adapter_factory import adapter_factory

config = config_factory()
command_runner = True
validator = Validator(config)
validator.validate()
validator.validate_backup_path()

commands = {
    "full_backup": {
        "identifier": "unique|required",
    },

    "incremental_backup": {
        "identifier": "unique|required",
        "from_identifier": "required",
    },
}

#get validation rules for command

def required_args(command: str) -> list:
   return [key for key, value in commands[command].items() if "required" in value]

def unique_args(command: str) -> list:
   return [key for key, value in commands[command].items() if "unique" in value]

def process_queue(queue: Queue) -> None:
    while True:
        process = queue.get(block=True)
        if process.return_code == 0:
            queue.task_done()

        data_adapter = data_adapter_factory()
        if process.type == "backup":
            backup = process_to_backup(process)
            data_adapter.create(backup)
        elif process.type == "restore":
            print("Restore completed successfully")

def validate_command(command_data: dict) -> tuple[bool, str]:
    if(command_data["cmd"] not in commands):
        return False, "Invalid command"

    # check if all required arguments are present
    for arg in required_args(command_data["cmd"]):
        if arg not in command_data["args"]:
            return False, f"Missing required argument {arg}"

    # check if there are more arguments than expected
    max_args_len = len(commands[command_data["cmd"]])
    args_len = len(command_data["args"])
    if(max_args_len < args_len):
        return False, f"""command {command_data["cmd"]} expected {max_args_len}
            arguments but received {args_len}"""

    # In the future we could make the unique validation more generic
    # by making the argument in commands include model and field
    # for instance backup_identifier_unique that way we can find the
    # model and field to validate
    unique_arguments = unique_args(command_data["cmd"])
    data_adapter = data_adapter_factory()
    for arg in unique_arguments:
        if arg != "identifier" or not command_data["args"][arg]:
            continue

        if data_adapter.get(Backup, {"identifier": command_data["args"][arg]}):
                return False, f"""Backup with identifier {command_data["args"][arg]}
                    already exists"""

    return True, None

def process_data(data: bytes) -> dict:
    command_data = json.loads(data.decode())
    valid, message = validate_command(command_data)
    if(not valid):
        return {"code": 403, "status": message }

    adapter = adapter_factory()
    # get the method from the adapter based on command called
    method = getattr(adapter, command_data["cmd"])
    # unpack arguments and call commands
    process, queue = method(*command_data["args"].values())

    # Start a thread to process the queue
    threading.Thread(target=process_queue, args=(queue,)).start()

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
        # @TODO(martijn): add log error of not removing socket
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

        except Exception as e:
            response = {"code": 500, "status": "error"}
            connection.sendall(json.dumps(response).encode("utf-8"))
            print("Exception" + str(e))
            # @TODO log exception  and let it
            # continue finally will close connection and restart server.

        finally:
            # Clean up the connection
            connection.close()
            start_server()

start_server()
