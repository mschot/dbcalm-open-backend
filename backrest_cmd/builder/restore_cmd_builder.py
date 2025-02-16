
from abc import ABC, abstractmethod

class RestoreCommandBuilder(ABC):
    @abstractmethod
    def build_restore_cmd(identifier: str) -> list:
        pass    

