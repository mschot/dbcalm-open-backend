
from abc import ABC, abstractmethod

class Adapter(ABC):

    def __init__(self):
        self.default_stream_compression = 'gzip'
        pass

    @abstractmethod
    def full_backup(self) -> None:
        pass

    @abstractmethod
    def incremental_backup(self) -> None:
        pass

    @abstractmethod
    def restore(self) -> None:
        pass

    