from pydantic import BaseModel


# Token request model
class TokenAuthCodeRequest(BaseModel):
    grant_type: str
    code: str
