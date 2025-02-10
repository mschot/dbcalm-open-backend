import subprocess
import threading
from queue import Queue
from datetime import datetime
from backrest.data.model.process import Process
from backrest.data.adapter.adapter_factory import adapter_factory as data_adapter_factory

class Runner():
    def __init__(self):
        
        self.output_queue = Queue()
        self.data_adapter = data_adapter_factory()
        pass    

    def create_process(self, pid, command, start_time) -> Process:        
        process = self.data_adapter.create(Process(pid=pid, command=command, start_time=start_time, status='running'))    
        return process
    
    def update_process(self, process: Process, end_time, stdout, stderr, returncode) -> Process:
        status = 'success' if returncode == 0 else 'failed'        
        process.output = stdout
        process.error = stderr
        process.return_code = returncode
        process.end_time = end_time
        process.status = status
        self.data_adapter.update(process)
        return Process

    def execute(self, command: list) -> Queue:
        start_time = datetime.now()        
        process = subprocess.Popen(
            command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )

        processModel = self.create_process(process.pid, ' '.join(command), start_time)        
                        
        def capture_output():        
            end_time = datetime.now()            
            stdout, stderr = process.communicate()
            #save changes to db
            process_rep = self.update_process(
                processModel, 
                end_time, 
                stdout, 
                stderr, 
                process.returncode
            )
            # Put the process representation in the output queue
            self.output_queue.put(process_rep)

        # Run the output capture in a separate thread
        threading.Thread(target=capture_output, daemon=True).start()
        return self.output_queue
       
    def log(self, content: str) -> None:
        #TODO add some sort of logging functionality
        # and remove any password fields
        
        print(content)
        pass