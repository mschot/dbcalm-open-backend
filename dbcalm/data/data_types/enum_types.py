from enum import Enum


class RestoreTarget(str, Enum):
    DATABASE = "database"
    FOLDER = "folder"

class BackupType(str, Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
