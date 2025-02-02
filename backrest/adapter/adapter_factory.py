from typing import Annotated
from backrest.adapter.adapter import Adapter
from fastapi import Depends
from backrest.adapter.mariadb_factory import mariadb_factory
from backrest.config.config import Config

def adapter_factory(config: Config) -> Adapter:
    if config.value('db_type') == 'mariadb':
        return Annotated[mariadb_factory, Depends()](config)        
    else:
        raise ValueError('Invalid adapter type')

        
    

    