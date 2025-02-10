from abc import ABC, abstractmethod

class Config (ABC):
    PROJECT_NAME = 'backrest'
    CONFIG_PATH = '/etc/'+ PROJECT_NAME + '/config.yml'   
    CMD_SOCKET_PATH = '/var/run/'+ PROJECT_NAME + '/cmd.sock'
    DB_PATH = '/var/lib/'+ PROJECT_NAME + '/db.sqlite3'   

    
    def __init__(self):                
        pass

    @abstractmethod
    def value(self, key: str) -> str|bool:
        pass    