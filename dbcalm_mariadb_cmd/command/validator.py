
import os
import subprocess
import sys
from pathlib import Path

from dbcalm.config.config_factory import config_factory
from dbcalm.data.repository.backup import BackupRepository

VALID_REQUEST = 200
INVALID_REQUEST = 400
SERVICE_UNAVAILABLE = 503
CONFLICT = 409
NOT_FOUND = 404


def get_clean_env_for_system_binaries() -> dict[str, str]:
    """Get environment for system binaries when running from PyInstaller.

    When running as a PyInstaller bundle, clear the bundled library path
    and use system libraries instead. This prevents conflicts when executing
    system binaries like mariabackup, mysqladmin, etc.
    """
    env = os.environ.copy()

    # If running from PyInstaller bundle, use system libraries
    if getattr(sys, "frozen", False):
        # Clear the PyInstaller library path
        env.pop("LD_LIBRARY_PATH", None)
        # Use system library paths
        env["LD_LIBRARY_PATH"] = "/usr/lib/x86_64-linux-gnu:/usr/lib:/lib"

    return env


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

    def _get_admin_binary(self) -> str:
        """Get the admin binary name based on db_type configuration.

        Returns:
            str: 'mysqladmin' for both MariaDB and MySQL (mysqladmin works for both)
        """
        # mysqladmin works for both MariaDB and MySQL
        # Could use mariadb-admin for MariaDB 10.5+ but mysqladmin is universal
        return "mysqladmin"

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
        backup_repo = BackupRepository()
        for arg in unique_arguments:
            if arg != "id" or not command_data["args"][arg]:
                continue

            if backup_repo.get(command_data["args"][arg]):
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
            self._get_admin_binary(),
            f"--defaults-file={credentials_file}",
            "--defaults-group-suffix=-dbcalm",
            "ping",
        ]

        result = subprocess.run(  # noqa: S603
            command,
            capture_output=True,
            text=True,
            check=False,
            env=get_clean_env_for_system_binaries(),
        )

        # If admin ping succeeds (return code 0), the server is alive
        # If it fails (non-zero return code), the server is dead
        return result.returncode != 0

    def server_alive(self) -> bool:
        credentials_file = (self.config.value("backup_credentials_file")
                if self.config.value("backup_credentials_file") is not None
                else f"/etc/{ self.config.PROJECT_NAME }/credentials.cnf")

        command = [
            self._get_admin_binary(),
            f"--defaults-file={credentials_file}",
            "--defaults-group-suffix=-dbcalm",
            "ping",
        ]

        result = subprocess.run(  # noqa: S603
            command,
            capture_output=True,
            text=True,
            check=False,
            env=get_clean_env_for_system_binaries(),
        )

        # If mysqladmin ping succeeds (return code 0), the server is alive
        # If it fails (non-zero return code), the server is dead
        return result.returncode == 0

    def data_dir_empty(self) -> bool:
        # Get data directory from config or use default
        data_dir = self.config.value("data_dir")
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
