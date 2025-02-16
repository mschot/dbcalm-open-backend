
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Backup(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    identifier: str
    from_identifier: Optional[str] = None
    start_time: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    end_time: Optional[datetime] = None
    
    