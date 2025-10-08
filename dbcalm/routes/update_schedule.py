from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from dbcalm.api.model.request.schedule_request import ScheduleRequest
from dbcalm.auth.verify_token import verify_token
from dbcalm.data.repository.schedule import ScheduleRepository
from dbcalm.service.cron_manager import CronManager

router = APIRouter()


@router.put("/schedules/{schedule_id}")
async def update_schedule(
    schedule_id: int,
    request: ScheduleRequest,
    _: Annotated[dict, Depends(verify_token)],
) -> dict:
    schedule_repo = ScheduleRepository()
    schedule = schedule_repo.get(schedule_id)

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    schedule.title = request.title
    schedule.backup_type = request.backup_type
    schedule.frequency = request.frequency
    schedule.day_of_week = request.day_of_week
    schedule.day_of_month = request.day_of_month
    schedule.hour = request.hour
    schedule.minute = request.minute
    schedule.enabled = request.enabled

    schedule_repo.update(schedule)

    # Update cron file (or remove if disabled)
    cron_manager = CronManager()
    cron_manager.write_cron_file(schedule)

    return schedule.model_dump()
