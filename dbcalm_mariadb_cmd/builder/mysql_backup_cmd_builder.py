from dbcalm.data.data_types.enum_types import RestoreTarget
from dbcalm_mariadb_cmd.builder.mariadb_backup_cmd_builder import (
    MariadbBackupCmdBuilder,
)

DEFAULT_MYSQL_BIN = "/usr/bin/xtrabackup"
DEFAULT_MYSQL_DATA_DIR = "/var/lib/mysql"


class MysqlBackupCmdBuilder(MariadbBackupCmdBuilder):
    """MySQL/Percona XtraBackup command builder.

    Inherits all command building logic from MariaDB builder since
    XtraBackup uses identical command syntax. Only the binary name differs.
    """

    def executable(self) -> str:
        """Return the backup binary path.

        Uses xtrabackup by default, but respects backup_bin config override
        for compatibility with mariabackup on Percona systems.
        """
        if self.config.value("backup_bin") is not None:
            return self.config.value("backup_bin")
        return DEFAULT_MYSQL_BIN

    def build_restore_cmds(
            self,
            tmp_dir: str,
            id_list: list,
            target: RestoreTarget,
        ) -> list:
        """Build restore commands with --datadir for XtraBackup.

        XtraBackup requires explicit --datadir parameter for copy-back operation.
        """
        # Call parent method to get all restore commands
        command_list = super().build_restore_cmds(tmp_dir, id_list, target)

        # If restoring to database, modify the copy-back command to include --datadir
        if target == RestoreTarget.DATABASE and len(command_list) > 0:
            # The copy-back command is always the last command in the list
            copy_back_cmd = command_list[-1]

            # Get data_dir from config, default to /var/lib/mysql
            data_dir = self.config.value("data_dir") or DEFAULT_MYSQL_DATA_DIR

            # Add --datadir parameter
            copy_back_cmd.append(f"--datadir={data_dir}")

        return command_list
