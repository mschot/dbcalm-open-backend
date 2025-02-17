from pathlib import Path

import yaml

from backrest.config.config import Config


class YamlConfig(Config):
    def value(self, key: str) -> str:
        with Path.open(self.CONFIG_PATH) as file:
            config = yaml.safe_load(file)
            value = config.get(key)
            if value is None:
                return None
            if value.lower() == "true" or value == "1" or value is True:
                return "1"
        return str(value)
