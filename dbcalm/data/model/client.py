
from pydantic import BaseModel, Field


class Client(BaseModel):
    id: str
    secret: str
    scopes: list[str] = Field(default_factory=list)
    label: str
