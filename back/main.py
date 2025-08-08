from typing import Sequence

import uvicorn
from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.security import APIKeyHeader
from mangum import Mangum
from sqlalchemy.orm import Session

from back.admin_service import AdminService
from api_models import *
from api_models import Challenge, Round, RoundStatus, RoundCreateRequest, TeamsImportResponse, TeamsImportRequest, \
    RoundTaskType, RoundTaskTypeCreateRequest, ChallengeUpdateRequest, SubmitAnswerRequest, Submission
from back.auth_service import AuthService
from back.database import get_db_session
from back.db_models import Challenge as DbChallenge, Round as DbRound, RoundTaskType as DbRoundTaskType, \
    Task as DbTask, Team as DbTeam
from back.player_service import PlayerService


def get_admin_service(db: Session = Depends(get_db_session)) -> AdminService:
    return AdminService(db)


def get_player_service(db: Session = Depends(get_db_session)) -> PlayerService:
    return PlayerService(db)


def get_auth_service(db: Session = Depends(get_db_session)) -> AuthService:
    return AuthService(db)


API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def authenticate_player(
    api_key: str = Depends(API_KEY_HEADER), 
    auth_service: AuthService = Depends(get_auth_service)
) -> AuthData:
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


def ensure_challenge_is_not_deleted(challenge: DbChallenge) -> None:
    if challenge.deleted:
        raise HTTPException(status_code=404, detail="Challenge is deleted")


def get_challenge_or_404(
    challenge_id: int, 
    admin_service: AdminService, 
    auth_data: AuthData, 
    req_method: str = "GET"
) -> DbChallenge:
    challenge = admin_service.get_challenge(challenge_id)
    if challenge is None:
        raise HTTPException(status_code=404, detail="Challenge not found")

    if challenge.deleted and req_method != "GET":
        raise HTTPException(status_code=404, detail="Challenge is deleted")

    # If a user is a player, check if they have access to this challenge
    if auth_data.role == UserRole.PLAYER and challenge.id != auth_data.challenge_id:
        raise HTTPException(status_code=404, detail="Challenge not found")

    return challenge


def get_round_or_404(
    round_id: int, 
    admin_service: AdminService, 
    auth_data: AuthData, 
    req_method: str = "GET"
) -> DbRound:
    game_round = admin_service.get_round(round_id)
    if game_round is None:
        raise HTTPException(status_code=404, detail="Round not found")

    challenge = get_challenge_or_404(game_round.challenge_id, admin_service, auth_data, req_method)

    if game_round.challenge_id != challenge.id:
        raise HTTPException(status_code=404, detail="Round not found for this challenge")

    if auth_data.role == UserRole.PLAYER:
        if game_round.challenge_id != auth_data.challenge_id or game_round.status != RoundStatus.PUBLISHED:
            raise HTTPException(status_code=404, detail="Round not found")

    return game_round


def get_round_task_type_or_404(
    round_id: int, 
    task_type_id: int, 
    admin_service: AdminService, 
    auth_data: AuthData, 
    req_method: str = "GET"
) -> DbRoundTaskType:
    get_round_or_404(round_id, admin_service, auth_data, req_method)

    round_task_type = admin_service.get_round_task_type(task_type_id)
    if round_task_type is None or round_task_type.round_id != round_id:
        raise HTTPException(status_code=404, detail="Task type not found for this round")

    return round_task_type


def get_task_or_404(
    task_id: int, 
    player_service: PlayerService, 
    auth_data: AuthData
) -> DbTask:
    task = player_service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.challenge_id != auth_data.challenge_id or task.team_id != auth_data.team_id:
        raise HTTPException(status_code=403, detail="Access to this task is forbidden")

    return task


admin = APIRouter(
    prefix="",
    tags=["Admin"],
    dependencies=[Depends(authenticate_admin)]
)


# admin endpoints
@admin.get("/challenges", response_model=list[Challenge])
def get_challenges(admin_service: AdminService = Depends(get_admin_service)) -> Sequence[DbChallenge]:
    return admin_service.get_all_challenges()


@admin.post("/challenges", response_model=Challenge)
def create_challenge(
    new_challenge: ChallengeCreateRequest, 
    admin_service: AdminService = Depends(get_admin_service)
) -> DbChallenge:
    return admin_service.create_challenge(new_challenge.title, new_challenge.description)


@admin.delete("/challenges", response_model=Challenge)
def delete_challenge(
    challenge_id: int, 
    admin_service: AdminService = Depends(get_admin_service), 
    auth_data: AuthData = Depends(authenticate_admin)
) -> DbChallenge:
    get_challenge_or_404(challenge_id, admin_service, auth_data, "DELETE")

    deleted = admin_service.delete_challenge(challenge_id)
    if deleted is None:
        raise HTTPException(status_code=404, detail="No challenges to delete")
    return deleted


@admin.put("/challenges/{challenge_id}", response_model=Challenge)
def update_challenge(
    challenge_id: int, 
    updated_challenge: ChallengeUpdateRequest, 
    admin_service: AdminService = Depends(get_admin_service), 
    auth_data: AuthData = Depends(authenticate_admin)
) -> DbChallenge:
    get_challenge_or_404(challenge_id, admin_service, auth_data, "GET")

    updated = admin_service.update_challenge(challenge_id, updated_challenge)
    if updated is None:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return updated


@admin.put("/rounds/{round_id}", response_model=Round)
def update_round(
    round_id: int, 
    round_data: RoundCreateRequest, 
    admin_service: AdminService = Depends(get_admin_service), 
    auth_data: AuthData = Depends(authenticate_admin)
) -> DbRound:
    get_round_or_404(round_id, admin_service, auth_data, "PUT")

    updated_game_round = admin_service.update_round(round_id, round_data)
    if updated_game_round is None:
        raise HTTPException(status_code=404, detail="Round not found")

    updated_game_round.task_types = admin_service.get_round_task_types_by_round(round_id)
    return updated_game_round


@admin.delete("/rounds/{round_id}", response_model=DeleteResponse)
def delete_round(
    round_id: int, 
    admin_service: AdminService = Depends(get_admin_service), 
    auth_data: AuthData = Depends(authenticate_admin)
) -> DeleteResponse:
    get_round_or_404(round_id, admin_service, auth_data, "DELETE")
    admin_service.delete_round(round_id)
    return DeleteResponse(deleted_id=round_id)


@admin.post("/rounds", response_model=Round)
def create_round(
    round_data: RoundCreateRequest, 
    admin_service: AdminService = Depends(get_admin_service), 
    auth_data: AuthData = Depends(authenticate_admin)
) -> DbRound:
    get_challenge_or_404(round_data.challenge_id, admin_service, auth_data, "POST")

    game_round = admin_service.create_round(round_data=round_data)

    return game_round


@admin.put("/task-types/{task_type_id}", response_model=RoundTaskType)
def update_round_task_type(
    task_type_id: int, 
    task_type_data: RoundTaskTypeCreateRequest, 
    admin_service: AdminService = Depends(get_admin_service), 
    auth_data: AuthData = Depends(authenticate_admin)
) -> DbRoundTaskType:
    task_type = admin_service.get_round_task_type(task_type_id)
    if task_type is None:
        raise HTTPException(status_code=404, detail="Task type not found")

    game_round = get_round_or_404(task_type.round_id, admin_service, auth_data, "PUT")
    get_challenge_or_404(game_round.challenge_id, admin_service, auth_data, "PUT")
    updated_round_task_type = admin_service.update_round_task_type(task_type_id, task_type_data)
    if updated_round_task_type is None:
        raise HTTPException(status_code=404, detail="Task type not found")
    return updated_round_task_type


@admin.delete("/task-types/{task_type_id}", response_model=RoundTaskType)
def delete_round_task_type(
    task_type_id: int, 
    admin_service: AdminService = Depends(get_admin_service), 
    auth_data: AuthData = Depends(authenticate_admin)
) -> DbRoundTaskType:
    task_type = admin_service.get_round_task_type(task_type_id)
    if task_type is None:
        raise HTTPException(status_code=404, detail="Task type not found")

    game_round = get_round_or_404(task_type.round_id, admin_service, auth_data, "DELETE")
    ensure_challenge_is_not_deleted(get_challenge_or_404(game_round.challenge_id, admin_service, auth_data, "DELETE"))
    deleted_round_task_type = admin_service.delete_round_task_type(task_type_id)
    if deleted_round_task_type is None:
        raise HTTPException(status_code=404, detail="Task type not found")
    return deleted_round_task_type


@admin.post("/task-types", response_model=RoundTaskType)
def create_round_task_type(
    task_type_data: RoundTaskTypeCreateRequest, 
    admin_service: AdminService = Depends(get_admin_service), 
    auth_data: AuthData = Depends(authenticate_admin)
) -> DbRoundTaskType:
    game_round = get_round_or_404(task_type_data.round_id, admin_service, auth_data, "POST")
    ensure_challenge_is_not_deleted(get_challenge_or_404(game_round.challenge_id, admin_service, auth_data, "POST"))
    round_task_type = admin_service.create_round_task_type(task_type_data)
    return round_task_type


@admin.get("/teams", response_model=list[Team])
def get_teams(
    challenge_id: int | None = None,
    admin_service: AdminService = Depends(get_admin_service), 
    auth_data: AuthData = Depends(authenticate_admin)
) -> Sequence[DbTeam]:
    if challenge_id is not None:
        # Check if the challenge exists
        get_challenge_or_404(challenge_id, admin_service, auth_data, "GET")
        # Get teams for the specified challenge
        return admin_service.get_teams_by_challenge(challenge_id)
    else:
        # Get all teams
        return admin_service.get_all_teams()


@admin.post("/teams", response_model=TeamsImportResponse)
def create_teams(
    request: TeamsImportRequest, 
    admin_service: AdminService = Depends(get_admin_service), 
    auth_data: AuthData = Depends(authenticate_admin)
) -> TeamsImportResponse:
    challenge = get_challenge_or_404(request.challenge_id, admin_service, auth_data, "POST")
    teams_data = admin_service.create_teams(challenge, request.teams)
    teams = [Team.model_validate(team) for team in teams_data]
    return TeamsImportResponse(challenge_id=challenge.id, teams=teams)


player = APIRouter(
    prefix="",
    tags=["Player"],
    dependencies=[Depends(authenticate_player)]
)


# player endpoints

@player.get("/auth", response_model=UserRole)
def auth(auth_data: AuthData = Depends(authenticate_player)) -> UserRole:
    return auth_data.role


@player.get("/team", response_model=Team)
def get_team(
    auth_data: AuthData = Depends(authenticate_player), 
    player_service: PlayerService = Depends(get_player_service)
) -> DbTeam:
    if auth_data.team_id is None:
        raise HTTPException(status_code=404, detail="Team not found")
    team = player_service.get_team(auth_data.team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@player.get("/challenges/{challenge_id}", response_model=Challenge)
def get_challenge(
    challenge_id: int | str, 
    admin_service: AdminService = Depends(get_admin_service), 
    auth_data: AuthData = Depends(authenticate_player)
) -> DbChallenge:
    if isinstance(challenge_id, str) and challenge_id.lower() == "current":
        if auth_data.challenge_id is None:
            raise HTTPException(status_code=404, detail="Current challenge not found")
        challenge_id = auth_data.challenge_id

    if not isinstance(challenge_id, int):
        challenge_id = int(challenge_id)

    return get_challenge_or_404(challenge_id, admin_service, auth_data, "GET")


@player.get("/rounds", response_model=list[Round])
def get_rounds(
    challenge_id: int, 
    admin_service: AdminService = Depends(get_admin_service), 
    auth_data: AuthData = Depends(authenticate_player)
) -> Sequence[DbRound]:
    get_challenge_or_404(challenge_id, admin_service, auth_data, "GET")

    rounds = admin_service.get_rounds_by_challenge(challenge_id)

    if auth_data.role != UserRole.ADMIN:
        rounds = [r for r in rounds if r.status == RoundStatus.PUBLISHED]

    for r in rounds:
        r.task_types = admin_service.get_round_task_types_by_round(r.id)
    return rounds


# GET /rounds/1
@player.get("/rounds/{round_id}", response_model=Round)
def get_round(
    round_id: int | str, 
    admin_service: AdminService = Depends(get_admin_service), 
    auth_data: AuthData = Depends(authenticate_player)
) -> DbRound:
    if isinstance(round_id, str) and round_id.lower() == "current":
        if auth_data.round_id is None:
            raise HTTPException(status_code=404, detail="Current round not found")
        round_id = auth_data.round_id

    if not isinstance(round_id, int):
        round_id = int(round_id)

    r = get_round_or_404(round_id, admin_service, auth_data, "GET")
    r.task_types = admin_service.get_round_task_types_by_round(round_id)
    return r


@player.get("/task-types", response_model=list[RoundTaskType])
def get_round_task_types(
    round_id: int, 
    admin_service: AdminService = Depends(get_admin_service), 
    auth_data: AuthData = Depends(authenticate_player)
) -> Sequence[DbRoundTaskType]:
    get_round_or_404(round_id, admin_service, auth_data, "GET")

    return admin_service.get_round_task_types_by_round(round_id)


@player.get("/task-types/{task_type_id}", response_model=RoundTaskType)
def get_round_task_type(
    task_type_id: int, 
    admin_service: AdminService = Depends(get_admin_service), 
    auth_data: AuthData = Depends(authenticate_player)
) -> DbRoundTaskType:
    # Get the task type to check if it exists and to get the round_id
    task_type = admin_service.get_round_task_type(task_type_id)
    if task_type is None:
        raise HTTPException(status_code=404, detail="Task type not found")

    get_round_or_404(task_type.round_id, admin_service, auth_data, "GET")

    return task_type


@player.get("/tasks/{task_id}", response_model=Task)
def get_task(
    task_id: int, 
    auth_data: AuthData = Depends(authenticate_player), 
    player_service: PlayerService = Depends(get_player_service)
) -> DbTask:
    return get_task_or_404(task_id, player_service, auth_data)


@player.post("/tasks/{task_id}/submission", response_model=Submission)
def submit_task_answer(
    task_id: int, 
    answer_data: SubmitAnswerRequest,
    auth_data: AuthData = Depends(authenticate_player), 
    player_service: PlayerService = Depends(get_player_service)
) -> Submission:
    answer = answer_data.answer
        
    try:
        if auth_data.team_id is None:
            raise HTTPException(status_code=400, detail="Team not found")
        submission = player_service.submit_task_answer(task_id, auth_data.team_id, answer)
        return submission
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@player.post("/tasks", response_model=Task)
def create_task(
    task_type: str | None = None,
    auth_data: AuthData = Depends(authenticate_player), 
    player_service: PlayerService = Depends(get_player_service),
    admin_service: AdminService = Depends(get_admin_service)

) -> DbTask:
    if auth_data.round_id is None:
        raise HTTPException(status_code=400, detail="No current round available")
    game_round = get_round_or_404(auth_data.round_id, admin_service, auth_data)
    try:
        if auth_data.challenge_id is None or auth_data.team_id is None:
            raise HTTPException(status_code=400, detail="Invalid team or challenge context")
        if task_type is None:
            task_type = player_service.get_random_task_type(game_round, auth_data.team_id).type
        elif not game_round.claim_by_type:
            raise HTTPException(status_code=400, detail="Round does not allow task creation by type")
        return player_service.create_task(auth_data.challenge_id, auth_data.team_id, task_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


app = FastAPI(title="Teamwork Challenge API",
              description="API for managing teamwork challenges and tasks",
              version="1.0.0")
app.include_router(admin)
app.include_router(player)


@app.get("/", response_model=str)
def home() -> str:
    return "hello"


handler = Mangum(app, lifespan="off")


if __name__ == "__main__":
    uvicorn.run(
        "back.main:app",
        reload=True,
        reload_dirs=[".", "../api_models"],
        port=8088,
    )
