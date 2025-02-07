
from backrest_cmd.config.config import Config
from fastapi.exceptions import ValidationException
import socket
import os

class Validator():
    ## This class is used to validate the configuration
    ## It checks if the configuration has the required keys
    ## It will probably need changing in the future as these checks are very basic
    ## db_host is currently not validated as it defaults to localhost

    should_exist = [
        'db_type',        
        'db_user',
        'db_password',        
        'backup_path',
        
    ]

    def __init__(self, config: Config) -> None:
        self.config = config
        pass

    def validate(self) -> None:
        for key in self.should_exist:
            if self.config.value(key) == '' or self.config.value(key) is None:
               raise ValidationException(f"Missing required config parameter: {key} in {self.config.config_path}")
                        
        # Check if backup path exists
        if not os.path.exists(self.config.value('backup_path')):
            raise ValidationException(f"Backup path does not exist: {self.config.value('backup_path')}")

        # Check if backup path is writable by the current user
        if not os.access(self.config.value('backup_path'), os.W_OK):
            raise ValidationException(f"Backup path is not writable by current user: {self.config.value('backup_path')}")

        # Check if db_host is reachable
        db_host = self.config.value('db_host', 'localhost')
        try:
            socket.gethostbyname(db_host)
        except socket.error:
            raise ValidationException(f"Database host is not reachable: {db_host}")
        
        ##  TODO check if db_user can connect to the database
        ##  TODO check if db_password is correct
        ##  TODO check if db_type is supported
        ##  TODO check if db_type is installed
        ##  TODO check if db_type is running


            
        
                
        