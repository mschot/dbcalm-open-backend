import uuid

from passlib.context import CryptContext

from dbcalm.data.adapter.adapter_factory import adapter_factory
from dbcalm.data.model.client import Client


class ClientRepository:
    def __init__(self) -> None:
        self.key_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.adapter = adapter_factory()

    def get(self, client_id: str) -> Client | None:
        return self.adapter.get(Client, {"id" : client_id})

    def update_label(self, client_id: str, label: str) -> Client | None:
        """Update only the label of a client.
        Args:
            client_id: The ID of the client to update
            label: The new label for the client

        Returns:
            The updated client or None if not found
        """
        client = self.get(client_id)
        if client:
            client.label = label
            return self.adapter.update(client)
        return None

    def list(
            self,
            query: dict | None,
            order: dict | None,
            page: int | None = 1,
            per_page: int | None = 10,
    ) -> tuple[list[Client], int]:
        items, total = self.adapter.list(Client, query, order, page, per_page)
        return items, total

    def delete(self, client_id: str) -> bool:
        """Delete a client by ID.

        Args:
            client_id: The ID of the client to delete

        Returns:
            bool: True if client was deleted, False otherwise
        """
        return self.adapter.delete(Client, {"id": client_id})

    def create(self, label: str) -> Client:
        """Create a new client with auto-generated ID and secret.

        Args:
            label: The label for the new client

        Returns:
            The created client with generated credentials
        """
        client_id = str(uuid.uuid4())
        client_secret = str(uuid.uuid4())

        hashed_client_secret = self.key_context.hash(client_secret)

        client = Client(
            id=client_id,
            secret=hashed_client_secret,
            label=label,
            scopes=["*"],
        )

        self.adapter.create(client)

        #now set back original secret as this is the only time we'll see it
        client.secret = client_secret
        return client
