
import os
from pathlib import Path

from dbcalm.config.config import Config
from dbcalm.errors.validation_error import ValidationError


class Validator:
    ## This class is used to validate the configuration
    ## It checks if the configuration has the required keys

    def __init__(self, config: Config) -> None:
        self.config = config
        self.should_exist = [
        "db_type",
        "backup_dir",
        "jwt_secret_key",
        "cors_origins",
    ]

    def validate(self) -> None:
        for key in self.should_exist:
            if self.config.value(key) == "" or self.config.value(key) is None:
               msg = f"""Missing required config parameter:
                    {key} in {self.config.CONFIG_PATH}"""
               raise ValidationError(msg)

        # Validate cors_origins is a list
        cors_origins = self.config.value("cors_origins")
        if not isinstance(cors_origins, list):
            msg = f"cors_origins must be a list in {self.config.CONFIG_PATH}"
            raise ValidationError(msg)

        # Validate api_port is a number if set
        api_port = self.config.value("api_port")
        if api_port is not None and not isinstance(api_port, int):
            msg = f"api_port must be a number in {self.config.CONFIG_PATH}"
            raise ValidationError(msg)

        # Validate api_host is a string if set
        api_host = self.config.value("api_host")
        if api_host is not None and not isinstance(api_host, str):
            msg = f"api_host must be a string in {self.config.CONFIG_PATH}"
            raise ValidationError(msg)

    def validate_backup_path(self) -> None:
        # Check if backup path exists
        backup_path = Path(self.config.value("backup_dir"))
        if not Path.exists(backup_path):
            msg = f"Backup path does not exist: {self.config.value('backup_dir')}"
            raise ValidationError(msg)

        # Check if backup path is writable by the current user
        if not os.access(self.config.value("backup_dir"), os.W_OK):
            msg = f"""Backup path is not writable by current user:
                {self.config.value('backup_dir')}"""
            raise ValidationError(msg)






