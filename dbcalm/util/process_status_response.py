from fastapi import Response

from dbcalm.api.model.response.status_response import StatusResponse


def process_status_response(process: dict, response: Response) -> StatusResponse:
    response.status_code = process["code"]
    pid = process.get("id")
    link = f"/status/{pid}" if pid else None

    return StatusResponse(
        pid = pid,
        link = link,
        status=process["status"],
    )
