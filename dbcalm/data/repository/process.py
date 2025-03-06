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
