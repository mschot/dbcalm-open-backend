from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from dbcalm.api.model.response.client_response import ClientWithSecretResponse
from dbcalm.auth.verify_token import verify_token
from dbcalm.data.repository.client import ClientRepository

router = APIRouter()

class CreateClientRequest(BaseModel):
    """Request model for creating a new client."""
    label: str

@router.post("/clients")
async def create_client(
    request: CreateClientRequest,
    _: Annotated[dict, Depends(verify_token)],
) -> ClientWithSecretResponse:
    """Create a new client with an auto-generated ID and secret.

    Args:
        request: The create client request containing the label
        _: The verified token payload (not used directly)

    Returns:
        A dictionary with the new client information,
        including the generated ID and secret
    """
    client_repo = ClientRepository()
    new_client = client_repo.create(request.label)

    # Return both secret and ID since this is the only time the secret will be visible
    return ClientWithSecretResponse(**new_client.model_dump())
