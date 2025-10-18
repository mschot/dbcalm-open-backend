from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from dbcalm.api.model.response.schedule_response import ScheduleResponse
from dbcalm.auth.verify_token import verify_token
from dbcalm.data.repository.schedule import ScheduleRepository

router = APIRouter()


@router.get(
    "/schedules/{schedule_id}",
    responses={
        200: {
            "description": "Schedule details",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "backup_type": "full",
                        "frequency": "daily",
                        "day_of_week": None,
                        "day_of_month": None,
                        "hour": 3,
                        "minute": 0,
                        "interval_value": None,
                        "interval_unit": None,
                        "enabled": True,
                        "created_at": "2024-10-15T10:30:00",
                        "updated_at": "2024-10-15T10:30:00",
                    },
                },
            },
        },
    },
)
async def get_schedule(
    schedule_id: int,
    _: Annotated[dict, Depends(verify_token)],
) -> ScheduleResponse:
    schedule_repo = ScheduleRepository()
    schedule = schedule_repo.get(schedule_id)

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    return ScheduleResponse(**schedule.model_dump())
