from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from dbcalm.auth.verify_token import verify_token
from dbcalm.data.repository.schedule import ScheduleRepository
from dbcalm.service.cron_manager import CronManager

router = APIRouter()


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(
    schedule_id: int,
    _: Annotated[dict, Depends(verify_token)],
) -> dict:
    schedule_repo = ScheduleRepository()
    schedule = schedule_repo.get(schedule_id)

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    # Remove cron file first
    cron_manager = CronManager()
    cron_manager.remove_cron_file(schedule_id)

    # Then delete from database
    schedule_repo.delete(schedule_id)

    return {"message": "Schedule deleted successfully"}
