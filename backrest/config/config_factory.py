from backrest.config.yaml_config import YamlConfig

config_type = 'yaml'

def config_factory():
    if config_type == 'yaml':    
        return YamlConfig()
    else:
        raise ValueError('Invalid config type')
    