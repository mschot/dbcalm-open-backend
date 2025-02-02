
from abc import ABC, abstractmethod

class ListBuilder(ABC):
    @abstractmethod
    def build(self) -> list:
        pass


