
from abc import ABC, abstractmethod
from pydantic import BaseModel
from sqlalchemy.orm.query import Query
class Adapter(ABC):
    def __init__(self):
        self.default_stream_compression = 'gzip'
        pass

    @abstractmethod
    def list(model: BaseModel, query: Query) -> list[BaseModel]:
        pass

    @abstractmethod
    def create(model: BaseModel) -> BaseModel:
        pass

    @abstractmethod
    def update(model: BaseModel) -> BaseModel:
        pass

    @abstractmethod
    def get(model: BaseModel, query: Query) -> BaseModel:
        pass

    @abstractmethod
    def delete(model: BaseModel, query: Query) -> None:
        pass

    