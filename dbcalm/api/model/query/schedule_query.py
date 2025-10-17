from enum import Enum


class ScheduleQueryField(str, Enum):
    """Valid fields for querying schedules."""

    ID = "id"
    BACKUP_TYPE = "backup_type"
    FREQUENCY = "frequency"
    DAY_OF_WEEK = "day_of_week"
    DAY_OF_MONTH = "day_of_month"
    HOUR = "hour"
    MINUTE = "minute"
    INTERVAL_VALUE = "interval_value"
    INTERVAL_UNIT = "interval_unit"
    ENABLED = "enabled"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class ScheduleOrderField(str, Enum):
    """Valid fields for ordering schedules."""

    ID = "id"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    ENABLED = "enabled"
