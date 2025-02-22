import os
import tempfile

from backrest.config.config_factory import config_factory
from backrest.data.model.process import Process
from backrest_cmd.adapter import adapter
from backrest_cmd.builder.backup_cmd_builder import BackupCommandBuilder
from backrest_cmd.process.runner import Runner


class Mariadb(adapter.Adapter):
    def __init__(
            self,
            command_builder: BackupCommandBuilder,
            command_runner: Runner,
        ) -> None:
        self.command_builder = command_builder
        self.command_runner = command_runner
        self.config = config_factory()

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

    def restore_backup(self, identifier_list: list) -> Process:
        full_backup_identifier = identifier_list[0]
        base_dir = f"{self.config.value('backup_dir')}/{full_backup_identifier}"
        with tempfile.TemporaryDirectory(delete=False) as tmp_dir:
           os.system(f"cp -r {base_dir} {tmp_dir}/")  # noqa: S605

        commands = self.command_builder.build_restore_cmds(
            f"{tmp_dir}/{full_backup_identifier}",
            identifier_list,
        )

        return self.command_runner.execute_consecutive(
            commands,
            "restore",
            {"identifier_list": identifier_list},
        )





