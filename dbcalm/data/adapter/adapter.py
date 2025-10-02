
from abc import ABC, abstractmethod

from pydantic import BaseModel


class Adapter(ABC):
    def __init__(self) -> None:
        self.default_stream_compression = "gzip"

    @abstractmethod
    def get_list(
        self,
        model: BaseModel,
        query: list | None,
        order: list | None,
        page: int | None = 1,
        per_page: int | None = 100,
    ) -> tuple[list[BaseModel], int]:
        pass

    @abstractmethod
    def create(self, model: BaseModel) -> BaseModel:
        pass

    @abstractmethod
    def update(self, model: BaseModel) -> BaseModel:
        pass

    @abstractmethod
    def get(self, model: BaseModel, query: dict) -> BaseModel:
        pass

    @abstractmethod
    def delete(self, model: BaseModel, query: dict) -> bool:
        pass

