from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from dbcalm.api.model.response.delete_response import DeleteResponse
from dbcalm.auth.verify_token import verify_token
from dbcalm.data.repository.schedule import ScheduleRepository
from dbcalm_cmd_client.client import Client

# HTTP status code for accepted async operations
HTTP_ACCEPTED = 202

router = APIRouter()


@router.delete(
    "/schedules/{schedule_id}",
    responses={
        200: {
            "description": "Schedule deleted successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Schedule deleted successfully",
                    },
                },
            },
        },
    },
)
async def delete_schedule(
    schedule_id: int,
    _: Annotated[dict, Depends(verify_token)],
) -> DeleteResponse:
    schedule_repo = ScheduleRepository()
    schedule = schedule_repo.get(schedule_id)

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    # Delete from database first
    schedule_repo.delete(schedule_id)

    # Update cron file with remaining schedules via cmd service
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

    return DeleteResponse(message="Schedule deleted successfully")
