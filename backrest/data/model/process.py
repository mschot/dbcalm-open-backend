
from datetime import datetime
from typing import Optional

from sqlmodel import JSON, Column, Field, SQLModel


class Process(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    command: str
    pid: int
    status: str
    output: Optional[str] = None
    error: Optional[str] = None
    return_code: Optional[int] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    type: str
    args: dict = Field(default_factory=dict, sa_column=Column(JSON))
