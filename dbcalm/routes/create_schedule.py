from typing import Annotated

from fastapi import APIRouter, Depends

from dbcalm.api.model.request.schedule_request import ScheduleRequest
from dbcalm.auth.verify_token import verify_token
from dbcalm.data.model.schedule import Schedule
from dbcalm.data.repository.schedule import ScheduleRepository
from dbcalm.service.cron_manager import CronManager

router = APIRouter()


@router.post("/schedules")
async def create_schedule(
    request: ScheduleRequest,
    _: Annotated[dict, Depends(verify_token)],
) -> dict:
    schedule = Schedule(
        title=request.title,
        backup_type=request.backup_type,
        frequency=request.frequency,
        day_of_week=request.day_of_week,
        day_of_month=request.day_of_month,
        hour=request.hour,
        minute=request.minute,
        enabled=request.enabled,
    )

    schedule_repo = ScheduleRepository()
    created_schedule = schedule_repo.create(schedule)

    # Create cron file
    cron_manager = CronManager()
    cron_manager.write_cron_file(created_schedule)

    return created_schedule.model_dump()
