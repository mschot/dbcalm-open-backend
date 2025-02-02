from backrest.adapter import adapter
from backrest.builder.list_builder import  ListBuilder
from backrest.command.runner import Runner


class Mariadb(adapter.Adapter):    
    def __init__(self, command_builder: ListBuilder, command_runner: Runner):
        self.command_builder = command_builder
        self.command_runner = command_runner        

    def full_backup(self) -> None:                
        command = self.command_builder.build()
        self.command_runner.execute(command)

    def incremental_backup(self) -> None:
        #command = self.command_builder.build()
        #self.command_runner.execute(command)
        pass

    def restore(self) -> None:
        # command = self.command_builder.build()
        # self.command_runner.execute(command)
        pass

        

        
        