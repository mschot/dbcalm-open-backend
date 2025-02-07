from fastapi import FastAPI
from backrest_cmd.config.config_factory import config_factory
from backrest_cmd.adapter.adapter_factory import adapter_factory
from backrest_cmd.config.validator import Validator
config = config_factory('yaml')
Validator(config).validate()

app = FastAPI()
@app.get("/backups")
async def list_backups():
    return {"message": "backups"}

@app.post("/backups")
async def create_backup():    
    adapter = adapter_factory(config)
    adapter.full_backup()
    return {"link": "/status/status_id"}

@app.get("/status/{status_id}")
async def get_status(status_id: int):
    return {
        "id": status_id,
        "status": "completed",
        "type": "backup",
        "link": "/backups/{backup_id}"
    }
