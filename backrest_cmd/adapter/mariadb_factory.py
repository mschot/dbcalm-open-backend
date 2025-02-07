from typing import Annotated
from fastapi import Depends
from backrest_cmd.builder.mariadb_backup_cmd_builder_factory import mariadb_backup_cmd_builder_factory
from backrest_cmd.adapter.mariadb import Mariadb
from backrest_cmd.command.runner_factory import runner_factory
from backrest.config.config import Config

  
def mariadb_factory(config: Config) -> Mariadb:
    return Mariadb(
        Annotated[mariadb_backup_cmd_builder_factory, Depends()](config),
        Annotated[runner_factory, Depends()]()
    )

        

        
        