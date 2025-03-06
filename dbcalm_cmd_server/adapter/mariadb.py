import uuid
from pathlib import Path

from dbcalm.config.config_factory import config_factory
from dbcalm.data.model.process import Process
from dbcalm.data.types.enum_types import RestoreTarget
from dbcalm_cmd_server.adapter import adapter
from dbcalm_cmd_server.builder.backup_cmd_builder import BackupCommandBuilder
from dbcalm_cmd_server.process.runner import Runner


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
            command=command,
            command_type="backup",
            args={"identifier": identifier},
        )

    def incremental_backup(self, identifier: str, from_identifier: str) -> Process:
        command = self.command_builder.build_incremental_backup_cmd(
            identifier,
            from_identifier,
        )
        return self.command_runner.execute(
            command=command,
            command_type="backup",
            args={"identifier": identifier, "from_identifier": from_identifier},
        )

    def get_tmp_dir(self) -> str:
        tmp_dir = self.config.value("backup_dir") + "/tmp/" + str(uuid.uuid4())  # noqa: S108
        path = Path(tmp_dir)
        path.mkdir(parents=True, exist_ok=True)
        return tmp_dir


    def restore_backup(self, identifier_list: list, target: RestoreTarget) -> Process:
        tmp_dir = self.get_tmp_dir()

        commands = self.command_builder.build_restore_cmds(
            tmp_dir,
            identifier_list,
            target,
        )

        return self.command_runner.execute_consecutive(
            commands=commands,
            command_type="restore",
            args={"identifier_list": identifier_list},
        )
