
from abc import ABC, abstractmethod

from pydantic import BaseModel


class Adapter(ABC):
    def __init__(self) -> None:
        self.default_stream_compression = "gzip"

    @abstractmethod
    def list(self: BaseModel, query: dict) -> list[BaseModel]:
        pass

    @abstractmethod
    def create(self: BaseModel) -> BaseModel:
        pass

    @abstractmethod
    def update(self: BaseModel) -> BaseModel:
        pass

    @abstractmethod
    def get(self: BaseModel, query: dict) -> BaseModel:
        pass

    @abstractmethod
    def delete(self: BaseModel, query: dict) -> None:
        pass

