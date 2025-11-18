from typing import Annotated

from fastapi import Depends

from dbcalm.config.config import Config
from dbcalm_cmd.process.runner_factory import runner_factory
from dbcalm_mariadb_cmd.adapter.mysql import Mysql
from dbcalm_mariadb_cmd.builder.mysql_backup_cmd_builder_factory import (
    mysql_backup_cmd_builder_factory,
)


def mysql_factory(config: Config) -> Mysql:
    """Create MySQL adapter with dependencies.

    Args:
        config: Application configuration

    Returns:
        Mysql: Configured MySQL adapter instance
    """
    return Mysql(
        Annotated[mysql_backup_cmd_builder_factory, Depends()](config),
        Annotated[runner_factory, Depends()](),
    )
