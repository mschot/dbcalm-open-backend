from pydantic import BaseModel, field_validator

# Constants for validation
MAX_DAY_OF_WEEK = 6
MAX_DAY_OF_MONTH = 28
MAX_HOUR = 23
MAX_MINUTE = 59


class ScheduleRequest(BaseModel):
    backup_type: str
    frequency: str
    day_of_week: int | None = None
    day_of_month: int | None = None
    hour: int | None = None
    minute: int | None = None
    interval_value: int | None = None
    interval_unit: str | None = None
    enabled: bool = True

    @field_validator("backup_type")
    @classmethod
    def validate_backup_type(cls, v: str) -> str:
        if v not in ["full", "incremental"]:
            msg = "backup_type must be 'full' or 'incremental'"
            raise ValueError(msg)
        return v

    @field_validator("frequency")
    @classmethod
    def validate_frequency(cls, v: str) -> str:
        if v not in ["daily", "weekly", "monthly", "hourly", "interval"]:
            msg = (
                "frequency must be 'daily', 'weekly', 'monthly', "
                "'hourly', or 'interval'"
            )
            raise ValueError(msg)
        return v

    @field_validator("day_of_week")
    @classmethod
    def validate_day_of_week(cls, v: int | None) -> int | None:
        if v is not None and not 0 <= v <= MAX_DAY_OF_WEEK:
            msg = f"day_of_week must be between 0 and {MAX_DAY_OF_WEEK}"
            raise ValueError(msg)
        return v

    @field_validator("day_of_month")
    @classmethod
    def validate_day_of_month(cls, v: int | None) -> int | None:
        if v is not None and not 1 <= v <= MAX_DAY_OF_MONTH:
            msg = f"day_of_month must be between 1 and {MAX_DAY_OF_MONTH}"
            raise ValueError(msg)
        return v

    @field_validator("hour")
    @classmethod
    def validate_hour(cls, v: int | None) -> int | None:
        if v is not None and not 0 <= v <= MAX_HOUR:
            msg = f"hour must be between 0 and {MAX_HOUR}"
            raise ValueError(msg)
        return v

    @field_validator("minute")
    @classmethod
    def validate_minute(cls, v: int | None) -> int | None:
        if v is not None and not 0 <= v <= MAX_MINUTE:
            msg = f"minute must be between 0 and {MAX_MINUTE}"
            raise ValueError(msg)
        return v

    @field_validator("interval_value")
    @classmethod
    def validate_interval_value(cls, v: int | None) -> int | None:
        if v is not None and v <= 0:
            msg = "interval_value must be greater than 0"
            raise ValueError(msg)
        return v

    @field_validator("interval_unit")
    @classmethod
    def validate_interval_unit(cls, v: str | None) -> str | None:
        if v is not None and v not in ["minutes", "hours"]:
            msg = "interval_unit must be 'minutes' or 'hours'"
            raise ValueError(msg)
        return v
