from __future__ import annotations

from dbcalm.api.model.response.base_response import BaseResponse


class StatusResponse(BaseResponse):
    status: str
    link: str | None = None
    pid: str | None = None
    resource_id: str | None = None

