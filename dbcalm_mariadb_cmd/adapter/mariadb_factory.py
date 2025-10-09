from typing import Annotated

from fastapi import Depends

from dbcalm.config.config import Config
from dbcalm_mariadb_cmd.adapter.mariadb import Mariadb
from dbcalm_mariadb_cmd.builder.mariadb_backup_cmd_builder_factory import (
    mariadb_backup_cmd_builder_factory,
)
from dbcalm_mariadb_cmd.process.runner_factory import runner_factory


def mariadb_factory(config: Config) -> Mariadb:
    return Mariadb(
        Annotated[mariadb_backup_cmd_builder_factory, Depends()](config),
        Annotated[runner_factory, Depends()](),
    )




