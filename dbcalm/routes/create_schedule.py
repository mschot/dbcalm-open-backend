from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException

from dbcalm.api.model.request.schedule_request import ScheduleRequest
from dbcalm.api.model.response.schedule_response import ScheduleResponse
from dbcalm.auth.verify_token import verify_token
from dbcalm.data.model.schedule import Schedule
from dbcalm.data.repository.schedule import ScheduleRepository
from dbcalm_cmd_client.client import Client

# HTTP status code for accepted async operations
HTTP_ACCEPTED = 202

router = APIRouter()


@router.post(
    "/schedules",
    responses={
        200: {
            "description": "Schedule created successfully",
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
                        "created_at": "2024-10-18T10:30:00",
                        "updated_at": "2024-10-18T10:30:00",
                    },
                },
            },
        },
    },
)
async def create_schedule(
    request: Annotated[
        ScheduleRequest,
        Body(
            openapi_examples={
                "daily_full_backup": {
                    "summary": "Daily full backup at 3:00 AM",
                    "description": "Schedule a daily full backup at 3:00 AM",
                    "value": {
                        "backup_type": "full",
                        "frequency": "daily",
                        "hour": 3,
                        "minute": 0,
                        "enabled": True,
                    },
                },
                "weekly_incremental_backup": {
                    "summary": "Weekly incremental backup on Sundays",
                    "description": (
                        "Schedule incremental backup every Sunday at 3:30 AM"
                    ),
                    "value": {
                        "backup_type": "incremental",
                        "frequency": "weekly",
                        "day_of_week": 0,
                        "hour": 3,
                        "minute": 30,
                        "enabled": True,
                    },
                },
                "monthly_backup": {
                    "summary": "Monthly backup on 1st at midnight",
                    "description": "Schedule monthly full backup on 1st day at 00:00",
                    "value": {
                        "backup_type": "full",
                        "frequency": "monthly",
                        "day_of_month": 1,
                        "hour": 0,
                        "minute": 0,
                        "enabled": True,
                    },
                },
                "interval_backup": {
                    "summary": "Every 4 hours incremental backup",
                    "description": "Schedule incremental backup every 4 hours",
                    "value": {
                        "backup_type": "incremental",
                        "frequency": "interval",
                        "interval_value": 4,
                        "interval_unit": "hours",
                        "enabled": True,
                    },
                },
            },
        ),
    ],
    _: Annotated[dict, Depends(verify_token)],
) -> ScheduleResponse:
    schedule_repo = ScheduleRepository()

    # Validate: incremental schedules require at least one enabled full backup schedule
    if request.backup_type == "incremental":
        from dbcalm.util.parse_query_with_operators import QueryFilter  # noqa: PLC0415

        full_schedules = schedule_repo.get_list(
            query=[
                QueryFilter(field="backup_type", operator="eq", value="full"),
                QueryFilter(field="enabled", operator="eq", value="true"),
            ],
            order=None,
            page=None,
            per_page=None,
        )[0]

        if not full_schedules:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Cannot create incremental backup schedule without at least "
                    "one enabled full backup schedule"
                ),
            )

    schedule = Schedule(
        backup_type=request.backup_type,
        frequency=request.frequency,
        day_of_week=request.day_of_week,
        day_of_month=request.day_of_month,
        hour=request.hour,
        minute=request.minute,
        interval_value=request.interval_value,
        interval_unit=request.interval_unit,
        retention_value=request.retention_value,
        retention_unit=request.retention_unit,
        enabled=request.enabled,
    )

    created_schedule = schedule_repo.create(schedule)

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

    return ScheduleResponse(**created_schedule.model_dump())
