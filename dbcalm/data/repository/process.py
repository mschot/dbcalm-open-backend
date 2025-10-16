from dbcalm.data.adapter.adapter_factory import adapter_factory
from dbcalm.data.model.process import Process


class ProcessRepository:
    def __init__(self) -> None:
        self.adapter = adapter_factory()

    def create(self, process: Process) -> Process:
        return self.adapter.create(process)

    def get(self, process_id: str) -> Process | None:
        return self.adapter.get(Process, {"id" : process_id})

    def by_command_id(self, command_id: str) -> Process | None:
        """Get the most recent process for a given command_id.

        When multiple processes share a command_id (e.g., consecutive commands),
        returns the last/most recent process (highest ID) which represents the
        final state of the operation.
        """
        from dbcalm.util.parse_query_with_operators import QueryFilter  # noqa: PLC0415

        query_filters = [
            QueryFilter(field="command_id", operator="eq", value=command_id),
        ]
        order_filters = [QueryFilter(field="id", operator="desc", value="desc")]

        processes, _ = self.adapter.get_list(
            Process,
            query_filters,
            order_filters,
            page=1,
            per_page=1,
        )

        return processes[0] if processes else None

    def get_list(
        self,
        query: dict | None,
        order: dict | None,
        page: int | None = 1,
        per_page: int | None = 10,
    ) -> tuple[list[Process], int]:
        items, total = self.adapter.get_list(Process, query, order, page, per_page)
        return items, total
