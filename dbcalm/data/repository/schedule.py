from datetime import UTC, datetime

from dbcalm.data.model.schedule import Schedule


class ScheduleRepository:
    def create(self, schedule: Schedule) -> Schedule:
        schedule.created_at = datetime.now(tz=UTC)
        schedule.updated_at = datetime.now(tz=UTC)

        from dbcalm.data.model.db_schedule import DbSchedule  # noqa: PLC0415

        db_schedule = DbSchedule(
            backup_type=schedule.backup_type,
            frequency=schedule.frequency,
            day_of_week=schedule.day_of_week,
            day_of_month=schedule.day_of_month,
            hour=schedule.hour,
            minute=schedule.minute,
            interval_value=schedule.interval_value,
            interval_unit=schedule.interval_unit,
            retention_value=schedule.retention_value,
            retention_unit=schedule.retention_unit,
            enabled=schedule.enabled,
            created_at=schedule.created_at,
            updated_at=schedule.updated_at,
        )
        db_schedule.save()
        schedule.id = db_schedule.id
        return schedule

    def get(self, schedule_id: int) -> Schedule | None:
        from peewee import DoesNotExist  # noqa: PLC0415

        from dbcalm.data.model.db_schedule import DbSchedule  # noqa: PLC0415

        try:
            db_schedule = DbSchedule.get_by_id(schedule_id)
            return Schedule(
                id=db_schedule.id,
                backup_type=db_schedule.backup_type,
                frequency=db_schedule.frequency,
                day_of_week=db_schedule.day_of_week,
                day_of_month=db_schedule.day_of_month,
                hour=db_schedule.hour,
                minute=db_schedule.minute,
                interval_value=db_schedule.interval_value,
                interval_unit=db_schedule.interval_unit,
                retention_value=db_schedule.retention_value,
                retention_unit=db_schedule.retention_unit,
                enabled=db_schedule.enabled,
                created_at=db_schedule.created_at,
                updated_at=db_schedule.updated_at,
            )
        except DoesNotExist:
            return None

    def get_list(
        self,
        query: list | None,
        order: list | None,
        page: int | None = 1,
        per_page: int | None = 25,
    ) -> tuple[list[Schedule], int]:
        from dbcalm.data.model.db_schedule import DbSchedule  # noqa: PLC0415

        # Build query
        db_query = DbSchedule.select()

        # Apply filters
        if query:
            for filter_obj in query:
                field = getattr(DbSchedule, filter_obj.field)
                if filter_obj.operator == "eq":
                    db_query = db_query.where(field == filter_obj.value)

        # Get total count
        total = db_query.count()

        # Apply ordering
        if order:
            for filter_obj in order:
                field = getattr(DbSchedule, filter_obj.field)
                if filter_obj.operator == "desc":
                    db_query = db_query.order_by(field.desc())
                else:
                    db_query = db_query.order_by(field.asc())

        # Apply pagination
        if page and per_page:
            offset = (page - 1) * per_page
            db_query = db_query.limit(per_page).offset(offset)

        # Execute and convert
        schedules = [
            Schedule(
                id=db_schedule.id,
                backup_type=db_schedule.backup_type,
                frequency=db_schedule.frequency,
                day_of_week=db_schedule.day_of_week,
                day_of_month=db_schedule.day_of_month,
                hour=db_schedule.hour,
                minute=db_schedule.minute,
                interval_value=db_schedule.interval_value,
                interval_unit=db_schedule.interval_unit,
                retention_value=db_schedule.retention_value,
                retention_unit=db_schedule.retention_unit,
                enabled=db_schedule.enabled,
                created_at=db_schedule.created_at,
                updated_at=db_schedule.updated_at,
            )
            for db_schedule in db_query
        ]

        return schedules, total

    def update(self, schedule: Schedule) -> bool:
        schedule.updated_at = datetime.now(tz=UTC)

        from dbcalm.data.model.db_schedule import DbSchedule  # noqa: PLC0415

        db_schedule = DbSchedule.get_by_id(schedule.id)
        db_schedule.backup_type = schedule.backup_type
        db_schedule.frequency = schedule.frequency
        db_schedule.day_of_week = schedule.day_of_week
        db_schedule.day_of_month = schedule.day_of_month
        db_schedule.hour = schedule.hour
        db_schedule.minute = schedule.minute
        db_schedule.interval_value = schedule.interval_value
        db_schedule.interval_unit = schedule.interval_unit
        db_schedule.retention_value = schedule.retention_value
        db_schedule.retention_unit = schedule.retention_unit
        db_schedule.enabled = schedule.enabled
        db_schedule.updated_at = schedule.updated_at
        db_schedule.save()
        return True

    def delete(self, schedule_id: int) -> bool:
        from dbcalm.data.model.db_schedule import DbSchedule  # noqa: PLC0415

        db_schedule = DbSchedule.get_by_id(schedule_id)
        db_schedule.delete_instance()
        return True
