from pydantic import BaseModel

from dbcalm.data.data_types.enum_types import BackupType


class BackupRequest(BaseModel):
    type: BackupType
    id: str = None
    from_backup_id: str = None


