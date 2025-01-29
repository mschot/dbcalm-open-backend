from adapter import Adapter
from .context import config as configuration
import subprocess

class MariaDBAdapter(Adapter):
    
    def full_backup(self) -> None:
        print("Full backup for MariaDB")
        config = configuration.Config()
        process = subprocess.Popen(
            [
                'mariabackup', 
                '--backup', 
                '--target-dir=' + config.value('backup_path'),
                '--user=' + config.value('username'),
                '--password=' + config.value('password'),
            ], 
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        
        self.backup_pid = process.pid
        