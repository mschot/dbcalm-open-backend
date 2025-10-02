from dbcalm.data.adapter.adapter_factory import adapter_factory
from dbcalm.data.model.process import Process


class ProcessRepository:
    def __init__(self) -> None:
        self.adapter = adapter_factory()

    def create(self, process: Process) -> Process:
        return self.adapter.create(process)

    def get(self, process_id: str) -> Process | None:
        return self.adapter.get(Process, {"id" : process_id})

    def by_command_id(self, command_id: str) -> list[Process]:
        return self.adapter.get(Process, {"command_id" : command_id})

    def get_list(
        self,
        query: dict | None,
        order: dict | None,
        page: int | None = 1,
        per_page: int | None = 10,
    ) -> tuple[list[Process], int]:
        items, total = self.adapter.get_list(Process, query, order, page, per_page)
        return items, total
