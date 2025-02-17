
from backrest.config.config import Config
from backrest_cmd.builder.mariadb_backup_cmd_builder import MariadbBackupCmdBuilder


def mariadb_backup_cmd_builder_factory(config: Config) -> MariadbBackupCmdBuilder:

    return MariadbBackupCmdBuilder(config)



