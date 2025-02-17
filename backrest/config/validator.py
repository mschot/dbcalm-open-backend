
import os
import socket
from pathlib import Path

from backrest.config.config import Config


class Validator:
    ## This class is used to validate the configuration
    ## It checks if the configuration has the required keys
    ## It will probably need changing in the future as these checks are very basic

    def __init__(self, config: Config) -> None:
        self.config = config
        self.should_exist = [
        "db_type",
        "backup_dir",
    ]

    def validate(self) -> None:
        for key in self.should_exist:
            if self.config.value(key) == "" or self.config.value(key) is None:
               msg = f"""Missing required config parameter:
                    {key} in {self.Config.CONFIG_PATH}"""
               raise ValidatorError(msg)

        # Check if db_host is reachable and let it throw an error if it is not
        db_host = self.config.value("db_host")
        socket.gethostbyname(db_host)

    def validate_backup_path(self) -> None:
        # Check if backup path exists
        backup_path = Path(self.config.value("backup_dir"))
        if not Path.exists(backup_path):
            msg = f"Backup path does not exist: {self.config.value('backup_dir')}"
            raise ValidatorError(msg)

        # Check if backup path is writable by the current user
        if not os.access(self.config.value("backup_dir"), os.W_OK):
            msg = f"""Backup path is not writable by current user:
                {self.config.value('backup_dir')}"""
            raise ValidatorError(msg)


class ValidatorError(Exception):
    pass



