
from backrest_cmd.builder.backup_cmd_builder import BackupCommandBuilder
from backrest_cmd.config.yaml_config import Config 
import datetime

class MariadbBackupCmdBuilder(BackupCommandBuilder):
    def __init__(self, config :Config):
        self.config = config    
    
    def build(self, identifier: str, incremental_base_dir: str = None) -> list:                
        command = [
            'mariabackup', 
            '--backup', 
            '--target-dir=' + self.config.value('backup_path').rstrip('/') + '/' + identifier,
            '--user=' + self.config.value('db_user'),
            '--password=' + self.config.value('db_password'),
        ]         

        ## Add host to the command
        if self.config.value('db_host') is None:
            host = 'localhost'
        else:
            host = self.config.value('db_host')
        command.append('--host=' + host)

        ## Add option for incremental backups
        if incremental_base_dir is not None:
            command.append('--incremental-basedir=' + incremental_base_dir)           
        
        ## Add option for stream backups
        stream = self.config.value('stream')
        if stream:
            command.append('--stream=xbstream')            

        ## Add option for compression
        compression = self.config.value('compression')
        if compression is None and stream:
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
        if stream and forward is None:
            timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            command.append('> ' + self.config.value('backup_path') + '/backup-'+ timestamp +'.xbstream')

        if forward is not None:
            command.append('| ' + forward)

        return command
    
    def build_full_backup_cmd(self, identifier: str) -> list:
        return self.build(identifier)
    
    def build_incremental_backup_cmd(self, identifier: str, build_from_identifier: str) -> list:
        return self.build_incremental_backup_cmd(identifier, build_from_identifier)
    
    
