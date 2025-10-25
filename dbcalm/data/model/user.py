
from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlmodel import Column, Field, SQLModel


def now() -> datetime:
    return datetime.now(tz=UTC)


class User(SQLModel, table=True):
    username: str = Field(primary_key=True, nullable=False)
    password: str = Field(nullable=False)
    created_at: datetime = Field(
        default_factory=now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
