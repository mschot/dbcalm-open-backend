from typing import Annotated

from fastapi import APIRouter, Body, Depends
from pydantic import BaseModel

from dbcalm.api.model.response.client_response import ClientWithSecretResponse
from dbcalm.auth.verify_token import verify_token
from dbcalm.data.repository.client import ClientRepository

router = APIRouter()

class CreateClientRequest(BaseModel):
    """Request model for creating a new client."""
    label: str

@router.post(
    "/clients",
    responses={
        200: {
            "description": "Client created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "client_a1b2c3d4e5f6",
                        "secret": "secret_x9y8z7w6v5u4t3s2r1q0",
                        "label": "Production API Client",
                        "scopes": ["*"],
                    },
                },
            },
        },
    },
)
async def create_client(
    request: Annotated[
        CreateClientRequest,
        Body(
            openapi_examples={
                "production_client": {
                    "summary": "Production API client",
                    "description": "Create a client for production API access",
                    "value": {
                        "label": "Production API Client",
                    },
                },
                "backup_automation": {
                    "summary": "Backup automation client",
                    "description": "Create a client for automated backup operations",
                    "value": {
                        "label": "Backup Automation Service",
                    },
                },
            },
        ),
    ],
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
