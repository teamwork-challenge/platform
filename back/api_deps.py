from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from api_models import *
from api_models import RoundStatus
from back.challenge_service import ChallengeService
from back.auth_service import AuthService
from back.database import get_db_session
from back.db_models import Challenge as DbChallenge, Round as DbRound, RoundTaskType as DbRoundTaskType, \
    Task as DbTask
from back.task_service import TaskService
from back.team_service import TeamService

# Services providers

def get_challenge_service(db: Session = Depends(get_db_session)) -> ChallengeService:
    return ChallengeService(db)


def get_task_service(db: Session = Depends(get_db_session)) -> TaskService:
    return TaskService(db)


def get_team_service(db: Session = Depends(get_db_session)) -> TeamService:
    return TeamService(db)


def get_auth_service(db: Session = Depends(get_db_session)) -> AuthService:
    return AuthService(db)


# Auth
PLAYER_API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False, scheme_name="Player")
ADMIN_API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False, scheme_name="Admin")

def authenticate_player(
    api_key: str = Depends(PLAYER_API_KEY_HEADER),
    team_service: TeamService = Depends(get_team_service)
) -> AuthData:
    if api_key is None:
        raise HTTPException(status_code=401, detail="API key is missing")
    auth_data = team_service.get_auth_data(api_key)
    if auth_data is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return auth_data


def authenticate_admin(
    api_key: str = Depends(ADMIN_API_KEY_HEADER),
    team_service: TeamService = Depends(get_team_service)
) -> AuthData:
    auth_data = authenticate_player(api_key, team_service)
    if auth_data.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return auth_data


# Helpers

def ensure_challenge_is_not_deleted(challenge: DbChallenge) -> None:
    if challenge.deleted:
        raise HTTPException(status_code=404, detail="Challenge is deleted")


def get_challenge_or_404(
    challenge_id: int,
    challenge_service: ChallengeService,
    auth_data: AuthData,
    req_method: str = "GET"
) -> DbChallenge:
    challenge = challenge_service.get_challenge(challenge_id)
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
    challenge_service: ChallengeService,
    auth_data: AuthData,
    req_method: str = "GET"
) -> DbRound:
    game_round = challenge_service.get_round(round_id)
    if game_round is None:
        raise HTTPException(status_code=404, detail="Round not found")

    challenge = get_challenge_or_404(game_round.challenge_id, challenge_service, auth_data, req_method)

    if game_round.challenge_id != challenge.id:
        raise HTTPException(status_code=404, detail="Round not found for this challenge")

    if auth_data.role == UserRole.PLAYER:
        if game_round.challenge_id != auth_data.challenge_id or game_round.status != RoundStatus.PUBLISHED:
            raise HTTPException(status_code=404, detail="Round not found")

    return game_round


def get_round_task_type_or_404(
    round_id: int,
    task_type_id: int,
    challenge_service: ChallengeService,
    auth_data: AuthData,
    req_method: str = "GET"
) -> DbRoundTaskType:
    get_round_or_404(round_id, challenge_service, auth_data, req_method)

    round_task_type = challenge_service.get_round_task_type(task_type_id)
    if round_task_type is None or round_task_type.round_id != round_id:
        raise HTTPException(status_code=404, detail="Task type not found for this round")

    return round_task_type


def get_task_or_404(
    task_id: int,
    task_service: TaskService,
    auth_data: AuthData
) -> DbTask:
    task = task_service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.challenge_id != auth_data.challenge_id or task.team_id != auth_data.team_id:
        raise HTTPException(status_code=403, detail="Access to this task is forbidden")

    return task
