from pydantic import BaseModel

from dbcalm.data.data_types.enum_types import BackupType


class BackupRequest(BaseModel):
    type: BackupType
    identifier: str = None
    from_identifier: str = None


