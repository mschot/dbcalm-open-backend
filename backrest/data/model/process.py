
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

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