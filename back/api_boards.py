from fastapi import APIRouter, Depends, HTTPException

from api_models import AuthData, Dashboard
from back.challenge_service import ChallengeService
from back.boards_service import BoardsService
from back.api_deps import (
    authenticate_player,
    get_challenge_service,
    get_round_or_404,
    get_boards_service,
)
router = APIRouter(prefix="", tags=["Leaderboard & Dashboard"])


@router.get("/dashboard")
def dashboard(
    round_id: int | None = None,
    auth_data: AuthData = Depends(authenticate_player),
    boards_service: BoardsService = Depends(get_boards_service),
    challenge_service: ChallengeService = Depends(get_challenge_service),
) -> Dashboard:
    resolved_round_id = round_id if round_id is not None else auth_data.round_id
    if resolved_round_id is None:
        raise HTTPException(status_code=404, detail="No current round available")
    get_round_or_404(resolved_round_id, challenge_service, auth_data)
    if auth_data.team_id is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return boards_service.get_dashboard(auth_data.team_id, resolved_round_id)