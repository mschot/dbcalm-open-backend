
from pydantic import BaseModel, Field


class AuthCode(BaseModel):
    code: str
    username: str
    scopes: list[str] = Field(default_factory=list)
    expires_at: int
