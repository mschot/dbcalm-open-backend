from __future__ import annotations

from sqlmodel import Session, SQLModel, create_engine

from backrest.config.config import Config
from backrest.data.adapter.adapter import Adapter
from backrest.logger.logger_factory import logger_factory


class Local(Adapter):
    def __init__(self) -> None:
        self.session  = self.session()
        self.logger = logger_factory()
        super().__init__()

    def session(self) -> Session:
        engine = create_engine("sqlite:///" + Config.DB_PATH)
        SQLModel.metadata.create_all(engine)
        return Session(engine, expire_on_commit=False)

    def get(self, model: SQLModel, query: dict) -> SQLModel|None:
        if len(self.list(model, query)) == 0:
            return None
        return self.list(model, query)[0]

    def create(self, model: SQLModel) -> SQLModel:
        self.session.add(model)
        try:
            self.session.commit()
        except Exception:
            self.logger.exception("error committing")
            self.session.rollback()
            raise
        return model

    def update(self, model: SQLModel) -> SQLModel:
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        return model

    def list(self, model: SQLModel, query: dict) -> list[SQLModel]:
        return self.session.query(model).filter_by(**query).all()

    def delete(self, model: SQLModel) -> None:
        self.session.delete(model)
        self.session.commit()
