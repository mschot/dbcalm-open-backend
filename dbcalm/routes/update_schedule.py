from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from dbcalm.api.model.request.schedule_request import ScheduleRequest
from dbcalm.auth.verify_token import verify_token
from dbcalm.data.repository.schedule import ScheduleRepository
from dbcalm_cmd_client.client import Client

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

    schedule.backup_type = request.backup_type
    schedule.frequency = request.frequency
    schedule.day_of_week = request.day_of_week
    schedule.day_of_month = request.day_of_month
    schedule.hour = request.hour
    schedule.minute = request.minute
    schedule.interval_value = request.interval_value
    schedule.interval_unit = request.interval_unit
    schedule.enabled = request.enabled

    schedule_repo.update(schedule)

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

    return schedule.model_dump()
