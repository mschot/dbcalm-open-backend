from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException

from dbcalm.api.model.request.schedule_request import ScheduleRequest
from dbcalm.api.model.response.schedule_response import ScheduleResponse
from dbcalm.auth.verify_token import verify_token
from dbcalm.data.repository.schedule import ScheduleRepository
from dbcalm_cmd_client.client import Client

# HTTP status code for accepted async operations
HTTP_ACCEPTED = 202

router = APIRouter()


@router.put(
    "/schedules/{schedule_id}",
    responses={
        200: {
            "description": "Schedule updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "backup_type": "incremental",
                        "frequency": "daily",
                        "day_of_week": None,
                        "day_of_month": None,
                        "hour": 4,
                        "minute": 15,
                        "interval_value": None,
                        "interval_unit": None,
                        "enabled": True,
                        "created_at": "2024-10-18T10:30:00",
                        "updated_at": "2024-10-18T14:45:00",
                    },
                },
            },
        },
    },
)
async def update_schedule(
    schedule_id: int,
    request: Annotated[
        ScheduleRequest,
        Body(
            openapi_examples={
                "update_time": {
                    "summary": "Update schedule time",
                    "description": "Change daily backup time to 4:15 AM",
                    "value": {
                        "backup_type": "incremental",
                        "frequency": "daily",
                        "hour": 4,
                        "minute": 15,
                        "enabled": True,
                    },
                },
                "disable_schedule": {
                    "summary": "Disable schedule",
                    "description": "Disable a schedule without deleting it",
                    "value": {
                        "backup_type": "full",
                        "frequency": "weekly",
                        "day_of_week": 0,
                        "hour": 3,
                        "minute": 0,
                        "enabled": False,
                    },
                },
            },
        ),
    ],
    _: Annotated[dict, Depends(verify_token)],
) -> ScheduleResponse:
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
    all_schedules = schedule_repo.get_list(
        query=None,
        order=None,
        page=None,
        per_page=None,
    )[0]
    schedule_dicts = [s.model_dump(mode="json") for s in all_schedules]

    client = Client()
    response = client.command(
        "update_cron_schedules",
        {"schedules": schedule_dicts},
    )

    if response["code"] != HTTP_ACCEPTED:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to update cron schedules: "
                f"{response.get('status', 'Unknown error')}"
            ),
        )

    return ScheduleResponse(**schedule.model_dump())
