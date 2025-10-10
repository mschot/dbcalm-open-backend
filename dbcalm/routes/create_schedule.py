from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from dbcalm.api.model.request.schedule_request import ScheduleRequest
from dbcalm.auth.verify_token import verify_token
from dbcalm.data.model.schedule import Schedule
from dbcalm.data.repository.schedule import ScheduleRepository
from dbcalm_cmd_client.client import Client

router = APIRouter()


@router.post("/schedules")
async def create_schedule(
    request: ScheduleRequest,
    _: Annotated[dict, Depends(verify_token)],
) -> dict:
    schedule = Schedule(
        backup_type=request.backup_type,
        frequency=request.frequency,
        day_of_week=request.day_of_week,
        day_of_month=request.day_of_month,
        hour=request.hour,
        minute=request.minute,
        interval_value=request.interval_value,
        interval_unit=request.interval_unit,
        enabled=request.enabled,
    )

    schedule_repo = ScheduleRepository()
    created_schedule = schedule_repo.create(schedule)

    # Update cron file with all schedules via cmd service
    all_schedules = schedule_repo.get_list(query=None, order=None, page=None, per_page=None)[0]
    schedule_dicts = [s.model_dump(mode='json') for s in all_schedules]

    client = Client()
    response = client.command("update_cron_schedules", {"schedules": schedule_dicts})

    if response["code"] != 202:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update cron schedules: {response.get('status', 'Unknown error')}",
        )

    return created_schedule.model_dump()
