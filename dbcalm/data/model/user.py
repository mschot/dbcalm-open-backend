
from datetime import UTC, datetime

from pydantic import BaseModel, Field


def now() -> datetime:
    return datetime.now(tz=UTC)


class User(BaseModel):
    username: str
    password: str
    created_at: datetime = Field(default_factory=now)
    updated_at: datetime = Field(default_factory=now)
