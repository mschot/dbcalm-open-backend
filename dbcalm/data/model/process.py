
from datetime import datetime

from pydantic import BaseModel, Field


class Process(BaseModel):
    id: int | None = None
    command: str
    command_id: str
    pid: int
    status: str
    output: str | None = None
    error: str | None = None
    return_code: int | None = None
    start_time: datetime
    end_time: datetime | None = None
    type: str
    args: dict = Field(default_factory=dict)
