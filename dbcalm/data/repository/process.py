from dbcalm.data.model.process import Process


class ProcessRepository:
    def create(self, process: Process) -> Process:
        """Create process."""
        from dbcalm.data.model.db_process import DbProcess  # noqa: PLC0415

        db_process = DbProcess(
            command=process.command,
            command_id=process.command_id,
            pid=process.pid,
            status=process.status,
            output=process.output,
            error=process.error,
            return_code=process.return_code,
            start_time=process.start_time,
            end_time=process.end_time,
            type=process.type,
        )
        db_process.set_args(process.args)
        db_process.save()

        process.id = db_process.id
        return process

    def get(self, process_id: str) -> Process | None:
        """Get process using Peewee."""
        from peewee import DoesNotExist  # noqa: PLC0415

        from dbcalm.data.model.db_process import DbProcess  # noqa: PLC0415

        try:
            db_process = DbProcess.get_by_id(int(process_id))
            # Convert Peewee model back to SQLModel
            return Process(
                id=db_process.id,
                command=db_process.command,
                command_id=db_process.command_id,
                pid=db_process.pid,
                status=db_process.status,
                output=db_process.output,
                error=db_process.error,
                return_code=db_process.return_code,
                start_time=db_process.start_time,
                end_time=db_process.end_time,
                type=db_process.type,
                args=db_process.get_args(),
            )
        except DoesNotExist:
            return None

    def by_command_id(self, command_id: str) -> Process | None:
        """Get most recent process by command_id.

        When multiple processes share a command_id (e.g., consecutive commands),
        returns the last/most recent process (highest ID) which represents the
        final state of the operation.
        """
        from peewee import DoesNotExist  # noqa: PLC0415

        from dbcalm.data.model.db_process import DbProcess  # noqa: PLC0415

        try:
            db_process = (
                DbProcess.select()
                .where(DbProcess.command_id == command_id)
                .order_by(DbProcess.id.desc())
                .get()
            )
            return Process(
                id=db_process.id,
                command=db_process.command,
                command_id=db_process.command_id,
                pid=db_process.pid,
                status=db_process.status,
                output=db_process.output,
                error=db_process.error,
                return_code=db_process.return_code,
                start_time=db_process.start_time,
                end_time=db_process.end_time,
                type=db_process.type,
                args=db_process.get_args(),
            )
        except DoesNotExist:
            return None

    def get_list(
        self,
        query: list | None,
        order: list | None,
        page: int | None = 1,
        per_page: int | None = 10,
    ) -> tuple[list[Process], int]:
        """Get list of processes."""
        from dbcalm.data.model.db_process import DbProcess  # noqa: PLC0415

        # Build query
        db_query = DbProcess.select()

        # Apply filters
        if query:
            for filter_obj in query:
                db_query = self._apply_filter(db_query, filter_obj)

        # Get total count before pagination
        total = db_query.count()

        # Apply ordering
        if order:
            for filter_obj in order:
                db_query = self._apply_order(db_query, filter_obj)

        # Apply pagination
        if page and per_page:
            offset = (page - 1) * per_page
            db_query = db_query.limit(per_page).offset(offset)

        # Execute query and convert to SQLModel
        processes = [
            Process(
                id=db_process.id,
                command=db_process.command,
                command_id=db_process.command_id,
                pid=db_process.pid,
                status=db_process.status,
                output=db_process.output,
                error=db_process.error,
                return_code=db_process.return_code,
                start_time=db_process.start_time,
                end_time=db_process.end_time,
                type=db_process.type,
                args=db_process.get_args(),
            )
            for db_process in db_query
        ]

        return processes, total

    def _apply_filter(  # noqa: C901, PLR0911, ANN202
        self,
        query,  # noqa: ANN001
        filter_obj,  # noqa: ANN001
    ):
        """Apply filter to query."""
        from dbcalm.data.model.db_process import DbProcess  # noqa: PLC0415
        from dbcalm.util.parse_query_with_operators import QueryFilter  # noqa: PLC0415

        if not isinstance(filter_obj, QueryFilter):
            msg = "filter_obj must be a QueryFilter instance"
            raise TypeError(msg)

        field = getattr(DbProcess, filter_obj.field)
        operator = filter_obj.operator
        value = filter_obj.value

        if operator == "eq":
            return query.where(field == value)
        if operator == "ne":
            return query.where(field != value)
        if operator == "gt":
            return query.where(field > value)
        if operator == "gte":
            return query.where(field >= value)
        if operator == "lt":
            return query.where(field < value)
        if operator == "lte":
            return query.where(field <= value)
        if operator == "like":
            return query.where(field.contains(value))
        if operator == "in":
            return query.where(field.in_(value))
        if operator == "isnull":
            return query.where(field.is_null())
        if operator == "isnotnull":
            return query.where(field.is_null(is_null=False))
        return query

    def _apply_order(  # noqa: ANN202
        self,
        query,  # noqa: ANN001
        filter_obj,  # noqa: ANN001
    ):
        """Apply ordering to query."""
        from dbcalm.data.model.db_process import DbProcess  # noqa: PLC0415
        from dbcalm.util.parse_query_with_operators import QueryFilter  # noqa: PLC0415

        if not isinstance(filter_obj, QueryFilter):
            msg = "filter_obj must be a QueryFilter instance"
            raise TypeError(msg)

        field = getattr(DbProcess, filter_obj.field)
        if filter_obj.operator == "desc":
            return query.order_by(field.desc())
        return query.order_by(field.asc())
