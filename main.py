from fastapi import FastAPI

app = FastAPI()


@app.get("/backups")
async def list_backups():
    return {"message": "backups"}

@app.post("/backups")
async def create_backups():
    return {"link": "/status/status_id"}

@app.get("/status/{status_id}")
async def get_status(status_id: int):
    return {
        "id": status_id,
        "status": "completed",
        "type": "backup",
        "link": "/backups/{backup_id}"
    }
