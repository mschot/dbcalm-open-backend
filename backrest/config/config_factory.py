from backrest.config.yaml_config import YamlConfig

config_type = "yaml"

def config_factory() -> YamlConfig:
    if config_type == "yaml":
        return YamlConfig()
    msg = "Invalid config type"
    raise ValueError(msg)
