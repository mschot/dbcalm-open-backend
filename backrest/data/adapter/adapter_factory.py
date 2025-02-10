from backrest.data.adapter.adapter import Adapter
from backrest.config.config_factory import config_factory
from backrest.data.adapter.local import Local

def adapter_factory() -> Adapter:    
    config = config_factory()
    if config.value('service') is None or config.value('service') == 'sqlite':
        return Local()        
    else:
        raise ValueError('Invalid adapter type')

        
    

    