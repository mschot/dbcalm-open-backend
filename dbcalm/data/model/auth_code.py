
from sqlmodel import JSON, Column, Field, SQLModel


class AuthCode(SQLModel, table=True):
    code: str = Field(unique=True, primary_key=True)
    username: str
    scopes: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    expires_at: int
