from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from dbcalm.api.model.response.schedule_response import ScheduleResponse
from dbcalm.auth.verify_token import verify_token
from dbcalm.data.repository.schedule import ScheduleRepository

router = APIRouter()


@router.get("/schedules/{schedule_id}")
async def get_schedule(
    schedule_id: int,
    _: Annotated[dict, Depends(verify_token)],
) -> ScheduleResponse:
    schedule_repo = ScheduleRepository()
    schedule = schedule_repo.get(schedule_id)

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    return ScheduleResponse(**schedule.model_dump())
