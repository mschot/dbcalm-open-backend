import subprocess

class Runner():
    def __init__(self):
        self.pid = None
        pass    

    def execute(self, command: list) -> None:
        self.log(command)
        process = subprocess.Popen(
            command, 
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        self.pid = process.pid        
       
    def log(self, command) -> None:
        #TODO add some sort of loggin functionality
        print(' '.join(command))
        pass