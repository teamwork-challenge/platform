from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader

from api_models import *
from back.services.challenge_service import ChallengeService
from back.db_models import RoundDocument, TaskDocument
from back.services.task_service import TaskService
from back.services.team_service import TeamService


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

def ensure_has_access(
    auth_data: AuthData,
    challenge_id: str
) -> None:
    if auth_data.role != UserRole.ADMIN and challenge_id != auth_data.challenge_id:
        raise HTTPException(status_code=404, detail="Challenge not found or access forbidden")


def get_challenge_or_404(
    challenge_id: str,
    challenge_service: ChallengeService,
    auth_data: AuthData
) -> Challenge:
    ensure_has_access(auth_data, challenge_id)
    challenge = challenge_service.get_challenge(challenge_id)
    if challenge is None:
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
        raise HTTPException(status_code=404, detail=f"Round not found: {round_id=} {challenge_id=}")

    challenge = get_challenge_or_404(challenge_id, challenge_service, auth_data)

    if game_round.challenge_id != challenge.id:
        raise HTTPException(status_code=404, detail="Round not found for this challenge")

    if auth_data.role == UserRole.PLAYER:
        if game_round.challenge_id != auth_data.challenge_id or not game_round.published:
            raise HTTPException(status_code=404, detail="Round not found")

    return game_round


def fix_round_id(auth_data: AuthData, round_id: str) -> str:
    if round_id.lower() == "current":
        if auth_data.round_id is None:
            raise HTTPException(status_code=404, detail="Current round not found")
        round_id = auth_data.round_id
    return round_id


def fix_challenge_id(auth_data: AuthData, challenge_id: str | None) -> str:
    if auth_data.role == UserRole.ADMIN:
        if challenge_id is None:
            raise HTTPException(status_code=400, detail="challenge_id is required for admin")
        if challenge_id.lower() == "current":
            if auth_data.challenge_id is None:
                raise HTTPException(status_code=404, detail="Current challenge not found")
            challenge_id = auth_data.challenge_id
        return challenge_id
    # Player path
    if auth_data.challenge_id is None:
        raise HTTPException(status_code=400, detail="Challenge not found")
    return auth_data.challenge_id

def get_task_or_404(
    task_id: str,
    task_service: TaskService,
    auth_data: AuthData
) -> TaskDocument:
    if auth_data.challenge_id is None or auth_data.team_id is None:
        raise HTTPException(status_code=400, detail="Invalid team or challenge context")
    if auth_data.round_id is None:
        raise HTTPException(status_code=400, detail="Round not found")
    assert auth_data.challenge_id is not None
    assert auth_data.round_id is not None
    task = task_service.get_task(task_id, auth_data.challenge_id, auth_data.round_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.challenge_id != auth_data.challenge_id or task.team_id != auth_data.team_id:
        raise HTTPException(status_code=403, detail="Access to this task is forbidden")

    return task
