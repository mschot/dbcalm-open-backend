from backrest_cmd.adapter.adapter import Adapter
from backrest_cmd.adapter.mariadb_factory import mariadb_factory
from backrest_cmd.config.config import Config

def adapter_factory(config: Config) -> Adapter:
    if config.value('db_type') == 'mariadb':
        return mariadb_factory(config)        
    else:
        raise ValueError('Invalid adapter type')

        
    

    