from dbcalm.data.model.backup import Backup
from dbcalm.errors.not_found_error import NotFoundError


class BackupRepository:
    def create(self, backup: Backup) -> None:
        from dbcalm.data.model.db_backup import DbBackup  # noqa: PLC0415

        db_backup = DbBackup(
            id=backup.id,
            from_backup_id=backup.from_backup_id,
            schedule_id=backup.schedule_id,
            start_time=backup.start_time,
            end_time=backup.end_time,
            process_id=backup.process_id,
        )
        db_backup.save(force_insert=True)

    def get(self, id: str) -> Backup | None:
        from peewee import DoesNotExist  # noqa: PLC0415

        from dbcalm.data.model.db_backup import DbBackup  # noqa: PLC0415

        try:
            db_backup = DbBackup.get(DbBackup.id == id)
            return Backup(
                id=db_backup.id,
                from_backup_id=db_backup.from_backup_id,
                schedule_id=db_backup.schedule_id,
                start_time=db_backup.start_time,
                end_time=db_backup.end_time,
                process_id=db_backup.process_id,
            )
        except DoesNotExist:
            return None

    def get_list(
            self,
            query: list | None,
            order: list | None,
            page: int | None = 1,
            per_page: int | None = 10,
    ) -> tuple[list[Backup], int]:
        from dbcalm.data.model.db_backup import DbBackup  # noqa: PLC0415

        # Build query
        db_query = DbBackup.select()

        # Apply filters
        if query:
            for filter_obj in query:
                field = getattr(DbBackup, filter_obj.field)
                if filter_obj.operator == "eq":
                    db_query = db_query.where(field == filter_obj.value)
                elif filter_obj.operator == "isnull":
                    db_query = db_query.where(field.is_null())
                elif filter_obj.operator == "isnotnull":
                    db_query = db_query.where(field.is_null(is_null=False))

        # Get total count
        total = db_query.count()

        # Apply ordering
        if order:
            for filter_obj in order:
                field = getattr(DbBackup, filter_obj.field)
                if filter_obj.operator == "desc":
                    db_query = db_query.order_by(field.desc())
                else:
                    db_query = db_query.order_by(field.asc())

        # Apply pagination
        if page and per_page:
            offset = (page - 1) * per_page
            db_query = db_query.limit(per_page).offset(offset)

        # Execute and convert
        backups = [
            Backup(
                id=db_backup.id,
                from_backup_id=db_backup.from_backup_id,
                schedule_id=db_backup.schedule_id,
                start_time=db_backup.start_time,
                end_time=db_backup.end_time,
                process_id=db_backup.process_id,
            )
            for db_backup in db_query
        ]

        return backups, total

    def required_backups(self, backup: Backup) -> list:
        required_backups = [backup.id]
        current = backup
        while current.from_backup_id:
            prev_backup = self.get(current.from_backup_id)
            if prev_backup:
                required_backups.append(prev_backup.id)
                current = prev_backup
            else:
                msg = f"Backup with id {current.from_backup_id} not found"
                raise NotFoundError(msg)

        required_backups.reverse()
        return required_backups

    def latest_backup(self) -> Backup | None:
        from peewee import DoesNotExist  # noqa: PLC0415

        from dbcalm.data.model.db_backup import DbBackup  # noqa: PLC0415

        try:
            db_backup = (
                DbBackup.select()
                .order_by(DbBackup.end_time.desc())
                .limit(1)
                .get()
            )
            return Backup(
                id=db_backup.id,
                from_backup_id=db_backup.from_backup_id,
                schedule_id=db_backup.schedule_id,
                start_time=db_backup.start_time,
                end_time=db_backup.end_time,
                process_id=db_backup.process_id,
            )
        except DoesNotExist:
            return None

    def delete(self, backup_id: str) -> bool:
        """Delete a backup by ID."""
        from dbcalm.data.model.db_backup import DbBackup  # noqa: PLC0415

        db_backup = DbBackup.get(DbBackup.id == backup_id)
        db_backup.delete_instance()
        return True
