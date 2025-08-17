from typing import Sequence

from datetime import datetime
from api_models import TaskStatus
from fastapi import APIRouter, Depends, HTTPException

from api_models import Task, SubmitAnswerRequest, Submission, AuthData
from back.api_deps import authenticate_player, get_player_service, get_admin_service, get_round_or_404, get_task_or_404
from back.player_service import PlayerService
from back.admin_service import AdminService
from back.db_models import Task as DbTask

router = APIRouter(prefix="/tasks", tags=["Tasks"]) 


@router.get("/{task_id}")
def get_task(
    task_id: int,
    auth_data: AuthData = Depends(authenticate_player),
    player_service: PlayerService = Depends(get_player_service)
) -> Task:
    return Task.model_validate(get_task_or_404(task_id, player_service, auth_data), from_attributes=True)


@router.post("/{task_id}/submission")
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
        return Submission.model_validate(submission, from_attributes=True)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("")
def create_task(
    task_type: str | None = None,
    auth_data: AuthData = Depends(authenticate_player),
    player_service: PlayerService = Depends(get_player_service),
    admin_service: AdminService = Depends(get_admin_service)
) -> Task:
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
        return Task.model_validate(player_service.create_task(auth_data.challenge_id, auth_data.team_id, task_type), from_attributes=True)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("")
def list_tasks(
    status: TaskStatus | None = None,
    task_type: str | None = None,
    round_id: int | None = None,
    since: datetime | None = None,
    auth_data: AuthData = Depends(authenticate_player),
    player_service: PlayerService = Depends(get_player_service)
) -> list[Task]:
    if auth_data.team_id is None:
        raise HTTPException(status_code=400, detail="Team not found")

    tasks = player_service.list_tasks_for_team(
        auth_data.team_id,
        status=status,
        task_type=task_type,
        round_id=round_id,
        since=since
    )
    return [Task.model_validate(t, from_attributes=True) for t in tasks]
