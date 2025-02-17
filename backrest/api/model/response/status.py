from __future__ import annotations

from pydantic import BaseModel


class Status(BaseModel):
    status: str
    link: str |None = None
    pid: str | None = None

