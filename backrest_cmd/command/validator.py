
from pathlib import Path

from backrest.config.config_factory import config_factory
from backrest.data.adapter.adapter_factory import (
    adapter_factory as data_adapter_factory,
)
from backrest.data.model.backup import Backup

VALID_REQUEST = 200
INVALID_REQUEST = 400
PREREQUISTE_FAILED = 412
CONFLICT = 409
NOT_FOUND = 404

class Validator:
    def __init__(self) -> None:
        self.commands = {
            "full_backup": {
                "identifier": "unique|required",
            },
            "incremental_backup": {
                "identifier": "unique|required",
                "from_identifier": "required",
            },
            "restore_backup": {
                "identifier_list": "required",
                "target": "required",
                "|other": ["server_dead", "data_dir_empty"],
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

        # check if there are more arguments than expected
        max_args_len = len(self.commands[command_data["cmd"]])
        args_len = len(command_data["args"])
        if(max_args_len < args_len):
            return INVALID_REQUEST, (f"command {command_data["cmd"]}"
                f" expected {max_args_len} arguments but received {args_len}")

        #check other requirements
        if "|other" in self.commands[command_data["cmd"]]:
            other_checks = self.validate_others(
                self.commands[command_data["cmd"]]["|other"],
            )
            if other_checks[0] != VALID_REQUEST:
                return other_checks


        # In the future we could make the unique validation more generic
        # by making the argument in commands include model and field
        # for instance backup_identifier_unique that way we can find the
        # model and field to validate
        unique_arguments = self.unique_args(command_data["cmd"])
        data_adapter = data_adapter_factory()
        for arg in unique_arguments:
            if arg != "identifier" or not command_data["args"][arg]:
                continue

            if data_adapter.get(Backup, {"identifier": command_data["args"][arg]}):
                return CONFLICT, ("Backup with identifier"
                    f"{command_data["args"][arg]} already exists")

        return VALID_REQUEST, None
    def validate_others(self, checks: list) -> tuple[bool, str]:
        if "server_dead" in checks and not self.server_dead():
            return PREREQUISTE_FAILED, ("cannot restore to database,"
                            " MySQL/MariaDb server is not stopped")

        if "data_dir_empty" in checks and not self.data_dir_empty():
            return PREREQUISTE_FAILED, ("cannot restore to database,"
                            " mysql/mariadb data directory is not empty"
                            "(usually /var/lib/mysql)")

        return VALID_REQUEST, None


    def server_dead(self) -> bool:
        from backrest_cmd.process.runner_factory import runner_factory

        command = [
            "mysqladmin",
            "--defaults-group-suffix=-backup",
            "--defaults-file=/etc/backrest/backup_credentials.cnf",
            "ping",
        ]

        runner = runner_factory()
        _, queue = runner.execute(
            command=command,
            command_type="mysql_ping_check",
            args={"check_type": "server_dead"},
        )

        # Wait for the command to complete
        completed_process = queue.get()

        # If mysqladmin ping succeeds (return code 0), the server is alive
        # If it fails (non-zero return code), the server is dead
        return completed_process.return_code != 0

    def data_dir_empty(self) -> bool:
        # Get data directory from config or use default
        config = config_factory()
        data_dir = config.value("mysql_data_dir")
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
