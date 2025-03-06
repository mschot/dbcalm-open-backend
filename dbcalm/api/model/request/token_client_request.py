from pydantic import BaseModel


# Token request model
class TokenClientRequest(BaseModel):
    grant_type: str
    client_id: str
    client_secret: str
