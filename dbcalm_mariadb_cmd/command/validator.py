
import subprocess
from pathlib import Path

from dbcalm.config.config_factory import config_factory
from dbcalm.data.adapter.adapter_factory import (
    adapter_factory as data_adapter_factory,
)
from dbcalm.data.model.backup import Backup

VALID_REQUEST = 200
INVALID_REQUEST = 400
SERVICE_UNAVAILABLE = 503
CONFLICT = 409
NOT_FOUND = 404

class Validator:
    def __init__(self) -> None:
        self.config = config_factory()
        self.commands = {
            "full_backup": {
                "id": "unique|required",
                "|backup": ["server_alive"],
            },
            "incremental_backup": {
                "id": "unique|required",
                "from_backup_id": "required",
                "|backup": ["server_alive"],
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

    def _validate_required_args(self, command_data: dict) -> tuple[int, str]:
        """Check if all required arguments are present."""
        for arg in self.required_args(command_data["cmd"]):
            if arg not in command_data["args"]:
                return INVALID_REQUEST, f"Missing required argument {arg}"
        return VALID_REQUEST, ""

    def _validate_backup_checks(self, command_data: dict) -> tuple[int, str]:
        """Validate backup-specific requirements."""
        if "|backup" not in self.commands[command_data["cmd"]]:
            return VALID_REQUEST, ""

        other_checks = self.backup(
            self.commands[command_data["cmd"]]["|backup"],
        )
        if other_checks[0] != VALID_REQUEST:
            return other_checks

        return VALID_REQUEST, ""

    def _validate_database_restore_checks(self, command_data: dict) -> tuple[int, str]:
        """Validate database restore requirements."""
        if (
            "|database_restore" not in self.commands[command_data["cmd"]]
            or command_data["args"]["target"] != "database"
        ):
            return VALID_REQUEST, ""

        other_checks = self.database_restore(
            self.commands[command_data["cmd"]]["|database_restore"],
        )
        if other_checks[0] != VALID_REQUEST:
            return other_checks

        return VALID_REQUEST, ""

    def _validate_unique_constraints(self, command_data: dict) -> tuple[int, str]:
        """Validate unique constraints for arguments."""
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
                return CONFLICT, (
                    f"Backup with id {command_data['args'][arg]} already exists"
                )

        return VALID_REQUEST, ""

    def validate(self, command_data: dict) -> tuple[int, str]:
        if command_data["cmd"] not in self.commands:
            return INVALID_REQUEST, "Invalid command"

        validators = [
            self._validate_required_args,
            self._validate_backup_checks,
            self._validate_database_restore_checks,
            self._validate_unique_constraints,
        ]

        for validator in validators:
            status, message = validator(command_data)
            if status != VALID_REQUEST:
                return status, message

        return VALID_REQUEST, ""

    def credentials_file_valid(self) -> bool:
        """Check if credentials file exists and has [client-dbcalm] section."""
        credentials_file = (
            self.config.value("backup_credentials_file")
            if self.config.value("backup_credentials_file") is not None
            else f"/etc/{self.config.PROJECT_NAME}/credentials.cnf"
        )

        credentials_path = Path(credentials_file)

        # Check if file exists
        if not credentials_path.is_file():
            return False

        try:
            # Read file and check for [client-dbcalm] section
            content = credentials_path.read_text()
        except (PermissionError, OSError):
            return False
        else:
            return "[client-dbcalm]" in content

    def backup(self, checks: list) -> tuple[int, str]:
        if not self.credentials_file_valid():
            return SERVICE_UNAVAILABLE, (
                "credentials file not found or missing [client-dbcalm] section"
            )

        if "server_alive" in checks and not self.server_alive():
            return SERVICE_UNAVAILABLE, (
                "cannot create backup, MySQL/MariaDB server is not running"
            )

        return VALID_REQUEST, ""

    def database_restore(self, checks: list) -> tuple[int, str]:
        if not self.credentials_file_valid():
            return SERVICE_UNAVAILABLE, (
                "credentials file not found or missing [client-dbcalm] section"
            )

        if "server_dead" in checks and not self.server_dead():
            return SERVICE_UNAVAILABLE, (
                "cannot restore to database, MySQL/MariaDb server is not stopped"
            )

        if "data_dir_empty" in checks and not self.data_dir_empty():
            return SERVICE_UNAVAILABLE, (
                "cannot restore to database, mysql/mariadb data directory is not empty "
                "(usually /var/lib/mysql)"
            )

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

    def server_alive(self) -> bool:
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
        return result.returncode == 0

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
