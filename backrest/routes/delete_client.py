from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from backrest.auth.verify_token import verify_token
from backrest.data.repository.client import ClientRepository

router = APIRouter()

@router.delete("/clients/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    _: Annotated[dict, Depends(verify_token)],
    client_id: str | None = None,
) -> None:
    client_repo = ClientRepository()

    deleted = client_repo.delete(client_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client with ID {client_id} not found",
        )
