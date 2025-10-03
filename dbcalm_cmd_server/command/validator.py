
import subprocess
from pathlib import Path

from dbcalm.config.config_factory import config_factory
from dbcalm.data.adapter.adapter_factory import (
    adapter_factory as data_adapter_factory,
)
from dbcalm.data.model.backup import Backup

VALID_REQUEST = 200
INVALID_REQUEST = 400
PREREQUISTE_FAILED = 412
CONFLICT = 409
NOT_FOUND = 404

class Validator:
    def __init__(self) -> None:
        self.config = config_factory()
        self.commands = {
            "full_backup": {
                "id": "unique|required",
            },
            "incremental_backup": {
                "id": "unique|required",
                "from_backup_id": "required",
            },
            "restore_backup": {
                "id_list": "required",
                "target": "required",
                "|database_restore": ["server_dead", "data_dir_empty"],
            },
        }

    def required_args(self, command: str) -> list:
        return [
                key for key,
                value in self.commands[command].items() if "required" in value
            ]

    def unique_args(self, command: str) -> list:
        return [
                key for key,
                value in self.commands[command].items() if "unique" in value
            ]

    def validate(self, command_data: dict) -> tuple[int, str]:
        if command_data["cmd"] not in self.commands:
            return INVALID_REQUEST, "Invalid command"

        # check if all required arguments are present
        for arg in self.required_args(command_data["cmd"]):
            if arg not in command_data["args"]:
                return INVALID_REQUEST, f"Missing required argument {arg}"


        #check other requirements
        if (
            "|database_restore" in self.commands[command_data["cmd"]]
            and command_data["args"]["target"] == "database"
        ):
            other_checks = self.database_restore(
                self.commands[command_data["cmd"]]["|database_restore"],
            )
            if other_checks[0] != VALID_REQUEST:
                return other_checks


        # In the future we could make the unique validation more generic
        # by making the argument in commands include model and field
        # for instance backup_id_unique that way we can find the
        # model and field to validate
        unique_arguments = self.unique_args(command_data["cmd"])
        data_adapter = data_adapter_factory()
        for arg in unique_arguments:
            if arg != "id" or not command_data["args"][arg]:
                continue

            if data_adapter.get(Backup, {"id": command_data["args"][arg]}):
                return CONFLICT, ("Backup with id"
                    f"{command_data["args"][arg]} already exists")

        return VALID_REQUEST, ""
    def database_restore(self, checks: list) -> tuple[int, str]:
        if "server_dead" in checks and not self.server_dead():
            return PREREQUISTE_FAILED, ("cannot restore to database,"
                            " MySQL/MariaDb server is not stopped")

        if "data_dir_empty" in checks and not self.data_dir_empty():
            return PREREQUISTE_FAILED, ("cannot restore to database,"
                            " mysql/mariadb data directory is not empty"
                            "(usually /var/lib/mysql)")

        return VALID_REQUEST, ""


    def server_dead(self) -> bool:
        credentials_file = (self.config.value("backup_credentials_file")
                if self.config.value("backup_credentials_file") is not None
                else f"/etc/{ self.config.PROJECT_NAME }/credentials.cnf")

        command = [
            "mysqladmin",
            f"--defaults-file={credentials_file}",
            "--defaults-group-suffix=-dbcalm",
            "ping",
        ]

        result = subprocess.run(  # noqa: S603
            command,
            capture_output=True,
            text=True,
            check=False,
        )

        # If mysqladmin ping succeeds (return code 0), the server is alive
        # If it fails (non-zero return code), the server is dead
        return result.returncode != 0

    def data_dir_empty(self) -> bool:
        # Get data directory from config or use default
        data_dir = self.config.value("mysql_data_dir")
        if data_dir is None:
            data_dir = "/var/lib/mysql"

        data_dir_path = Path(data_dir)
        # Check if directory exists
        if not data_dir_path.is_dir():
            # If directory doesn't exist, consider it "empty"
            return True

        try:
            # Get list of all items in directory
            items = list(data_dir_path.iterdir())
        except (PermissionError, FileNotFoundError):
            # If we can't access the directory for whatever reason,
            # we'll assume it's not ready for restore operations
            return False

        # Filter out common allowed items
        allowed_items = [
            "ib_buffer_pool", "ibdata1",
            "ib_logfile0", "ib_logfile1",
        ]
        allowed_extensions = [".sock", ".pid", ".err", ".cnf", ".flag"]

        # Check each item in the directory
        data_items = []
        for item in items:
            # Skip allowed items and items that end with allowed extensions
            if (item in allowed_items or item.suffix  in allowed_extensions):
                continue
            data_items.append(item)

        # If there are no data items, the directory is considered "empty"
        return len(data_items) == 0
