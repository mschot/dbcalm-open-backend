
from sqlmodel import JSON, Column, Field, SQLModel


class Client(SQLModel, table=True):
    id: str = Field(unique=True, primary_key=True)
    secret: str
    scopes: list[str] = Field(default_factory=list, sa_column=Column(JSON))
