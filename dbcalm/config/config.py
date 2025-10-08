import os
from abc import ABC, abstractmethod
from typing import Any


class Config (ABC):
    PROJECT_NAME = "dbcalm"
    CONFIG_PATH = "/etc/"+ PROJECT_NAME + "/config.yml"
    CMD_SOCKET_PATH = "/var/run/"+ PROJECT_NAME + "/cmd.sock"
    DB_PATH = "/var/lib/"+ PROJECT_NAME + "/db.sqlite3"
    DB_HOST = "localhost"  # Always localhost - backup requires local filesystem access

    # Development mode can be enabled by setting DBCALM_DEV_MODE env var
    DEV_MODE = os.environ.get("DBCALM_DEV_MODE", "0") in ("1", "true", "yes")

    # Default timeout values for client commands
    DEFAULT_TIMEOUT = 5  # seconds for production
    DEV_TIMEOUT = 60     # seconds for development

    @abstractmethod
    def value(self, key: str, default: Any = None) -> Any:
        pass
