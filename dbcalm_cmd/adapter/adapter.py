
from abc import ABC, abstractmethod
from queue import Queue

from dbcalm.data.model.process import Process


class Adapter(ABC):

    @abstractmethod
    def update_cron_schedules(self, schedules: list) -> tuple[Process, Queue]:
        pass
