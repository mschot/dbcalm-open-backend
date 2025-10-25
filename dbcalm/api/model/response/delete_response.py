from pydantic import Field

from dbcalm.api.model.response.base_response import BaseResponse


class DeleteResponse(BaseResponse):
    """Generic response for successful deletion."""

    message: str = Field(description="Confirmation message")
