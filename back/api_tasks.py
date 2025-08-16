from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException

from api_models import Task, SubmitAnswerRequest, Submission, AuthData
from back.api_deps import authenticate_player, get_player_service, get_admin_service, get_round_or_404, get_task_or_404
from back.player_service import PlayerService
from back.admin_service import AdminService
from back.db_models import Task as DbTask

router = APIRouter(prefix="/tasks", tags=["Tasks"]) 


@router.get("/{task_id}", response_model=Task)
def get_task(
    task_id: int,
    auth_data: AuthData = Depends(authenticate_player),
    player_service: PlayerService = Depends(get_player_service)
) -> DbTask:
    return get_task_or_404(task_id, player_service, auth_data)


@router.post("/{task_id}/submission", response_model=Submission)
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


@router.post("/", response_model=Task)
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


@router.get("/", response_model=list[Task])
def list_tasks(
    auth_data: AuthData = Depends(authenticate_player),
    player_service: PlayerService = Depends(get_player_service)
) -> Sequence[DbTask]:
    if auth_data.team_id is None:
        raise HTTPException(status_code=400, detail="Team not found")
    return player_service.list_tasks_for_team(auth_data.team_id)
