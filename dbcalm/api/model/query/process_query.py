from enum import Enum


class ProcessQueryField(str, Enum):
    """Valid fields for querying processes."""

    ID = "id"
    COMMAND = "command"
    COMMAND_ID = "command_id"
    PID = "pid"
    STATUS = "status"
    RETURN_CODE = "return_code"
    START_TIME = "start_time"
    END_TIME = "end_time"
    TYPE = "type"


class ProcessOrderField(str, Enum):
    """Valid fields for ordering processes."""

    ID = "id"
    START_TIME = "start_time"
    END_TIME = "end_time"
    STATUS = "status"
