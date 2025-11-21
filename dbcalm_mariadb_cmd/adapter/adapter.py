
from abc import ABC, abstractmethod

from dbcalm.data.data_types.enum_types import RestoreTarget
from dbcalm.data.model.process import Process


class Adapter(ABC):

    def __init__(self) -> None:
        self.default_stream_compression = "gzip"

    @abstractmethod
    def full_backup(self, id: str, schedule_id: int | None = None) -> Process:
        pass

    @abstractmethod
    def incremental_backup(
        self,
        id: str,
        from_backup_id: str,
        schedule_id: int | None = None,
    ) -> Process:
        pass

    @abstractmethod
    def restore_backup(self, id_list: list, target: RestoreTarget) -> Process:
        pass

