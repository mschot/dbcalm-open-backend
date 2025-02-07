from backrest_cmd.config.yaml_config import YamlConfig


def config_factory(config_type):
    if config_type == 'yaml':    
        return YamlConfig()
    else:
        raise ValueError('Invalid config type')
    