import uvicorn
from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.security import APIKeyHeader

from api_models import *
from api_models.models import Round, RoundCreateRequest, TeamImportResponse, TeamRequest, TeamCreateRequest, RoundTaskType, RoundTaskTypeCreateRequest
from auth_service import AuthService
from admin_service import AdminService
from player_service import PlayerService
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
@admin.get("/challenges", response_model=list[Challenge])
def get_challenges(admin_service: AdminService = Depends(get_admin_service)):
    return admin_service.get_all_challenges()


@admin.post("/challenges", response_model=Challenge)
def create_challenge(new_challenge: ChallengeCreateRequest, admin_service: AdminService = Depends(get_admin_service)):
    return admin_service.create_challenge(new_challenge.title, new_challenge.description)


@admin.delete("/challenges")
def delete_challenge(challenge_id: int, admin_service: AdminService = Depends(get_admin_service)):
    deleted = admin_service.delete_challenge(challenge_id)
    if deleted is None:
        raise HTTPException(status_code=404, detail="No challenges to delete")
    return {"message": "Challenge deleted", "deleted_challenge": deleted}


@admin.get("/challenges/{id}", response_model=Challenge)
def get_challenge(challenge_id: int, admin_service: AdminService = Depends(get_admin_service)):
    challenge = admin_service.get_challenge(challenge_id)
    if challenge is None:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return challenge


@admin.put("/challenges/{id}", response_model=Challenge)
def update_challenge(challenge_id: int, updated_challenge: ChallengeCreateRequest, admin_service: AdminService = Depends(get_admin_service)):
    updated = admin_service.update_challenge(challenge_id, updated_challenge.title, updated_challenge.description)
    if updated is None:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return {"message": "Challenge updated", "challenge": updated}


@admin.get("/rounds", response_model=list[Round])
def get_rounds(challenge_id: int, admin_service: AdminService = Depends(get_admin_service)):
    challenge = admin_service.get_challenge(challenge_id)
    if challenge is None:
        raise HTTPException(status_code=404, detail="Challenge not found")

    rounds = admin_service.get_rounds_by_challenge(challenge_id)

    for round in rounds:
        round.task_types = admin_service.get_round_task_types_by_round(round.id)

    return rounds


@admin.get("/rounds/{id}", response_model=Round)
def get_round(challenge_id: int, round_id: int, admin_service: AdminService = Depends(get_admin_service)):
    challenge = admin_service.get_challenge(challenge_id)
    if challenge is None:
        raise HTTPException(status_code=404, detail="Challenge not found")

    round = admin_service.get_round(round_id)
    if round is None:
        raise HTTPException(status_code=404, detail="Round not found")

    if round.challenge_id != challenge_id:
        raise HTTPException(status_code=404, detail="Round not found for this challenge")

    round.task_types = admin_service.get_round_task_types_by_round(round_id)

    return round


@admin.put("/rounds/{id}", response_model=Round)
def update_round(challenge_id: int, round_id: int, round_data: RoundCreateRequest, admin_service: AdminService = Depends(get_admin_service)):
    round = admin_service.get_round(round_id)
    if round is None or round.challenge_id != challenge_id:
        raise HTTPException(status_code=404, detail="Round not found for this challenge")

    updated_round = admin_service.update_round(
        round_id=round_id,
        start_time=round_data.start_time,
        end_time=round_data.end_time,
        claim_by_type=round_data.claim_by_type,
        allow_resubmit=round_data.allow_resubmit,
        score_decay=round_data.score_decay,
        status=round_data.status
    )

    updated_round.task_types = admin_service.get_round_task_types_by_round(round_id)

    return updated_round


@admin.delete("/rounds/{round_id}")
def delete_round(round_id: int, admin_service: AdminService = Depends(get_admin_service)):
    round = admin_service.get_round(round_id)
    if round is None:
        raise HTTPException(status_code=404, detail="Round not found")

    deleted_round = admin_service.delete_round(round_id)

    return {"message": "Round deleted", "round": deleted_round}


@admin.post("/round", response_model=Round)
def create_round(round_data: RoundCreateRequest, admin_service: AdminService = Depends(get_admin_service)):
    challenge = admin_service.get_challenge(round_data.challenge_id)
    if challenge is None:
        raise HTTPException(status_code=404, detail="Challenge not found")

    round = admin_service.create_round(
        challenge_id=round_data.challenge_id,
        index=round_data.index,
        start_time=round_data.start_time,
        end_time=round_data.end_time,
        claim_by_type=round_data.claim_by_type,
        allow_resubmit=round_data.allow_resubmit,
        score_decay=round_data.score_decay,
        status=round_data.status
    )

    if round is None:
        raise HTTPException(status_code=404, detail="Challenge not found")

    return round


@admin.get("/task-types", response_model=list[RoundTaskType])
def get_round_task_types(challenge_id: int, round_id: int, admin_service: AdminService = Depends(get_admin_service)):
    challenge = admin_service.get_challenge(challenge_id)
    if challenge is None:
        raise HTTPException(status_code=404, detail="Challenge not found")

    round = admin_service.get_round(round_id)
    if round is None or round.challenge_id != challenge_id:
        raise HTTPException(status_code=404, detail="Round not found for this challenge")

    return admin_service.get_round_task_types_by_round(round_id)


@admin.get("/task-types/{id}", response_model=RoundTaskType)
def get_round_task_type(challenge_id: int, round_id: int, task_type_id: int, admin_service: AdminService = Depends(get_admin_service)):
    challenge = admin_service.get_challenge(challenge_id)
    if challenge is None:
        raise HTTPException(status_code=404, detail="Challenge not found")

    round = admin_service.get_round(round_id)
    if round is None or round.challenge_id != challenge_id:
        raise HTTPException(status_code=404, detail="Round not found for this challenge")

    round_task_type = admin_service.get_round_task_type(task_type_id)
    if round_task_type is None or round_task_type.round_id != round_id:
        raise HTTPException(status_code=404, detail="Task type not found for this round")

    return round_task_type


@admin.put("/task-types/{id}", response_model=RoundTaskType)
def update_round_task_type(challenge_id: int, round_id: int, task_type_id: int, task_type_data: RoundTaskTypeCreateRequest, admin_service: AdminService = Depends(get_admin_service)):
    challenge = admin_service.get_challenge(challenge_id)
    if challenge is None:
        raise HTTPException(status_code=404, detail="Challenge not found")

    round = admin_service.get_round(round_id)
    if round is None or round.challenge_id != challenge_id:
        raise HTTPException(status_code=404, detail="Round not found for this challenge")

    round_task_type = admin_service.get_round_task_type(task_type_id)
    if round_task_type is None or round_task_type.round_id != round_id:
        raise HTTPException(status_code=404, detail="Task type not found for this round")

    updated_round_task_type = admin_service.update_round_task_type(
        round_task_type_id=task_type_id,
        type=task_type_data.type,
        generator_url=task_type_data.generator_url,
        generator_settings=task_type_data.generator_settings,
        generator_secret=task_type_data.generator_secret
    )

    return updated_round_task_type


@admin.delete("/task-types/{id}")
def delete_round_task_type(task_type_id: int, admin_service: AdminService = Depends(get_admin_service)):
    round_task_type = admin_service.get_round_task_type(task_type_id)
    if round_task_type is None:
        raise HTTPException(status_code=404, detail="Task type not found")

    deleted_round_task_type = admin_service.delete_round_task_type(task_type_id)

    return {"message": "Task type deleted", "task_type": deleted_round_task_type}


@admin.post("/task-type", response_model=RoundTaskType)
def create_round_task_type(challenge_id: int, round_id: int, task_type_data: RoundTaskTypeCreateRequest, admin_service: AdminService = Depends(get_admin_service)):
    challenge = admin_service.get_challenge(challenge_id)
    if challenge is None:
        raise HTTPException(status_code=404, detail="Challenge not found")

    round = admin_service.get_round(round_id)
    if round is None or round.challenge_id != challenge_id:
        raise HTTPException(status_code=404, detail="Round not found for this challenge")

    round_task_type = admin_service.create_round_task_type(
        round_id=task_type_data.round_id,
        type=task_type_data.type,
        generator_url=task_type_data.generator_url,
        generator_settings=task_type_data.generator_settings,
        generator_secret=task_type_data.generator_secret
    )

    return round_task_type


@admin.post("/teams", response_model=TeamImportResponse)
def create_teams(request: TeamCreateRequest, admin_service: AdminService = Depends(get_admin_service)):
    teams_data = admin_service.create_teams(request.challenge_id, request.teams)
    if teams_data is None:
        raise HTTPException(status_code=404, detail="Challenge not found")

    # Convert the list of dictionaries to a list of Team objects
    teams = []
    for team_dict in teams_data:
        teams.append(Team(
            id=team_dict["team_id"],
            challenge_id=team_dict["challenge_id"],
            name=team_dict["name"],
            api_key=team_dict["api_key"],
            members=team_dict["members"],
            captain_contact=team_dict["captain_contact"],
            total_score=0
        ))

    return TeamImportResponse(challenge_id=request.challenge_id, teams=teams)


player = APIRouter(
    prefix="",
    tags=["Player"],
    dependencies=[Depends(authenticate_player)]
)


# player endpoints
@player.get("/team", response_model=Team)
def get_team(auth_data: AuthData = Depends(authenticate_player), player_service: PlayerService = Depends(get_player_service)):
    team = player_service.get_team(auth_data.team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")

    return team


@player.get("/tasks/{task_id}")
def get_task(task_id: int, auth_data: AuthData = Depends(authenticate_player), player_service: PlayerService = Depends(get_player_service)):
    task = player_service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.challenge_id != auth_data.challenge_id or task.team_id != auth_data.team_id:
        raise HTTPException(status_code=403, detail="Access to this task is forbidden")

    return task


@player.post("/tasks")
def create_task(task_type: Optional[str], auth_data: AuthData = Depends(authenticate_player), player_service: PlayerService = Depends(get_player_service)):
    return player_service.create_task(auth_data.challenge_id, auth_data.team_id, task_type)


app = FastAPI(title="Teamwork Challenge API",
              description="API for managing teamwork challenges and tasks",
              version="1.0.0")
app.include_router(admin)
app.include_router(player)

# Create a handler for AWS Lambda

handler = Mangum(app, lifespan="off")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        reload=True,
        reload_dirs=[".", "../api_models"],
        port=8088,
    )
