from abc import ABC, abstractmethod

class Config (ABC):
    project_name = 'backrest'
    
    def __init__(self):
        self.config_path = '/etc/'+ self.project_name + '/config.yml'   
        pass

    @abstractmethod
    def value(self, key: str) -> str|bool:
        pass    