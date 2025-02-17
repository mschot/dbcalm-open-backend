
from abc import ABC, abstractmethod
from queue import Queue


class Adapter(ABC):

    def __init__(self) -> None:
        self.default_stream_compression = "gzip"

    @abstractmethod
    def full_backup(self, identifier: str) -> Queue:
        pass

    @abstractmethod
    def incremental_backup(self, identifier: str, from_identifier: str) -> Queue:
        pass

    @abstractmethod
    def restore(self) -> Queue:
        pass

