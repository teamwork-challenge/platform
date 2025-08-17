from typing import Sequence

from datetime import datetime
from api_models import TaskStatus
from fastapi import APIRouter, Depends, HTTPException

from api_models import Task, SubmitAnswerRequest, Submission, AuthData
from back.api_deps import authenticate_player, get_task_service, get_challenge_service, get_round_or_404, get_task_or_404
from back.task_service import TaskService
from back.challenge_service import ChallengeService
from back.db_models import Task as DbTask

router = APIRouter(prefix="/tasks", tags=["Tasks"]) 


@router.get("/{task_id}")
def get_task(
    task_id: int,
    auth_data: AuthData = Depends(authenticate_player),
    task_service: TaskService = Depends(get_task_service)
) -> Task:
    return Task.model_validate(get_task_or_404(task_id, task_service, auth_data), from_attributes=True)


@router.post("/{task_id}/submission")
def submit_task_answer(
    task_id: int,
    answer_data: SubmitAnswerRequest,
    auth_data: AuthData = Depends(authenticate_player),
    task_service: TaskService = Depends(get_task_service)
) -> Submission:
    answer = answer_data.answer
    try:
        if auth_data.team_id is None:
            raise HTTPException(status_code=400, detail="Team not found")
        submission = task_service.submit_task_answer(task_id, auth_data.team_id, answer)
        return Submission.model_validate(submission, from_attributes=True)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("")
def create_task(
    task_type: str | None = None,
    auth_data: AuthData = Depends(authenticate_player),
    task_service: TaskService = Depends(get_task_service),
    challenge_service: ChallengeService = Depends(get_challenge_service)
) -> Task:
    if auth_data.round_id is None:
        raise HTTPException(status_code=400, detail="No current round available")
    game_round = get_round_or_404(auth_data.round_id, challenge_service, auth_data)
    try:
        if auth_data.challenge_id is None or auth_data.team_id is None:
            raise HTTPException(status_code=400, detail="Invalid team or challenge context")
        if task_type is None:
            task_type = task_service.get_random_task_type(game_round, auth_data.team_id).type
        elif not game_round.claim_by_type:
            raise HTTPException(status_code=400, detail="Round does not allow task creation by type")
        return Task.model_validate(task_service.create_task(auth_data.challenge_id, auth_data.team_id, task_type), from_attributes=True)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("")
def list_tasks(
    status: TaskStatus | None = None,
    task_type: str | None = None,
    round_id: int | None = None,
    since: datetime | None = None,
    auth_data: AuthData = Depends(authenticate_player),
    task_service: TaskService = Depends(get_task_service)
) -> list[Task]:
    if auth_data.team_id is None:
        raise HTTPException(status_code=400, detail="Team not found")

    tasks = task_service.list_tasks_for_team(
        auth_data.team_id,
        status=status,
        task_type=task_type,
        round_id=round_id,
        since=since
    )
    return [Task.model_validate(t, from_attributes=True) for t in tasks]
