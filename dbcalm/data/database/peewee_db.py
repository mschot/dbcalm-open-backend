"""Peewee database configuration.

This module provides the Peewee database instance that will be used
by Peewee models.
"""

from peewee import SqliteDatabase

from dbcalm.config.config import Config

# Create database instance
db = SqliteDatabase(Config.DB_PATH)


def create_tables() -> None:
    """Create all database tables if they don't exist.

    Uses safe=True to prevent errors if tables already exist.
    """
    from dbcalm.data.model.db_auth_code import DbAuthCode  # noqa: PLC0415
    from dbcalm.data.model.db_backup import DbBackup  # noqa: PLC0415
    from dbcalm.data.model.db_client import DbClient  # noqa: PLC0415
    from dbcalm.data.model.db_process import DbProcess  # noqa: PLC0415
    from dbcalm.data.model.db_restore import DbRestore  # noqa: PLC0415
    from dbcalm.data.model.db_schedule import DbSchedule  # noqa: PLC0415
    from dbcalm.data.model.db_user import DbUser  # noqa: PLC0415

    db.create_tables(
        [
            DbUser,
            DbClient,
            DbAuthCode,
            DbBackup,
            DbRestore,
            DbSchedule,
            DbProcess,
        ],
        safe=True,
    )


def init_db() -> None:
    """Initialize database connection and create tables.

    This ensures the database connection is ready and all tables exist.
    Should be called on application startup.
    """
    db.connect(reuse_if_open=True)
    create_tables()


def close_db() -> None:
    """Close database connection.

    Should be called on application shutdown.
    """
    if not db.is_closed():
        db.close()
