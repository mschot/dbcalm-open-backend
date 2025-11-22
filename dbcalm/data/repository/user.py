from datetime import UTC, datetime

from passlib.context import CryptContext

from dbcalm.data.model.user import User


class UserRepository:
    def __init__(self) -> None:
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def create(self, user: User) -> User:
        user.password = self.pwd_context.hash(user.password)

        from dbcalm.data.model.db_user import DbUser  # noqa: PLC0415

        # Set timestamps
        now = datetime.now(tz=UTC)
        if not user.created_at:
            user.created_at = now
        if not user.updated_at:
            user.updated_at = now

        # Create Peewee user
        db_user = DbUser(
            username=user.username,
            password=user.password,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
        db_user.save(force_insert=True)

        return user

    def get(self, username: str) -> User | None:
        from peewee import DoesNotExist  # noqa: PLC0415

        from dbcalm.data.model.db_user import DbUser  # noqa: PLC0415

        try:
            db_user = DbUser.get(DbUser.username == username)
            return User(
                username=db_user.username,
                password=db_user.password,
                created_at=db_user.created_at,
                updated_at=db_user.updated_at,
            )
        except DoesNotExist:
            return None

    def delete(self, username: str) -> bool:
        from dbcalm.data.model.db_user import DbUser  # noqa: PLC0415

        db_user = DbUser.get(DbUser.username == username)
        db_user.delete_instance()
        return True

    def update(self, user: User) -> bool:
        if user.password:
            user.password = self.pwd_context.hash(user.password)

        from dbcalm.data.model.db_user import DbUser  # noqa: PLC0415

        # Update timestamp
        user.updated_at = datetime.now(tz=UTC)

        # Get existing user and update fields
        db_user = DbUser.get(DbUser.username == user.username)
        db_user.password = user.password
        db_user.updated_at = user.updated_at
        db_user.save()
        return True

    def get_list(
        self,
        query: dict | None = None,  # noqa: ARG002
        order: dict | None = None,  # noqa: ARG002
        page: int | None = None,
        per_page: int | None = None,
    ) -> tuple[list[User], int]:
        """Get list of users."""
        from dbcalm.data.model.db_user import DbUser  # noqa: PLC0415

        # Build query - for simplicity, get all users
        db_query = DbUser.select()

        # Get total count
        total = db_query.count()

        # Apply pagination if specified
        if page and per_page:
            offset = (page - 1) * per_page
            db_query = db_query.limit(per_page).offset(offset)

        # Execute and convert
        users = [
            User(
                username=db_user.username,
                password=db_user.password,
                created_at=db_user.created_at,
                updated_at=db_user.updated_at,
            )
            for db_user in db_query
        ]

        return users, total
