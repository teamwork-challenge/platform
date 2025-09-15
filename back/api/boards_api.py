from typing import Optional

from fastapi import APIRouter, Depends

from api_models import Dashboard, AuthData, Leaderboard
from back.api.deps import authenticate_player, fix_round_id, get_board_service
from back.services.boards_service import BoardService

router = APIRouter(prefix="", tags=["Leaderboard & Dashboard"])


@router.get("/dashboard")
def get_dashboard(
    round_id: Optional[str] = None,
    board_service: BoardService = Depends(get_board_service),
    auth_data: AuthData = Depends(authenticate_player)
) -> Dashboard:
    if round_id is not None:
        round_id = fix_round_id(auth_data, round_id)
    return board_service.get_dashboard(auth_data, round_id)


@router.get("/leaderboard")
def get_leaderboard(
    round_id: Optional[str] = None,
    board_service: BoardService = Depends(get_board_service),
    auth_data: AuthData = Depends(authenticate_player)
) -> Leaderboard:
    if round_id is not None:
        round_id = fix_round_id(auth_data, round_id)
    return board_service.get_leaderboard(auth_data, round_id)