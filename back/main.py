from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.security import APIKeyHeader

from models import AuthData
from models import ChallengeOut, ChallengeNew, Task, UserRole
from services import AdminService, PlayerService, AuthService
from mangum import Mangum
from sqlalchemy.orm import Session
from database import get_db_session

def get_admin_service(db: Session = Depends(get_db_session)) -> AdminService:
    return AdminService(db)

def get_player_service(db: Session = Depends(get_db_session)) -> PlayerService:
    return PlayerService(db)

def get_auth_service(db: Session = Depends(get_db_session)) -> AuthService:
    return AuthService(db)

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

def authenticate_player(api_key: str = Depends(API_KEY_HEADER), auth_service: AuthService = Depends(get_auth_service)) -> AuthData:
    if api_key is None:
        raise HTTPException(status_code=401, detail="API key is missing")
    auth_data = auth_service.get_auth_data(api_key)
    if auth_data is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return auth_data

def authenticate_admin(auth_data: AuthData = Depends(authenticate_player)) -> AuthData:
    if auth_data.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return auth_data

admin = APIRouter(
    prefix="",
    tags=["Admin"],
    dependencies=[Depends(authenticate_admin)]
)

# admin endpoints
@admin.get("/challenges", response_model=list[ChallengeOut])
def get_challenges(admin_service: AdminService = Depends(get_admin_service)):
    return admin_service.get_all_challenges()

@admin.post("/challenges", response_model=ChallengeOut)
def create_challenge(new_challenge: ChallengeNew, admin_service: AdminService = Depends(get_admin_service)):
    return admin_service.create_challenge(new_challenge.title, new_challenge.description)

@admin.get("/challenges/{challenge_id}", response_model=ChallengeOut)
def get_challenge(challenge_id: int, admin_service: AdminService = Depends(get_admin_service)):
    challenge = admin_service.get_challenge(challenge_id)
    if challenge is None:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return challenge

@admin.put("/challenges/{challenge_id}", response_model=ChallengeOut)
def update_challenge(challenge_id: int, updated_challenge: ChallengeNew, admin_service: AdminService = Depends(get_admin_service)):
    updated = admin_service.update_challenge(challenge_id, updated_challenge.title, updated_challenge.description)
    if updated is None:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return {"message": "Challenge updated", "challenge": updated}

@admin.delete("/challenges")
def delete_challenge(challenge_id: int, admin_service: AdminService = Depends(get_admin_service)):
    deleted = admin_service.delete_challenge(challenge_id)
    if deleted is None:
        raise HTTPException(status_code=404, detail="No challenges to delete")
    return {"message": "Challenge deleted", "deleted_challenge": deleted}


player = APIRouter(
    prefix="",
    tags=["Player"],
    dependencies=[Depends(authenticate_player)]
)

# player endpoints
@player.get("/tasks/{task_id}")
def get_task(task_id: int, auth_data: AuthData = Depends(authenticate_player), player_service: PlayerService = Depends(get_player_service)):
    task = player_service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.challenge_id != auth_data.challenge_id or task.team_id != auth_data.team_id:
        raise HTTPException(status_code=403, detail="Access to this task is forbidden")

    return task

@player.post("/tasks")
def create_task(new_task: Task, auth_data: AuthData = Depends(authenticate_player), player_service: PlayerService = Depends(get_player_service)):
    return player_service.create_task(auth_data.challenge_id, new_task.title, new_task.status)

app = FastAPI(title="Teamwork Challenge API",
              description="API for managing teamwork challenges and tasks",
              version="1.0.0")
app.include_router(admin)
app.include_router(player)

# Create handler for AWS Lambda

handler = Mangum(app, lifespan="off")
