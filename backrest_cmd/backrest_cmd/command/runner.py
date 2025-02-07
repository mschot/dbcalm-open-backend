import subprocess
import threading
from queue import Queue

class Runner():
    def __init__(self):
        
        self.output_queue = Queue()
        pass    

    def execute(self, command: list) -> Queue:
        self.log(' '.join(command))
        process = subprocess.Popen(
            command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
                
        def capture_output():        
            stdout, stderr = process.communicate()
            self.output_queue.put(
                {
                    "pid": process.pid, 
                    "stdout": stdout, 
                    "stderr": stderr, 
                    "returncode": process.returncode
                }
            )

        # Run the output capture in a separate thread
        threading.Thread(target=capture_output, daemon=True).start()
        return self.output_queue
       
    def log(self, content: str) -> None:
        #TODO add some sort of loggin functionality
        # and remove any password fields
        
        print(content)
        pass