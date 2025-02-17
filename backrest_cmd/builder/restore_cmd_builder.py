
from abc import ABC, abstractmethod


class RestoreCommandBuilder(ABC):
    @abstractmethod
    def build_restore_cmd(self: str) -> list:
        pass

