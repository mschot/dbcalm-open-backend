
from datetime import datetime

from sqlmodel import JSON, Column, Field, SQLModel


class Process(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
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
    args: dict = Field(default_factory=dict, sa_column=Column(JSON))
