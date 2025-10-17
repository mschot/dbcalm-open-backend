from enum import Enum


class RestoreQueryField(str, Enum):
    """Valid fields for querying restores."""

    ID = "id"
    START_TIME = "start_time"
    END_TIME = "end_time"
    TARGET = "target"
    TARGET_PATH = "target_path"
    BACKUP_ID = "backup_id"
    BACKUP_TIMESTAMP = "backup_timestamp"
    PROCESS_ID = "process_id"


class RestoreOrderField(str, Enum):
    """Valid fields for ordering restores."""

    ID = "id"
    START_TIME = "start_time"
    END_TIME = "end_time"
    BACKUP_ID = "backup_id"
