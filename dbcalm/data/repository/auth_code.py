import time

from dbcalm.data.adapter.adapter_factory import adapter_factory
from dbcalm.data.model.auth_code import AuthCode


class AuthCodeRepository:
    def __init__(self) -> None:
        self.adapter = adapter_factory()

    def create(self, auth_code: AuthCode) -> None:
        return self.adapter.create(auth_code)

    def get(self, code: str) -> AuthCode | None:
        auth_code = self.adapter.get(AuthCode, {"code":code})
        if auth_code is None:
            return None
        if auth_code.expires_at < time.time():
            self.adapter.delete(auth_code)
            return None

        return auth_code







