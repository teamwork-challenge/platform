from fastapi import APIRouter, Depends, HTTPException

from api_models import (
    Challenge, Round, RoundTaskType,
    AuthData, DeleteResponse, UserRole
)
from back.api_deps import (
    authenticate_player, authenticate_admin, get_challenge_service,
    get_challenge_or_404, get_round_or_404
)
from back.firebase_challenge_service import ChallengeService

router = APIRouter(prefix="", tags=["Challenges & Rounds"]) 


# Admin: challenges
@router.get("/challenges", dependencies=[Depends(authenticate_admin)])
def get_challenges(challenge_service: ChallengeService = Depends(get_challenge_service)) -> list[Challenge]:
    db_items = challenge_service.get_all_challenges()
    return [Challenge.model_validate(x, from_attributes=True) for x in db_items]


@router.get("/challenges/{challenge_id}")
def get_challenge(
    challenge_id: str,
    challenge_service: ChallengeService = Depends(get_challenge_service),
    auth_data: AuthData = Depends(authenticate_player)
) -> Challenge:
    if challenge_id.lower() == "current":
        if auth_data.challenge_id is None:
            raise HTTPException(status_code=404, detail="Current challenge not found")
        challenge_id = auth_data.challenge_id

    challenge = get_challenge_or_404(challenge_id, challenge_service, auth_data)
    return Challenge.model_validate(challenge, from_attributes=True)


@router.delete("/challenges/{challenge_id}")
def delete_challenge(
    challenge_id: str,
    challenge_service: ChallengeService = Depends(get_challenge_service),
    auth_data: AuthData = Depends(authenticate_admin)
) -> Challenge:
    get_challenge_or_404(challenge_id, challenge_service, auth_data)

    deleted = challenge_service.delete_challenge(challenge_id)
    if deleted is None:
        raise HTTPException(status_code=404, detail="No challenges to delete")
    return Challenge.model_validate(deleted, from_attributes=True)


@router.put("/challenges/{challenge_id}")
def put_challenge(
    challenge_id: str,
    updated_challenge: Challenge,
    challenge_service: ChallengeService = Depends(get_challenge_service),
    auth_data: AuthData = Depends(authenticate_admin)
) -> Challenge:
    get_challenge_or_404(challenge_id, challenge_service, auth_data)

    updated = challenge_service.update_challenge(challenge_id, updated_challenge)
    if updated is None:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return Challenge.model_validate(updated, from_attributes=True)


@router.get("/challenges/{challenge_id}/rounds")
def get_rounds(
    challenge_id: str,
    challenge_service: ChallengeService = Depends(get_challenge_service),
    auth_data: AuthData = Depends(authenticate_player)
) -> list[Round]:
    get_challenge_or_404(challenge_id, challenge_service, auth_data)

    rounds = challenge_service.get_rounds_by_challenge(challenge_id)
    if auth_data.role != UserRole.ADMIN:
        rounds = [r for r in rounds if r.published]

    return [Round.model_validate(r, from_attributes=True) for r in rounds]


@router.put("/challenges/{challenge_id}/rounds/{round_id}")
def put_round(
    round_id: str,
    challenge_id: str,
    round_data: Round,
    challenge_service: ChallengeService = Depends(get_challenge_service),
    auth_data: AuthData = Depends(authenticate_admin)
) -> Round:
    round_data.id = round_id
    round_data.challenge_id = challenge_id
    get_challenge_or_404(round_data.challenge_id, challenge_service, auth_data)
    updated_game_round = challenge_service.update_round(round_data)
    return updated_game_round


@router.delete("/challenges/{challenge_id}/rounds/{round_id}")
def delete_round(
    round_id: str,
    challenge_id: str,
    challenge_service: ChallengeService = Depends(get_challenge_service),
    auth_data: AuthData = Depends(authenticate_admin)
) -> DeleteResponse:
    r = get_round_or_404(round_id, challenge_id, challenge_service, auth_data)
    challenge_service.delete_round(round_id, challenge_id)
    return DeleteResponse(deleted_id=round_id)


@router.get("/challenges/{challenge_id}/rounds/{round_id}")
def get_round(
    round_id: str,
    challenge_id: str,
    challenge_service: ChallengeService = Depends(get_challenge_service),
    auth_data: AuthData = Depends(authenticate_player)
) -> Round:
    round_id = fix_round_id(auth_data, round_id)
    resolved_challenge_id = fix_challenge_id(auth_data, challenge_id)
    r = get_round_or_404(round_id, resolved_challenge_id, challenge_service, auth_data)
    res = Round.model_validate(r, from_attributes=True)
    res.task_types = challenge_service.get_round_task_types_by_round(round_id, resolved_challenge_id)
    return res


def fix_round_id(auth_data: AuthData, round_id: str):
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


@router.get("/challenges/{challenge_id}/round/{round_id}/task-types")
def get_round_task_types(
    round_id: str,
    challenge_id: str,
    challenge_service: ChallengeService = Depends(get_challenge_service),
    auth_data: AuthData = Depends(authenticate_player)
) -> list[RoundTaskType]:
    round_id = fix_round_id(auth_data, round_id)
    challenge_id = fix_challenge_id(auth_data, challenge_id)
    get_round_or_404(round_id, challenge_id, challenge_service, auth_data)

    types = challenge_service.get_round_task_types_by_round(round_id, challenge_id)
    return types


@router.get("/challenges/{challenge_id}/round/{round_id}/task-types/{task_type}")
def get_round_task_type(
    task_type: str,
    round_id: str | None = None,
    challenge_id: str | None = None,
    challenge_service: ChallengeService = Depends(get_challenge_service),
    auth_data: AuthData = Depends(authenticate_player)
) -> RoundTaskType:
    challenge_id = fix_challenge_id(auth_data, challenge_id)
    round_id = fix_round_id(auth_data, round_id)
    get_round_or_404(round_id, challenge_id, challenge_service, auth_data)
    task_type = challenge_service.get_round_task_type(task_type, challenge_id, round_id)
    return RoundTaskType.model_validate(task_type, from_attributes=True)
