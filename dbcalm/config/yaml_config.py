from pathlib import Path
from typing import Any

import yaml

from dbcalm.config.config import Config


class YamlConfig(Config):
    def value(self, key: str, default: Any = None) -> Any:  # noqa: ANN401
        with Path.open(self.CONFIG_PATH) as file:
            config = yaml.safe_load(file)
            value = config.get(key)
            if value is None:
                return default
            if isinstance(value, str) and (value.lower() == "true" or value == "1"):
                return "1"
            if value is True:
                return "1"
            return value
