from fastapi import APIRouter, Depends, HTTPException

from back.api_deps import fix_challenge_id
from api_models import Team, TeamsImportRequest, TeamsImportResponse, UserRole, AuthData, RenameTeamRequest
from back.api_deps import authenticate_player, authenticate_admin, get_team_service, get_challenge_service, \
    get_challenge_or_404
from back.firebase_challenge_service import ChallengeService
from back.firebase_team_service import TeamService

router = APIRouter(prefix="", tags=["Team"])


# Player: auth & team
@router.get("/auth")
def auth(auth_data: AuthData = Depends(authenticate_player)) -> UserRole:
    return auth_data.role


@router.get("/team")
def get_team(
    auth_data: AuthData = Depends(authenticate_player),
    team_service: TeamService = Depends(get_team_service)
) -> Team:
    if auth_data.team_id is None:
        raise HTTPException(status_code=404, detail="No Team")
    if auth_data.challenge_id is None:
        raise HTTPException(status_code=404, detail="No Challenge")
    team = team_service.get_team(auth_data.team_id, auth_data.challenge_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return Team.model_validate(team, from_attributes=True)


@router.put("/team")
def rename_team(
    request: RenameTeamRequest,
    auth_data: AuthData = Depends(authenticate_player),
    team_service: TeamService = Depends(get_team_service)
) -> Team:
    if auth_data.team_id is None:
        raise HTTPException(status_code=404, detail="Team not found")
    if auth_data.challenge_id is None:
        raise HTTPException(status_code=404, detail="Challenge not found")
    updated = team_service.rename_team(auth_data.team_id, auth_data.challenge_id, request.name)
    return Team.model_validate(updated, from_attributes=True)


# Admin: teams management
@router.get("/challenges/{challenge_id}/teams")
def get_teams(
    challenge_id: str,
    team_service: TeamService = Depends(get_team_service),
    auth_data: AuthData = Depends(authenticate_admin)
) -> list[Team]:
    challenge_id = fix_challenge_id(auth_data, challenge_id)
    teams = team_service.get_teams_by_challenge(challenge_id)
    return [Team.model_validate(t, from_attributes=True) for t in teams]


@router.post("/teams")
def create_teams(
    request: TeamsImportRequest,
    challenge_service: ChallengeService = Depends(get_challenge_service),
    team_service: TeamService = Depends(get_team_service),
    auth_data: AuthData = Depends(authenticate_admin)
) -> TeamsImportResponse:
    challenge = get_challenge_or_404(request.challenge_id, challenge_service, auth_data)
    teams_data = team_service.create_teams(challenge.id, request.teams)
    teams = [Team.model_validate(team, from_attributes=True) for team in teams_data]
    return TeamsImportResponse(challenge_id=challenge.id, teams=teams)
