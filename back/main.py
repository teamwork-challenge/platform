from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.security import APIKeyHeader
from models import Challenge, Task, UserRole
from services import AdminService, PlayerService
from repo import Repo
from mangum import Mangum

repo = Repo()

# create services with repo
admin_service = AdminService(repo)
player_service = PlayerService(repo)

# API key header
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# Dependency for API key authentication
def get_api_key(api_key: str = Depends(API_KEY_HEADER)) -> str:
    if api_key is None:
        raise HTTPException(status_code=401, detail="API key is missing")

    key_data = repo.validate_api_key(api_key)
    if key_data is None:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return api_key

# Dependency for admin role authentication
def get_admin_api_key(api_key: str = Depends(get_api_key)) -> str:
    role = repo.get_role_from_api_key(api_key)
    if role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return api_key

# Dependency for player role authentication
def get_player_api_key(api_key: str = Depends(get_api_key)) -> dict:
    role = repo.get_role_from_api_key(api_key)
    if role != UserRole.PLAYER:
        raise HTTPException(status_code=403, detail="Player access required")

    challenge_id = repo.get_challenge_from_api_key(api_key)
    if challenge_id is None:
        raise HTTPException(status_code=403, detail="No challenge associated with this API key")

    return {"api_key": api_key, "challenge_id": challenge_id}

admin = APIRouter(
    prefix="",
    tags=["Admin"],
    dependencies=[Depends(get_admin_api_key)]
)

# admin endpoints
@admin.get("/challenges")
def get_challenges():
    return admin_service.get_all_challenges()

@admin.post("/challenges")
def create_challenge(new_challenge: Challenge):
    return admin_service.create_challenge(new_challenge.title)

@admin.get("/challenges/{challenge_id}")
def get_challenge(challenge_id: int):
    challenge = admin_service.get_challenge(challenge_id)
    if challenge is None:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return challenge

@admin.put("/challenges/{challenge_id}")
def update_challenge(challenge_id: int, updated_challenge: Challenge):
    updated = admin_service.update_challenge(challenge_id, updated_challenge.title)
    if updated is None:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return {"message": "Challenge updated", "challenge": updated}

@admin.delete("/challenges")
def delete_challenge(challenge_id: int):
    deleted = admin_service.delete_challenge(challenge_id)
    if deleted is None:
        raise HTTPException(status_code=404, detail="No challenges to delete")
    return {"message": "Challenge deleted", "deleted_challenge": deleted}


player = APIRouter(
    prefix="",
    tags=["Player"],
    dependencies=[Depends(get_player_api_key)]
)

# player endpoints
@player.get("/tasks/{task_id}")
def get_task(task_id: int):
    task = player_service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@player.post("/tasks")
def create_task(new_task: Task, auth_data: dict = Depends(get_player_api_key)):
    challenge_id = auth_data["challenge_id"]
    return player_service.create_task(challenge_id, new_task.title, new_task.status)

app = FastAPI(title="Teamwork Challenge API",
              description="API for managing teamwork challenges and tasks",
              version="1.0.0")
app.include_router(admin)
app.include_router(player)

# Create handler for AWS Lambda
handler = Mangum(app, lifespan="off")
