from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from api_models import Task, SubmitAnswerRequest, Submission, AuthData
from api_models import TaskStatus
from back.api_deps import authenticate_player, get_task_service, get_challenge_service, get_round_or_404, \
    get_task_or_404
from back.firebase_challenge_service import ChallengeService
from back.firebase_task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["Tasks"]) 


@router.get("/{task_id}")
def get_task(
    task_id: str,
    auth_data: AuthData = Depends(authenticate_player),
    task_service: TaskService = Depends(get_task_service)
) -> Task:
    # Use the existing helper for access checks, then map Firestore TaskDocument to API Task
    db_task = get_task_or_404(task_id, task_service, auth_data)
    return Task.model_validate({
        'id': db_task.id,
        'title': f"{db_task.type} Task",
        'type': db_task.type,
        'status': db_task.status,
        'score': db_task.score,
        'statement': getattr(db_task, 'statement', None),
        'input': getattr(db_task, 'input', None),
        'claimed_at': db_task.claimed_at,
        'submissions': [],
        'last_attempt_at': db_task.claimed_at,
        'solved_at': getattr(db_task, 'solved_at', None)
    })


@router.post("/{task_id}/submission")
def submit_task_answer(
    task_id: str,
    answer_data: SubmitAnswerRequest,
    auth_data: AuthData = Depends(authenticate_player),
    task_service: TaskService = Depends(get_task_service)
) -> Submission:
    answer = answer_data.answer
    try:
        if auth_data.team_id is None or auth_data.challenge_id is None or auth_data.round_id is None:
            raise HTTPException(status_code=400, detail="Team, challenge or round not found")
        submission = task_service.submit_task_answer(task_id, auth_data.team_id, auth_data.challenge_id, auth_data.round_id, answer)
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
    if auth_data.challenge_id is None:
        raise HTTPException(status_code=400, detail="Challenge not found")
    game_round = get_round_or_404(auth_data.round_id, auth_data.challenge_id, challenge_service, auth_data)
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
    round_id: str | None = None,
    since: datetime | None = None,
    auth_data: AuthData = Depends(authenticate_player),
    task_service: TaskService = Depends(get_task_service)
) -> list[Task]:
    if auth_data.team_id is None:
        raise HTTPException(status_code=400, detail="Team not found")
    if auth_data.challenge_id is None:
        raise HTTPException(status_code=400, detail="Challenge not found")

    tasks = task_service.list_tasks_for_team(
        auth_data.team_id,
        auth_data.challenge_id,
        status=status,
        task_type=task_type,
        round_id=round_id,
        since=since
    )
    return [Task.model_validate(t, from_attributes=True) for t in tasks]
