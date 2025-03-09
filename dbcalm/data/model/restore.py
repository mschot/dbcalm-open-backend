# backrest/data/model/restore.py

from datetime import datetime

from sqlmodel import Field, SQLModel

from dbcalm.data.data_types.enum_types import RestoreTarget


class Restore(SQLModel, table=True):
    """Restore database model."""
    id: int | None = Field(default=None, primary_key=True)
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: datetime | None = None
    target: RestoreTarget
    target_path: str
    backup_id: int
    process_id: int


