
from abc import ABC, abstractmethod

from dbcalm.data.model.process import Process
from dbcalm.data.types.enum_types import RestoreTarget


class Adapter(ABC):

    def __init__(self) -> None:
        self.default_stream_compression = "gzip"

    @abstractmethod
    def full_backup(self, identifier: str) -> Process:
        pass

    @abstractmethod
    def incremental_backup(self, identifier: str, from_identifier: str) -> Process:
        pass

    @abstractmethod
    def restore_backup(self, identifier_list: list, target: RestoreTarget) -> Process:
        pass

