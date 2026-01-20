from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from api_models import Task, SubmitAnswerRequest, Submission, AuthData, UserRole, TaskWithHint
from api_models import TaskStatus
from back.api.deps import authenticate_player, authenticate_admin, get_task_service, get_challenge_service, get_round_or_404, fix_challenge_id, fix_round_id
from back.services.challenge_service import ChallengeService
from back.services.task_service import TaskService

router = APIRouter(prefix="/challenges/{challenge_id}/rounds/{round_id}", tags=["Tasks"])

# Explicit error message to HTTP status code mapping
# Status codes: 400 = Bad Request, 409 = Conflict
TASK_ERROR_MAPPING: dict[str, int] = {
    # Resource limit errors (409 Conflict)
    "Maximum number of tasks": 409,
    "already taken": 409,
    "All tasks were already taken": 409,
    # Validation errors (400 Bad Request)
    "Challenge not found": 400,
    "Round not found": 400,
    "Round is not published": 400,
    "Round has not started yet": 400,
    "Round has already ended": 400,
    "No task type found": 400,
    "Task not found": 400,
    "Task does not belong to this team": 400,
    "Task type not found": 400,
    "Attempts limit exceeded": 400,
    "Time limit exceeded": 400,
}

def map_value_error_to_http(e: ValueError) -> HTTPException:
    """Map ValueError to appropriate HTTPException with explicit status code."""
    msg = str(e)
    
    # Check for exact matches first
    for error_key, status_code in TASK_ERROR_MAPPING.items():
        if error_key in msg:
            return HTTPException(status_code=status_code, detail=msg)
    
    # Default fallback for unmapped errors
    return HTTPException(status_code=400, detail=msg)


@router.get("/tasks")
def list_tasks(
    challenge_id: str,
    round_id: str,
    status: TaskStatus | None = None,
    task_type: str | None = None,
    since: datetime | None = None,
    auth_data: AuthData = Depends(authenticate_player),
    task_service: TaskService = Depends(get_task_service)
) -> list[Task]:
    if auth_data.team_id is None:
        raise HTTPException(status_code=400, detail="Team not found")
    challenge_id = fix_challenge_id(auth_data, challenge_id)
    round_id = fix_round_id(auth_data, round_id)
    tasks = task_service.list_tasks_for_team(
        auth_data.team_id,
        challenge_id,
        status=status,
        task_type=task_type,
        round_id=round_id,
        since=since
    )
    return [Task.model_validate(t, from_attributes=True) for t in tasks]


@router.post("/tasks")
def create_task(
    challenge_id: str,
    round_id: str,
    task_type: str | None = None,
    auth_data: AuthData = Depends(authenticate_player),
    task_service: TaskService = Depends(get_task_service),
    challenge_service: ChallengeService = Depends(get_challenge_service)
) -> Task:
    if auth_data.team_id is None:
        raise HTTPException(status_code=400, detail="Team not found")
    challenge_id = fix_challenge_id(auth_data, challenge_id)
    round_id = fix_round_id(auth_data, round_id)
    game_round = get_round_or_404(round_id, challenge_id, challenge_service, auth_data)
    if auth_data.team_id is None:
        raise HTTPException(status_code=400, detail="Invalid team context")
    if task_type is None:
        try:
            task_type = task_service.get_random_task_type(game_round, auth_data.team_id).type
        except ValueError as e:
            raise map_value_error_to_http(e)
    elif not game_round.claim_by_type:
        raise HTTPException(status_code=400, detail="Round does not allow task creation by type")
    try:
        created = task_service.create_task(challenge_id, round_id, auth_data.team_id, task_type)
    except ValueError as e:
        raise map_value_error_to_http(e)
    except Exception as e:
        msg = str(e)
        if "Failed to commit transaction" in msg:
            raise HTTPException(status_code=409, detail=msg)
        raise
    return Task.model_validate(created, from_attributes=True)


@router.get("/tasks/{task_id}")
def get_task(
    task_id: str,
    challenge_id: str,
    round_id: str,
    auth_data: AuthData = Depends(authenticate_player),
    task_service: TaskService = Depends(get_task_service)
) -> Task:
    challenge_id = fix_challenge_id(auth_data, challenge_id)
    round_id = fix_round_id(auth_data, round_id)
    task_doc = task_service.get_task(task_id, challenge_id, round_id)
    if task_doc is None:
        raise HTTPException(status_code=404, detail="Task not in the DB")
    if task_doc.challenge_id != challenge_id or (auth_data.role == UserRole.PLAYER and task_doc.team_id != auth_data.team_id):
        raise HTTPException(status_code=403, detail="Access to this task is forbidden")
    submissions = task_service.list_submissions_for_task(task_doc.challenge_id, task_doc.round_id, task_doc.id)
    answer = Task.model_validate(task_doc, from_attributes=True)
    answer.submissions = submissions
    return answer


@router.post("/submissions")
def submit_task_answer(
    challenge_id: str,
    round_id: str,
    submission: SubmitAnswerRequest,
    auth_data: AuthData = Depends(authenticate_player),
    task_service: TaskService = Depends(get_task_service)
) -> Submission:
    if auth_data.team_id is None:
        raise HTTPException(status_code=400, detail="Team not found")
    challenge_id = fix_challenge_id(auth_data, challenge_id)
    round_id = fix_round_id(auth_data, round_id)
    try:
        return task_service.submit_task_answer(submission.task_id, auth_data.team_id, challenge_id, round_id, submission.answer)
    except ValueError as e:
        raise map_value_error_to_http(e)


@router.get("/tasks/report/{task_type}")
def generate_tasks_report(
    task_type: str,
    challenge_id: str,
    round_id: str,
    auth_data: AuthData = Depends(authenticate_admin),  # Admin only!
    task_service: TaskService = Depends(get_task_service)
) -> list[TaskWithHint]:
    """Generate all tasks of a specific type for reporting (admin only).
    Calls task generator /gen endpoint repeatedly and returns tasks with checker_hint.
    """
    challenge_id = fix_challenge_id(auth_data, challenge_id)
    round_id = fix_round_id(auth_data, round_id)
    
    try:
        generated_tasks = task_service.generate_tasks_for_report(
            challenge_id,
            round_id,
            task_type
        )
        
        # Convert GenResponse to TaskWithHint
        return [
            TaskWithHint(
                statement=task.statement,
                input=task.input,
                checker_hint=task.checker_hint,
                statement_version=task.statement_version
            )
            for task in generated_tasks
        ]
    except ValueError as e:
        raise map_value_error_to_http(e)
