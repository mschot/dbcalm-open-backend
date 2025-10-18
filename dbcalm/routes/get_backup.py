from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from dbcalm.api.model.response.backup_response import BackupResponse
from dbcalm.auth.verify_token import verify_token
from dbcalm.data.repository.backup import BackupRepository

router = APIRouter()


@router.get(
    "/backups/{backup_id}",
    responses={
        200: {
            "description": "Backup details",
            "content": {
                "application/json": {
                    "example": {
                        "id": "2024-10-18-03-00-00",
                        "from_backup_id": None,
                        "start_time": "2024-10-18T03:00:00",
                        "end_time": "2024-10-18T03:15:32",
                        "process_id": 1234,
                    },
                },
            },
        },
    },
)
async def get_backup(
    backup_id: str,
    _: Annotated[dict, Depends(verify_token)],
) -> BackupResponse:
    backup_repo = BackupRepository()
    backup = backup_repo.get(backup_id)

    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")

    return BackupResponse(**backup.model_dump())
