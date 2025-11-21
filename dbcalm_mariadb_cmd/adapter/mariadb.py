from dbcalm.config.config_factory import config_factory
from dbcalm.data.data_types.enum_types import RestoreTarget
from dbcalm.util.get_tmp_dir import get_tmp_dir
from dbcalm_cmd.process.process_model import Process
from dbcalm_cmd.process.runner import Runner
from dbcalm_mariadb_cmd.adapter import adapter
from dbcalm_mariadb_cmd.builder.backup_cmd_builder import BackupCommandBuilder


class Mariadb(adapter.Adapter):
    def __init__(
            self,
            command_builder: BackupCommandBuilder,
            command_runner: Runner,
        ) -> None:
        self.command_builder = command_builder
        self.command_runner = command_runner
        self.config = config_factory()

    def full_backup(self, id: str, schedule_id: int | None = None) -> Process:
        command = self.command_builder.build_full_backup_cmd(id)
        args = {"id": id}
        if schedule_id is not None:
            args["schedule_id"] = schedule_id
        return self.command_runner.execute(
            command=command,
            command_type="backup",
            args=args,
        )

    def incremental_backup(
        self,
        id: str,
        from_backup_id: str,
        schedule_id: int | None = None,
    ) -> Process:
        command = self.command_builder.build_incremental_backup_cmd(
            id,
            from_backup_id,
        )
        args = {"id": id, "from_backup_id": from_backup_id}
        if schedule_id is not None:
            args["schedule_id"] = schedule_id
        return self.command_runner.execute(
            command=command,
            command_type="backup",
            args=args,
        )

    def restore_backup(self, id_list: list, target: RestoreTarget) -> Process:
        # Use 'restores' folder for folder restores, 'tmp' for database restores
        subdirectory = "restores" if target == RestoreTarget.FOLDER else "tmp"
        restore_dir = get_tmp_dir(self.config.value("backup_dir"), subdirectory)

        commands = self.command_builder.build_restore_cmds(
            restore_dir,
            id_list,
            target,
        )

        return self.command_runner.execute_consecutive(
            commands=commands,
            command_type="restore",
            args={"id_list": id_list, "target": target, "tmp_dir": restore_dir},
        )
