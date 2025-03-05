
from backrest.data.adapter.adapter_factory import (
    adapter_factory as data_adapter_factory,
)
from backrest.data.model.backup import Backup


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

    def validate(self, command_data: dict) -> tuple[bool, str]:
        if command_data["cmd"] not in self.commands:
            return False, "Invalid command"

        # check if all required arguments are present
        for arg in self.required_args(command_data["cmd"]):
            if arg not in command_data["args"]:
                return False, f"Missing required argument {arg}"

        # check if there are more arguments than expected
        max_args_len = len(self.commands[command_data["cmd"]])
        args_len = len(command_data["args"])
        if(max_args_len < args_len):
            return False, f"""command {command_data["cmd"]} expected {max_args_len}
                arguments but received {args_len}"""

        #check other requirements
        if self.commands[command_data["cmd"]].keys().contains("|other"):
            other_checks = self.validate_others(
                self.commands[command_data["cmd"]]["|other"],
            )
            if not other_checks[0]:
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
                    return False, f"""Backup with identifier {command_data["args"][arg]}
                        already exists"""

        return True, None
    def validate_others(self, checks: list) -> tuple[bool, str]:
        if(checks.contains("server_dead") and not self.server_dead()):
                return False, ("cannot restore to database,",
                                " MySQL/MariaDb server is not stopped")

        if (checks.contains("data_dir_empty") and not self.data_dir_empty()):
                return False, ("cannot restore to database,",
                                " mysql/mariadb data directory is not empty",
                                "(usually /var/lib/mysql)")
        return True, None


    def server_dead() -> bool:
        #CONTINUE here tomorrow using mysqladmin ping
        # mysqladmin --defaults-group-suffix=-backup
        #  --defaults-file=/etc/backrest/backup_credentials.cnf ping


        return False

    def data_dir_empty() -> bool:
        return False
