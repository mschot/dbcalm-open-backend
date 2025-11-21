
from abc import ABC, abstractmethod
from queue import Queue

from dbcalm_cmd.process.process_model import Process


class Adapter(ABC):

    @abstractmethod
    def update_cron_schedules(self, schedules: list) -> tuple[Process, Queue]:
        pass
