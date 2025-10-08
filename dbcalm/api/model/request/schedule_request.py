from pydantic import BaseModel, Field, field_validator


class ScheduleRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    backup_type: str
    frequency: str
    day_of_week: int | None = None
    day_of_month: int | None = None
    hour: int
    minute: int
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
        if v not in ["daily", "weekly", "monthly"]:
            msg = "frequency must be 'daily', 'weekly', or 'monthly'"
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
    def validate_hour(cls, v: int) -> int:
        if not 0 <= v <= 23:
            msg = "hour must be between 0 and 23"
            raise ValueError(msg)
        return v

    @field_validator("minute")
    @classmethod
    def validate_minute(cls, v: int) -> int:
        if not 0 <= v <= 59:
            msg = "minute must be between 0 and 59"
            raise ValueError(msg)
        return v
