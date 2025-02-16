from backrest.data.adapter.adapter import Adapter
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.orm.query import Query
from backrest.config.config import Config



class Local(Adapter):
    def __init__(self):
        self.session  = self.session()            
        super().__init__()

    def session(self) -> Session:        
        engine = create_engine('sqlite:///' + Config.DB_PATH)
        SQLModel.metadata.create_all(engine)
        return Session(engine)
        
    def get(self, model: SQLModel, query: dict) -> SQLModel|None:            
        if len(self.list(model, query)) == 0:
            return None
        return self.list(model, query)[0]
    
    def create(self, model: SQLModel) -> SQLModel:
        self.session.add(model)
        try:
            self.session.commit()            
        except Exception as e:
            print(vars(e))            
            self.session.rollback()
            raise e
        return model       

    def update(self, model: SQLModel) -> SQLModel:        
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)         
        return model

    def list(self, model: SQLModel, query: dict) -> list[SQLModel]:           
        return self.session.query(model).filter_by(**query).all()
    
    def delete(self, model: SQLModel, _: dict) -> None:
        self.session.delete(model)
        self.session.commit()
        return                
