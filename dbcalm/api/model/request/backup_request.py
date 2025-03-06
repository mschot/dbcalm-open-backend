from pydantic import BaseModel


class BackupRequest(BaseModel):
    identifier: str = None
    from_identifier: str = None


