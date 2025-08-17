from typing import Sequence, List

import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from api_models import TeamCreateRequest, AuthData, UserRole
from back.db_models import Team, Challenge, AdminKeys


class TeamService:
    def __init__(self, db: Session):
        self.db = db

    def get_team(self, team_id: int) -> Team | None:
        stmt = select(Team).where(Team.id == team_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def create_teams(self, challenge: Challenge, teams: List[TeamCreateRequest]) -> list[Team]:
        created_teams: list[Team] = []
        for team_data in teams:
            team_name = team_data.name
            members = team_data.members
            captain_contact = team_data.captain_contact

            api_key = str(uuid.uuid4())

            team = Team(
                api_key=api_key,
                challenge_id=challenge.id,
                name=team_name,
                members=members,
                captain_contact=captain_contact,
                total_score=0
            )

            self.db.add(team)
            self.db.flush()

            created_teams.append(team)

        self.db.commit()

        return created_teams

    def get_teams_by_challenge(self, challenge_id: int) -> Sequence[Team]:
        stmt = select(Team).where(Team.challenge_id == challenge_id)
        return self.db.execute(stmt).scalars().all()

    def get_all_teams(self) -> Sequence[Team]:
        stmt = select(Team)
        return self.db.execute(stmt).scalars().all()

    def get_auth_data(self, api_key: str) -> AuthData | None:
        keys_query = select(AdminKeys).where(AdminKeys.api_key == api_key)
        key = self.db.execute(keys_query).scalar_one_or_none()
        if key is not None:
            return AuthData(
                key=key.api_key,
                role=UserRole.ADMIN,
            )
        team_query = select(Team).where(Team.api_key == api_key)
        team = self.db.execute(team_query).scalar_one_or_none()
        if team is not None:
            # Get the challenge to retrieve current_round_id
            stmt = select(Challenge).where(Challenge.id == team.challenge_id)
            challenge = self.db.execute(stmt).scalar_one_or_none()
            current_round_id = challenge.current_round_id if challenge else None

            return AuthData(
                key=team.api_key,
                role=UserRole.PLAYER,
                team_id=team.id,
                challenge_id=team.challenge_id,
                round_id=current_round_id,
            )
        return None
