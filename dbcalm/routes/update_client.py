from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from dbcalm.api.model.response.client_response import ClientResponse
from dbcalm.auth.verify_token import verify_token
from dbcalm.data.repository.client import ClientRepository

router = APIRouter()


class UpdateClientRequest(BaseModel):
    """Request model for updating a client's label."""
    label: str


@router.put("/clients/{client_id}", status_code=status.HTTP_200_OK)
async def update_client(
    _: Annotated[dict, Depends(verify_token)],
    client_id: str,
    request: UpdateClientRequest,
) -> ClientResponse:
    """Update a client's label.

    Args:
        client_id: The ID of the client to update
        request: The update client request containing the new label
        _: The verified token payload (not used directly)

    Returns:
        A dictionary with the updated client information

    Raises:
        HTTPException: If the client could not be found
    """
    client_repo = ClientRepository()

    # First check if client exists
    client = client_repo.get(client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client with ID {client_id} not found",
        )

    # Update the client label
    updated_client = client_repo.update_label(client_id, request.label)
    if not updated_client:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update client",
        )

    # Return the updated client information (excluding secret)
    return ClientResponse(**updated_client.model_dump(exclude={"secret"}))
