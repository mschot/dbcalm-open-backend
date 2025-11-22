import uuid

from passlib.context import CryptContext

from dbcalm.data.model.client import Client


class ClientRepository:
    def __init__(self) -> None:
        self.key_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def get(self, client_id: str) -> Client | None:
        from peewee import DoesNotExist  # noqa: PLC0415

        from dbcalm.data.model.db_client import DbClient  # noqa: PLC0415

        try:
            db_client = DbClient.get(DbClient.id == client_id)
            return Client(
                id=db_client.id,
                secret=db_client.secret,
                scopes=db_client.get_scopes(),
                label=db_client.label,
            )
        except DoesNotExist:
            return None

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
            return self.update(client)
        return None

    def get_list(
            self,
            query: list | None,
            order: list | None,
            page: int | None = 1,
            per_page: int | None = 10,
    ) -> tuple[list[Client], int]:
        from dbcalm.data.model.db_client import DbClient  # noqa: PLC0415

        # Build query
        db_query = DbClient.select()

        # Apply filters
        if query:
            for filter_obj in query:
                field = getattr(DbClient, filter_obj.field)
                if filter_obj.operator == "eq":
                    db_query = db_query.where(field == filter_obj.value)

        # Get total count
        total = db_query.count()

        # Apply ordering
        if order:
            for filter_obj in order:
                field = getattr(DbClient, filter_obj.field)
                if filter_obj.operator == "desc":
                    db_query = db_query.order_by(field.desc())
                else:
                    db_query = db_query.order_by(field.asc())

        # Apply pagination
        if page and per_page:
            offset = (page - 1) * per_page
            db_query = db_query.limit(per_page).offset(offset)

        # Execute and convert
        clients = [
            Client(
                id=db_client.id,
                secret=db_client.secret,
                scopes=db_client.get_scopes(),
                label=db_client.label,
            )
            for db_client in db_query
        ]

        return clients, total

    def delete(self, client_id: str) -> bool:
        """Delete a client by ID.

        Args:
            client_id: The ID of the client to delete

        Returns:
            bool: True if client was deleted, False otherwise
        """
        from dbcalm.data.model.db_client import DbClient  # noqa: PLC0415

        db_client = DbClient.get(DbClient.id == client_id)
        db_client.delete_instance()
        return True

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

        from dbcalm.data.model.db_client import DbClient  # noqa: PLC0415

        db_client = DbClient(
            id=client.id,
            secret=client.secret,
            label=client.label,
        )
        db_client.set_scopes(client.scopes)
        db_client.save(force_insert=True)

        #now set back original secret as this is the only time we'll see it
        client.secret = client_secret
        return client

    def update(self, client: Client) -> Client:
        """Update client using Peewee."""
        from dbcalm.data.model.db_client import DbClient  # noqa: PLC0415

        db_client = DbClient.get(DbClient.id == client.id)
        db_client.secret = client.secret
        db_client.label = client.label
        db_client.set_scopes(client.scopes)
        db_client.save()
        return client
