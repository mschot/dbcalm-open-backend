from backrest.data.model.process import Process
from backrest_cmd.adapter import adapter
from backrest_cmd.builder.backup_cmd_builder import BackupCommandBuilder
from backrest_cmd.command.runner import Runner


class Mariadb(adapter.Adapter):
    def __init__(
            self,
            command_builder: BackupCommandBuilder,
            command_runner: Runner,
        ) -> None:
        self.command_builder = command_builder
        self.command_runner = command_runner

    def full_backup(self, identifier: str) -> Process:
        command = self.command_builder.build_full_backup_cmd(identifier)
        return self.command_runner.execute(
            command,
            "backup",
            {"identifier": identifier},
        )

    def incremental_backup(self, identifier: str, from_identifier: str) -> Process:
        command = self.command_builder.build_incremental_backup_cmd(
            identifier,
            from_identifier,
        )
        return self.command_runner.execute(
            command,
            "backup",
            {"identifier": identifier, "from_identifier": from_identifier},
        )

    def restore(self) -> None:
        command = self.command_builder.build()
        self.command_runner.execute(command)




