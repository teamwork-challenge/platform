from typing import Any
from fastapi import APIRouter, Depends, HTTPException

from api_models import Submission, AuthData, UserRole
from back.api.deps import authenticate_player, authenticate_admin, get_task_service, fix_challenge_id, fix_round_id
from back.services.task_service import TaskService
from typing import Optional

router = APIRouter(prefix="/challenges/{challenge_id}/rounds/{round_id}", tags=["Submissions"])




@router.get("/submissions")
def unified_list_submissions(
    challenge_id: str,
    round_id: str,
    task_id: Optional[str] = None,
    team_id: Optional[str] = None,
    auth_data: AuthData = Depends(authenticate_player),
    task_service: TaskService = Depends(get_task_service)
) -> Any:
    """
    Unified endpoint to list submissions.
    - If task_id is provided: list submissions for that task (player can access only own team's tasks).
    - If team_id is provided and user is admin: return last submission for that team.
    - If neither task_id nor team_id provided and user is admin: return last submission for all teams.
    """
    challenge_id = fix_challenge_id(auth_data, challenge_id)
    round_id = fix_round_id(auth_data, round_id)

    if task_id:
        # Validate access to the task
        task_doc = task_service.get_task(task_id, challenge_id, round_id)
        if task_doc is None:
            raise HTTPException(status_code=404, detail="Task not found")
        if task_doc.challenge_id != challenge_id or (auth_data.role == UserRole.PLAYER and task_doc.team_id != auth_data.team_id):
            raise HTTPException(status_code=403, detail="Access to this task is forbidden")
        subs = task_service.list_submissions_for_task(challenge_id, round_id, task_id)
        return [Submission.model_validate(s, from_attributes=True).model_dump() for s in subs]

    if team_id:
        # Only admin can request arbitrary team; player can request only their team
        if auth_data.role == UserRole.PLAYER:
            if auth_data.team_id is None or team_id != auth_data.team_id:
                raise HTTPException(status_code=403, detail="Forbidden for other team")
        sub = task_service.get_last_submission_for_team(challenge_id, round_id, team_id)
        if sub is None:
            raise HTTPException(status_code=404, detail="No submissions yet")
        return Submission.model_validate(sub, from_attributes=True).model_dump()

    # No params -> admin-only: last for all teams
    if auth_data.role != UserRole.ADMIN:
        raise HTTPException(status_code=400, detail="Either task_id or team_id must be provided")
    results = task_service.get_last_submission_for_all_teams(challenge_id, round_id)
    return [
        {"team_id": tid, "submission": Submission.model_validate(sub, from_attributes=True).model_dump()}
        for tid, sub in results.items()
    ]
