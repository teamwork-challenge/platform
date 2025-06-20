from fastapi import FastAPI, HTTPException
from models import Challenge, Task
from services import AdminService, PlayerService

#create a FastAPI application
app = FastAPI()

admin_service = AdminService()
player_service = PlayerService()

# admin endpoints
@app.get("/challenges", tags=["Admin"])
def get_challenges():
    return admin_service.get_challenges()

@app.post("/challenges", tags=["Admin"])
def create_challenge(new_challenge: Challenge):
    return admin_service.create_challenge(new_challenge.title)

@app.get("/challenges/{challenge_id}", tags=["Admin"])
def get_challenge(challenge_id: int):
    return admin_service.get_challenge(challenge_id)

@app.put("/challenges/{challenge_id}", tags=["Admin"])
def update_challenge(challenge_id: int, updated_challenge: Challenge):
    return admin_service.update_challenge(challenge_id, updated_challenge.title)

@app.delete("/challenges", tags=["Admin"])
def delete_all_challenges():
    return admin_service.delete_all_challenges()

# player endpoints
@app.get("/tasks/{task_id}", tags=["Player"])
def get_task(task_id: int):
    return player_service.get_task(task_id)

@app.post("/tasks", tags=["Player"])
def create_task(new_task: Task):
    return player_service.create_task(new_task.title, new_task.status)
