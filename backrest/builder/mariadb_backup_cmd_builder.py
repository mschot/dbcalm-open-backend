
from backrest.builder.list_builder import ListBuilder
from backrest.config.yaml_config import Config 
import datetime

class MariadbBackupCmdBuilder(ListBuilder):
    def __init__(self, config :Config):
        self.config = config    

    def build(self, incremental_base_dir: str = None) -> list:                
        command = [
            'mariabackup', 
            '--backup', 
            '--target-dir=' + self.config.value('backup_path'),
            '--user=' + self.config.value('db_username'),
            '--password=' + self.config.value('db_password'),
        ]         

        ## Add host to the command
        if self.config.value('db_host') == None:
            host = 'localhost'
        else:
            host = self.config.value('db_host')
        command.append('--host=' + host)

        ## Add option for incremental backups
        if incremental_base_dir != None:
            command.append('--incremental-basedir=' + incremental_base_dir)           
        
        ## Add option for stream backups
        stream = self.config.value('stream')
        if stream == True:
            command.append('--stream=xbstream')            

        ## Add option for compression
        compression = self.config.value('compression')
        if compression == None and stream == True:
                compression = self.default_stream_compression

        match compression:
            case 'gzip':
                command.append('| gzip')
            case 'zstd':
                # explanation of the command:
                # - = read from stdin
                # -c = write to stdout
                # -T0 = use all available threads
                command.append('| zstd - -c -T0')            
            
        ## Add option to forward to another command (or write to file)
        forward = self.config.value('forward')
        if stream == True and forward == None:
            timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            command.append('> ' + self.config.value('backup_path') + '/backup-'+ timestamp +'.xbstream')

        if forward != None:
            command.append('| ' + forward)

        return command