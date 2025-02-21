from passlib.context import CryptContext

from backrest.data.adapter.adapter_factory import adapter_factory
from backrest.data.model.user import User


class UserRepository:
    def __init__(self) -> None:
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.adapter = adapter_factory()

    def create(self, user: User) -> User:
        user.password = self.pwd_context.hash(user.password)
        return self.adapter.create(user)

    def get(self, username: str) -> User | None:
        return self.adapter.get(User, {"username" : username})
