from dbcalm.config.config import Config
from dbcalm_cmd.process.runner_factory import runner_factory
from dbcalm_mariadb_cmd.adapter.mariadb import Mariadb
from dbcalm_mariadb_cmd.builder.mariadb_backup_cmd_builder_factory import (
    mariadb_backup_cmd_builder_factory,
)


def mariadb_factory(config: Config) -> Mariadb:
    """Create MariaDB adapter with dependencies.

    Args:
        config: Application configuration

    Returns:
        Mariadb: Configured MariaDB adapter instance
    """
    return Mariadb(
        mariadb_backup_cmd_builder_factory(config),
        runner_factory(),
    )




