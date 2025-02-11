from fastapi import FastAPI, Response
from backrest.config.config_factory import config_factory
from backrest.config.validator import Validator
from backrest.api.model.request.backup_request import BackupRequest
from backrest.api.model.response.status import Status
from backrest_client.client import Client
from backrest.str.kebab import kebab_case
from typing import Any
import uvicorn
import os
from datetime import datetime


config = config_factory()
Validator(config).validate()

app = FastAPI()
@app.get("/backups")
async def list_backups():
    return {"message": "backups"}

@app.post("/backups", response_model=Status)
async def create_backup(request: BackupRequest, response: Response) -> Any :    
    client = Client()
    
    if request.identifier is None:
        identifier = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    else:
        identifier = kebab_case(identifier)
        
    if(request.from_identifier is None):
        process = client.command('full_backup', {'identifier': identifier})
    else:
        process = client.command('incremental_backup', {'identifier': identifier, 'from_identifier': request.from_identifier})

    if process['code'] == 202:
        response.status_code = 202
        pid = str(process['pid']) + process['created_at']
        return Status(pid = pid, link = "/status/%s" % pid, status=process['status'])
    else:
        response.status_code = 500
        return Status(status="Error")

@app.get("/status/{status_id}")
async def get_status(status_id: int):
    return {
        "id": status_id,
        "status": "completed",
        "type": "backup",
        "link": "/backups/{backup_id}"
    }

if(__name__ == "__main__"):

    uvicorn_args = {
        "app": app,
        "host": "0.0.0.0",
        "port": 8000,
    }
    if(config.value('ssl_cert') and config.value('ssl_key')):
        ssl_cert = config.value('ssl_cert')
        ssl_key = config.value('ssl_key')

        if(not os.access(ssl_cert, os.R_OK) or not os.access(ssl_key, os.R_OK)):
            raise Exception("SSL certificate and/or key file(s) are not readable by " + config.PROJECT_NAME)    

        uvicorn_args['ssl_certfile'] = ssl_cert
        uvicorn_args['ssl_keyfile'] = ssl_key
    
    uvicorn.run(**uvicorn_args)    

