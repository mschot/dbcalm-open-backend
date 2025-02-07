from backrest_cmd.adapter import adapter
from backrest_cmd.builder.backup_cmd_builder import BackupCommandBuilder
from backrest_cmd.command.runner import Runner
from queue import Queue


class Mariadb(adapter.Adapter):    
    def __init__(self, command_builder: BackupCommandBuilder, command_runner: Runner):
        self.command_builder = command_builder
        self.command_runner = command_runner                

    def full_backup(self, identifier: str) -> Queue:                
        command = self.command_builder.build_full_backup_cmd(identifier)
        return self.command_runner.execute(command)

    def incremental_backup(self) -> None:
        #command = self.command_builder.build()
        #self.command_runner.execute(command)
        pass

    def restore(self) -> None:
        # command = self.command_builder.build()
        # self.command_runner.execute(command)
        pass

        

        
        