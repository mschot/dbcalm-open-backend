from passlib.context import CryptContext

from backrest.data.adapter.adapter_factory import adapter_factory
from backrest.data.model.client import Client


class ClientRepository:
    def __init__(self) -> None:
        self.key_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.adapter = adapter_factory()

    def create(self, client: Client) -> Client:
        client.secret = self.key_context.hash(client.secret)
        return self.adapter.create(client)

    def get(self, client_id: str) -> Client | None:
        return self.adapter.get(Client, {"id" : client_id})
