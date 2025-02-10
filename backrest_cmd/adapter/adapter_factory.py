from backrest_cmd.adapter.adapter import Adapter
from backrest_cmd.adapter.mariadb_factory import mariadb_factory
from backrest.config.config_factory import config_factory

def adapter_factory() -> Adapter:
    config = config_factory()
    if config.value('db_type') == 'mariadb':
        return mariadb_factory(config)        
    else:
        raise ValueError('Invalid adapter type')

        
    

    