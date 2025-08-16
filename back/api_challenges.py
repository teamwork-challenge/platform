from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException

from api_models import (
    Challenge, Round, RoundStatus, RoundCreateRequest, RoundTaskType, RoundTaskTypeCreateRequest,
    ChallengeUpdateRequest, ChallengeCreateRequest, AuthData, DeleteResponse, UserRole
)
from back.admin_service import AdminService
from back.api_deps import (
    authenticate_player, authenticate_admin, get_admin_service,
    ensure_challenge_is_not_deleted, get_challenge_or_404, get_round_or_404
)
from back.db_models import Challenge as DbChallenge, Round as DbRound, RoundTaskType as DbRoundTaskType

router = APIRouter(prefix="", tags=["Challenges & Rounds"]) 


# Admin: challenges
@router.get("/challenges", response_model=list[Challenge], )
def get_challenges(admin_service: AdminService = Depends(get_admin_service)) -> Sequence[DbChallenge]:
    return admin_service.get_all_challenges()


@router.post("/challenges", response_model=Challenge)
def create_challenge(
    new_challenge: ChallengeCreateRequest,
    admin_service: AdminService = Depends(get_admin_service)
) -> DbChallenge:
    return admin_service.create_challenge(new_challenge.title, new_challenge.description)


@router.delete("/challenges", response_model=Challenge)
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


@router.put("/challenges/{challenge_id}", response_model=Challenge)
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


# Admin: rounds
@router.put("/rounds/{round_id}", response_model=Round)
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


@router.delete("/rounds/{round_id}", response_model=DeleteResponse)
def delete_round(
    round_id: int,
    admin_service: AdminService = Depends(get_admin_service),
    auth_data: AuthData = Depends(authenticate_admin)
) -> DeleteResponse:
    get_round_or_404(round_id, admin_service, auth_data, "DELETE")
    admin_service.delete_round(round_id)
    return DeleteResponse(deleted_id=round_id)


@router.post("/rounds", response_model=Round)
def create_round(
    round_data: RoundCreateRequest,
    admin_service: AdminService = Depends(get_admin_service),
    auth_data: AuthData = Depends(authenticate_admin)
) -> DbRound:
    get_challenge_or_404(round_data.challenge_id, admin_service, auth_data, "POST")

    game_round = admin_service.create_round(round_data=round_data)

    return game_round


# Admin: round task types
@router.put("/task-types/{task_type_id}", response_model=RoundTaskType)
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


@router.delete("/task-types/{task_type_id}", response_model=RoundTaskType)
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


@router.post("/task-types", response_model=RoundTaskType)
def create_round_task_type(
    task_type_data: RoundTaskTypeCreateRequest,
    admin_service: AdminService = Depends(get_admin_service),
    auth_data: AuthData = Depends(authenticate_admin)
) -> DbRoundTaskType:
    game_round = get_round_or_404(task_type_data.round_id, admin_service, auth_data, "POST")
    ensure_challenge_is_not_deleted(get_challenge_or_404(game_round.challenge_id, admin_service, auth_data, "POST"))
    round_task_type = admin_service.create_round_task_type(task_type_data)
    return round_task_type


# Player: challenges/rounds/task types
@router.get("/challenges/{challenge_id}", response_model=Challenge)
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


@router.get("/rounds", response_model=list[Round])
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


@router.get("/rounds/{round_id}", response_model=Round)
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


@router.get("/task-types", response_model=list[RoundTaskType])
def get_round_task_types(
    round_id: int,
    admin_service: AdminService = Depends(get_admin_service),
    auth_data: AuthData = Depends(authenticate_player)
) -> Sequence[DbRoundTaskType]:
    get_round_or_404(round_id, admin_service, auth_data, "GET")

    return admin_service.get_round_task_types_by_round(round_id)


@router.get("/task-types/{task_type_id}", response_model=RoundTaskType)
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
