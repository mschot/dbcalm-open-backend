from pydantic import BaseModel, Field, field_validator


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
            msg = "frequency must be 'daily', 'weekly', 'monthly', 'hourly', or 'interval'"
            raise ValueError(msg)
        return v

    @field_validator("day_of_week")
    @classmethod
    def validate_day_of_week(cls, v: int | None) -> int | None:
        if v is not None and not 0 <= v <= 6:
            msg = "day_of_week must be between 0 and 6"
            raise ValueError(msg)
        return v

    @field_validator("day_of_month")
    @classmethod
    def validate_day_of_month(cls, v: int | None) -> int | None:
        if v is not None and not 1 <= v <= 28:
            msg = "day_of_month must be between 1 and 28"
            raise ValueError(msg)
        return v

    @field_validator("hour")
    @classmethod
    def validate_hour(cls, v: int | None) -> int | None:
        if v is not None and not 0 <= v <= 23:
            msg = "hour must be between 0 and 23"
            raise ValueError(msg)
        return v

    @field_validator("minute")
    @classmethod
    def validate_minute(cls, v: int | None) -> int | None:
        if v is not None and not 0 <= v <= 59:
            msg = "minute must be between 0 and 59"
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
