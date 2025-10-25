
from datetime import datetime

from sqlalchemy import DateTime
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
    start_time: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    end_time: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True)),
    )
    type: str
    args: dict = Field(default_factory=dict, sa_column=Column(JSON))
