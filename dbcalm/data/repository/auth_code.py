import time

from dbcalm.data.model.auth_code import AuthCode


class AuthCodeRepository:
    def create(self, auth_code: AuthCode) -> None:
        from dbcalm.data.model.db_auth_code import DbAuthCode  # noqa: PLC0415

        db_auth_code = DbAuthCode(
            code=auth_code.code,
            username=auth_code.username,
            expires_at=auth_code.expires_at,
        )
        db_auth_code.set_scopes(auth_code.scopes)
        db_auth_code.save(force_insert=True)

    def get(self, code: str) -> AuthCode | None:
        from peewee import DoesNotExist  # noqa: PLC0415

        from dbcalm.data.model.db_auth_code import DbAuthCode  # noqa: PLC0415

        try:
            db_auth_code = DbAuthCode.get(DbAuthCode.code == code)

            # Check expiration
            if db_auth_code.expires_at < time.time():
                db_auth_code.delete_instance()
                return None

            return AuthCode(
                code=db_auth_code.code,
                username=db_auth_code.username,
                scopes=db_auth_code.get_scopes(),
                expires_at=db_auth_code.expires_at,
            )
        except DoesNotExist:
            return None
