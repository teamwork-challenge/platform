from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException

from api_models import Team, TeamsImportRequest, TeamsImportResponse, UserRole, AuthData
from back.api_deps import authenticate_player, authenticate_admin, get_player_service, get_admin_service, get_challenge_or_404
from back.player_service import PlayerService
from back.admin_service import AdminService
from back.db_models import Team as DbTeam

router = APIRouter(prefix="", tags=["Team"]) 


# Player: auth & team
@router.get("/auth", response_model=UserRole)
def auth(auth_data: AuthData = Depends(authenticate_player)) -> UserRole:
    return auth_data.role


@router.get("/team", response_model=Team)
def get_team(
    auth_data: AuthData = Depends(authenticate_player),
    player_service: PlayerService = Depends(get_player_service)
) -> DbTeam:
    if auth_data.team_id is None:
        raise HTTPException(status_code=404, detail="Team not found")
    team = player_service.get_team(auth_data.team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


# Admin: teams management
@router.get("/teams", response_model=list[Team])
def get_teams(
    challenge_id: int | None = None,
    admin_service: AdminService = Depends(get_admin_service),
    auth_data: AuthData = Depends(authenticate_admin)
) -> Sequence[DbTeam]:
    if challenge_id is not None:
        # Check if the challenge exists
        get_challenge_or_404(challenge_id, admin_service, auth_data, "GET")
        # Get teams for the specified challenge
        return admin_service.get_teams_by_challenge(challenge_id)
    else:
        # Get all teams
        return admin_service.get_all_teams()


@router.post("/teams", response_model=TeamsImportResponse)
def create_teams(
    request: TeamsImportRequest,
    admin_service: AdminService = Depends(get_admin_service),
    auth_data: AuthData = Depends(authenticate_admin)
) -> TeamsImportResponse:
    challenge = get_challenge_or_404(request.challenge_id, admin_service, auth_data, "POST")
    teams_data = admin_service.create_teams(challenge, request.teams)
    teams = [Team.model_validate(team) for team in teams_data]
    return TeamsImportResponse(challenge_id=challenge.id, teams=teams)
