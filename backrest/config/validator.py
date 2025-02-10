
from backrest.config.config import Config
import socket
import os

class Validator():
    ## This class is used to validate the configuration
    ## It checks if the configuration has the required keys
    ## It will probably need changing in the future as these checks are very basic
    ## db_host is currently not validated as it defaults to localhost

    should_exist = [
        'db_type',                
        'backup_dir',        
    ]

    def __init__(self, config: Config, command_runner = False) -> None:
        self.config = config
        self.command_runner = command_runner
        pass

    def validate(self) -> None:
        for key in self.should_exist:
            if self.config.value(key) == '' or self.config.value(key) is None:
               raise Exception(f"Missing required config parameter: {key} in {self.Config.CONFIG_PATH}")
                        
        # Check if backup path exists
        if self.command_runner and not os.path.exists(self.config.value('backup_dir')):
            raise Exception(f"Backup path does not exist: {self.config.value('backup_dir')}")

        # Check if backup path is writable by the current user
        if self.command_runner and not os.access(self.config.value('backup_dir'), os.W_OK):
            raise Exception(f"Backup path is not writable by current user: {self.config.value('backup_dir')}")

        # Check if db_host is reachable
        db_host = self.config.value('db_host')
        try:
            socket.gethostbyname(db_host)
        except socket.error:
            raise Exception(f"Database host is not reachable: {db_host}")            


            
        
                
        