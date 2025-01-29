
from abc import ABC, abstractmethod

class Adapter(ABC):
    @abstractmethod
    def full_backup(self) -> None:
        pass

    @abstractmethod
    def incremental_backup(self) -> None:
        pass

    @abstractmethod
    def restore(self) -> None:
        pass