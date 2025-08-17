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

router = APIRouter(prefix="", tags=["Challenges & Rounds"]) 


# Admin: challenges
@router.get("/challenges")
def get_challenges(admin_service: AdminService = Depends(get_admin_service)) -> list[Challenge]:
    db_items = admin_service.get_all_challenges()
    return [Challenge.model_validate(x, from_attributes=True) for x in db_items]


@router.post("/challenges")
def create_challenge(
    new_challenge: ChallengeCreateRequest,
    admin_service: AdminService = Depends(get_admin_service)
) -> Challenge:
    db_ch = admin_service.create_challenge(new_challenge.title, new_challenge.description)
    return Challenge.model_validate(db_ch, from_attributes=True)


@router.delete("/challenges")
def delete_challenge(
    challenge_id: int,
    admin_service: AdminService = Depends(get_admin_service),
    auth_data: AuthData = Depends(authenticate_admin)
) -> Challenge:
    get_challenge_or_404(challenge_id, admin_service, auth_data, "DELETE")

    deleted = admin_service.delete_challenge(challenge_id)
    if deleted is None:
        raise HTTPException(status_code=404, detail="No challenges to delete")
    return Challenge.model_validate(deleted, from_attributes=True)


@router.put("/challenges/{challenge_id}")
def update_challenge(
    challenge_id: int,
    updated_challenge: ChallengeUpdateRequest,
    admin_service: AdminService = Depends(get_admin_service),
    auth_data: AuthData = Depends(authenticate_admin)
) -> Challenge:
    get_challenge_or_404(challenge_id, admin_service, auth_data, "GET")

    updated = admin_service.update_challenge(challenge_id, updated_challenge)
    if updated is None:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return Challenge.model_validate(updated, from_attributes=True)


# Admin: rounds
@router.put("/rounds/{round_id}")
def update_round(
    round_id: int,
    round_data: RoundCreateRequest,
    admin_service: AdminService = Depends(get_admin_service),
    auth_data: AuthData = Depends(authenticate_admin)
) -> Round:
    get_round_or_404(round_id, admin_service, auth_data, "PUT")

    updated_game_round = admin_service.update_round(round_id, round_data)
    if updated_game_round is None:
        raise HTTPException(status_code=404, detail="Round not found")

    updated_game_round.task_types = admin_service.get_round_task_types_by_round(round_id)
    return Round.model_validate(updated_game_round, from_attributes=True)


@router.delete("/rounds/{round_id}")
def delete_round(
    round_id: int,
    admin_service: AdminService = Depends(get_admin_service),
    auth_data: AuthData = Depends(authenticate_admin)
) -> DeleteResponse:
    get_round_or_404(round_id, admin_service, auth_data, "DELETE")
    admin_service.delete_round(round_id)
    return DeleteResponse(deleted_id=round_id)


@router.post("/rounds")
def create_round(
    round_data: RoundCreateRequest,
    admin_service: AdminService = Depends(get_admin_service),
    auth_data: AuthData = Depends(authenticate_admin)
) -> Round:
    get_challenge_or_404(round_data.challenge_id, admin_service, auth_data, "POST")

    game_round = admin_service.create_round(round_data=round_data)

    return Round.model_validate(game_round, from_attributes=True)


# Admin: round task types
@router.put("/task-types/{task_type_id}")
def update_round_task_type(
    task_type_id: int,
    task_type_data: RoundTaskTypeCreateRequest,
    admin_service: AdminService = Depends(get_admin_service),
    auth_data: AuthData = Depends(authenticate_admin)
) -> RoundTaskType:
    task_type = admin_service.get_round_task_type(task_type_id)
    if task_type is None:
        raise HTTPException(status_code=404, detail="Task type not found")

    game_round = get_round_or_404(task_type.round_id, admin_service, auth_data, "PUT")
    get_challenge_or_404(game_round.challenge_id, admin_service, auth_data, "PUT")
    updated_round_task_type = admin_service.update_round_task_type(task_type_id, task_type_data)
    if updated_round_task_type is None:
        raise HTTPException(status_code=404, detail="Task type not found")
    return RoundTaskType.model_validate(updated_round_task_type, from_attributes=True)


@router.delete("/task-types/{task_type_id}")
def delete_round_task_type(
    task_type_id: int,
    admin_service: AdminService = Depends(get_admin_service),
    auth_data: AuthData = Depends(authenticate_admin)
) -> RoundTaskType:
    task_type = admin_service.get_round_task_type(task_type_id)
    if task_type is None:
        raise HTTPException(status_code=404, detail="Task type not found")

    game_round = get_round_or_404(task_type.round_id, admin_service, auth_data, "DELETE")
    ensure_challenge_is_not_deleted(get_challenge_or_404(game_round.challenge_id, admin_service, auth_data, "DELETE"))
    deleted_round_task_type = admin_service.delete_round_task_type(task_type_id)
    if deleted_round_task_type is None:
        raise HTTPException(status_code=404, detail="Task type not found")
    return RoundTaskType.model_validate(deleted_round_task_type, from_attributes=True)


@router.post("/task-types")
def create_round_task_type(
    task_type_data: RoundTaskTypeCreateRequest,
    admin_service: AdminService = Depends(get_admin_service),
    auth_data: AuthData = Depends(authenticate_admin)
) -> RoundTaskType:
    game_round = get_round_or_404(task_type_data.round_id, admin_service, auth_data, "POST")
    ensure_challenge_is_not_deleted(get_challenge_or_404(game_round.challenge_id, admin_service, auth_data, "POST"))
    round_task_type = admin_service.create_round_task_type(task_type_data)
    return RoundTaskType.model_validate(round_task_type, from_attributes=True)


# Player: challenges/rounds/task types
@router.get("/challenges/{challenge_id}")
def get_challenge(
    challenge_id: int | str,
    admin_service: AdminService = Depends(get_admin_service),
    auth_data: AuthData = Depends(authenticate_player)
) -> Challenge:
    if isinstance(challenge_id, str) and challenge_id.lower() == "current":
        if auth_data.challenge_id is None:
            raise HTTPException(status_code=404, detail="Current challenge not found")
        challenge_id = auth_data.challenge_id

    if not isinstance(challenge_id, int):
        challenge_id = int(challenge_id)

    return Challenge.model_validate(get_challenge_or_404(challenge_id, admin_service, auth_data, "GET"), from_attributes=True)


@router.get("/rounds")
def get_rounds(
    challenge_id: int,
    admin_service: AdminService = Depends(get_admin_service),
    auth_data: AuthData = Depends(authenticate_player)
) -> list[Round]:
    get_challenge_or_404(challenge_id, admin_service, auth_data, "GET")

    rounds = admin_service.get_rounds_by_challenge(challenge_id)

    if auth_data.role != UserRole.ADMIN:
        rounds = [r for r in rounds if r.status == RoundStatus.PUBLISHED]

    for r in rounds:
        r.task_types = admin_service.get_round_task_types_by_round(r.id)
    return [Round.model_validate(r, from_attributes=True) for r in rounds]


@router.get("/rounds/{round_id}")
def get_round(
    round_id: int | str,
    admin_service: AdminService = Depends(get_admin_service),
    auth_data: AuthData = Depends(authenticate_player)
) -> Round:
    if isinstance(round_id, str) and round_id.lower() == "current":
        if auth_data.round_id is None:
            raise HTTPException(status_code=404, detail="Current round not found")
        round_id = auth_data.round_id

    if not isinstance(round_id, int):
        round_id = int(round_id)

    r = get_round_or_404(round_id, admin_service, auth_data, "GET")
    r.task_types = admin_service.get_round_task_types_by_round(round_id)
    return Round.model_validate(r, from_attributes=True)


@router.get("/task-types")
def get_round_task_types(
    round_id: int,
    admin_service: AdminService = Depends(get_admin_service),
    auth_data: AuthData = Depends(authenticate_player)
) -> list[RoundTaskType]:
    get_round_or_404(round_id, admin_service, auth_data, "GET")

    return [RoundTaskType.model_validate(rt, from_attributes=True) for rt in admin_service.get_round_task_types_by_round(round_id)]


@router.get("/task-types/{task_type_id}")
def get_round_task_type(
    task_type_id: int,
    admin_service: AdminService = Depends(get_admin_service),
    auth_data: AuthData = Depends(authenticate_player)
) -> RoundTaskType:
    # Get the task type to check if it exists and to get the round_id
    task_type = admin_service.get_round_task_type(task_type_id)
    if task_type is None:
        raise HTTPException(status_code=404, detail="Task type not found")

    get_round_or_404(task_type.round_id, admin_service, auth_data, "GET")

    return RoundTaskType.model_validate(task_type, from_attributes=True)
