from dbcalm.data.data_types.enum_types import RestoreTarget
from dbcalm.data.model.restore import Restore


class RestoreRepository:
    def create(self, restore: Restore) -> None:
        from dbcalm.data.model.db_restore import DbRestore  # noqa: PLC0415

        db_restore = DbRestore(
            start_time=restore.start_time,
            end_time=restore.end_time,
            target=restore.target.value,  # Convert enum to string
            target_path=restore.target_path,
            backup_id=restore.backup_id,
            backup_timestamp=restore.backup_timestamp,
            process_id=restore.process_id,
        )
        db_restore.save()

    def get(self, restore_id: int) -> Restore | None:
        from peewee import DoesNotExist  # noqa: PLC0415

        from dbcalm.data.model.db_restore import DbRestore  # noqa: PLC0415

        try:
            db_restore = DbRestore.get_by_id(restore_id)
            return Restore(
                id=db_restore.id,
                start_time=db_restore.start_time,
                end_time=db_restore.end_time,
                target=RestoreTarget(db_restore.target),  # Convert string to enum
                target_path=db_restore.target_path,
                backup_id=db_restore.backup_id,
                backup_timestamp=db_restore.backup_timestamp,
                process_id=db_restore.process_id,
            )
        except DoesNotExist:
            return None

    def get_list(
            self,
            query: list | None,
            order: list | None,
            page: int | None = 1,
            per_page: int | None = 10,
    ) -> tuple[list[Restore], int]:
        from dbcalm.data.model.db_restore import DbRestore  # noqa: PLC0415

        # Build query
        db_query = DbRestore.select()

        # Apply filters
        if query:
            for filter_obj in query:
                field = getattr(DbRestore, filter_obj.field)
                if filter_obj.operator == "eq":
                    db_query = db_query.where(field == filter_obj.value)

        # Get total count
        total = db_query.count()

        # Apply ordering
        if order:
            for filter_obj in order:
                field = getattr(DbRestore, filter_obj.field)
                if filter_obj.operator == "desc":
                    db_query = db_query.order_by(field.desc())
                else:
                    db_query = db_query.order_by(field.asc())

        # Apply pagination
        if page and per_page:
            offset = (page - 1) * per_page
            db_query = db_query.limit(per_page).offset(offset)

        # Execute and convert
        restores = [
            Restore(
                id=db_restore.id,
                start_time=db_restore.start_time,
                end_time=db_restore.end_time,
                target=RestoreTarget(db_restore.target),
                target_path=db_restore.target_path,
                backup_id=db_restore.backup_id,
                backup_timestamp=db_restore.backup_timestamp,
                process_id=db_restore.process_id,
            )
            for db_restore in db_query
        ]

        return restores, total
