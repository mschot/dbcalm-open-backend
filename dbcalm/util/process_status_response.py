from fastapi import Response

from dbcalm.api.model.response.status_response import StatusResponse


def process_status_response(
    process: dict,
    response: Response,
    resource_id: str | None = None,
) -> StatusResponse:
    response.status_code = process["code"]
    pid = process.get("id")
    link = f"/status/{pid}" if pid else None

    # If resource_id not provided, try to extract from process args
    if resource_id is None:
        args = process.get("args")
        if args and isinstance(args, dict):
            resource_id = args.get("id")

    return StatusResponse(
        pid = pid,
        link = link,
        status=process["status"],
        resource_id=resource_id,
    )
