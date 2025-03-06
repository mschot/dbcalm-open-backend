from pydantic import BaseModel


# Authorization request model
class AuthCodeRequest(BaseModel):
    client_id: str
    response_type: str = "code"
    redirect_uri: str
    state: str | None = None
