from dbcalm.config.config_factory import config_factory
from dbcalm.data.data_types.enum_types import RestoreTarget
from dbcalm.data.model.process import Process
from dbcalm.util.get_tmp_dir import get_tmp_dir
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

    def full_backup(self, id: str) -> Process:
        command = self.command_builder.build_full_backup_cmd(id)
        return self.command_runner.execute(
            command=command,
            command_type="backup",
            args={"id": id},
        )

    def incremental_backup(self, id: str, from_backup_id: str) -> Process:
        command = self.command_builder.build_incremental_backup_cmd(
            id,
            from_backup_id,
        )
        return self.command_runner.execute(
            command=command,
            command_type="backup",
            args={"id": id, "from_backup_id": from_backup_id},
        )


    def restore_backup(self, id_list: list, target: RestoreTarget) -> Process:
        tmp_dir = get_tmp_dir(self.config.value("backup_dir"))

        commands = self.command_builder.build_restore_cmds(
            tmp_dir,
            id_list,
            target,
        )

        return self.command_runner.execute_consecutive(
            commands=commands,
            command_type="restore",
            args={"id_list": id_list},
        )
