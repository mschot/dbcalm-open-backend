from enum import Enum


class BackupQueryField(str, Enum):
    """Valid fields for querying backups."""

    ID = "id"
    FROM_BACKUP_ID = "from_backup_id"
    START_TIME = "start_time"
    END_TIME = "end_time"
    PROCESS_ID = "process_id"


class BackupOrderField(str, Enum):
    """Valid fields for ordering backups."""

    ID = "id"
    START_TIME = "start_time"
    END_TIME = "end_time"
