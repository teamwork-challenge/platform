from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader

from api_models import *
from back.firebase_challenge_service import ChallengeService
from back.firebase_models import RoundDocument, TaskDocument
from back.firebase_task_service import TaskService
from back.firebase_team_service import TeamService


# Services providers

def get_challenge_service() -> ChallengeService:
    return ChallengeService()


def get_task_service() -> TaskService:
    return TaskService()


def get_team_service() -> TeamService:
    return TeamService()


# Auth
PLAYER_API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False, scheme_name="Player")
ADMIN_API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False, scheme_name="Admin")

def authenticate_player(
    api_key: str | None = Depends(PLAYER_API_KEY_HEADER),
    team_service: TeamService = Depends(get_team_service)
) -> AuthData:
    if api_key is None:
        raise HTTPException(status_code=401, detail="API key is missing")
    auth_data = team_service.get_auth_data(api_key)
    if auth_data is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return auth_data


def authenticate_admin(
    api_key: str | None = Depends(ADMIN_API_KEY_HEADER),
    team_service: TeamService = Depends(get_team_service)
) -> AuthData:
    auth_data = authenticate_player(api_key, team_service)
    if auth_data.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return auth_data


# Helpers

def get_challenge_or_404(
    challenge_id: str,
    challenge_service: ChallengeService,
    auth_data: AuthData
) -> Challenge:
    challenge = challenge_service.get_challenge(challenge_id)
    if challenge is None:
        raise HTTPException(status_code=404, detail="Challenge not found")

    # If a user is a player, check if they have access to this challenge
    if auth_data.role == UserRole.PLAYER and challenge.id != auth_data.challenge_id:
        raise HTTPException(status_code=404, detail="Challenge not found")

    return challenge


def get_round_or_404(
    round_id: str,
    challenge_id: str,
    challenge_service: ChallengeService,
    auth_data: AuthData
) -> RoundDocument:
    game_round = challenge_service.get_round(round_id, challenge_id)
    if game_round is None:
        raise HTTPException(status_code=404, detail="Round not found")

    challenge = get_challenge_or_404(challenge_id, challenge_service, auth_data)

    if game_round.challenge_id != challenge.id:
        raise HTTPException(status_code=404, detail="Round not found for this challenge")

    if auth_data.role == UserRole.PLAYER:
        if game_round.challenge_id != auth_data.challenge_id or not game_round.published:
            raise HTTPException(status_code=404, detail="Round not found")

    return game_round


def get_round_task_type_or_404(
    round_id: str,
    challenge_id: str,
    task_type_id: str,
    challenge_service: ChallengeService,
    auth_data: AuthData,
    req_method: str = "GET"
) -> RoundTaskType:
    get_round_or_404(round_id, challenge_id, challenge_service, auth_data)

    round_task_type = challenge_service.get_round_task_type(task_type_id, challenge_id, round_id)
    if round_task_type is None:
        raise HTTPException(status_code=404, detail="Task type not found for this round")

    return round_task_type


def get_task_or_404(
    task_id: str,
    task_service: TaskService,
    auth_data: AuthData
) -> TaskDocument:
    if auth_data.challenge_id is None or auth_data.team_id is None:
        raise HTTPException(status_code=400, detail="Invalid team or challenge context")
    if auth_data.round_id is None:
        raise HTTPException(status_code=400, detail="Round not found")
    task = task_service.get_task(task_id, auth_data.challenge_id, auth_data.round_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.challenge_id != auth_data.challenge_id or task.team_id != auth_data.team_id:
        raise HTTPException(status_code=403, detail="Access to this task is forbidden")

    return task
