from sqlalchemy.orm import Session
from sqlalchemy import select

from api_models import AuthData, UserRole
from db_models import AdminKeys, Team, Challenge

class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def get_auth_data(self, api_key: str) -> AuthData | None:
        stmt = select(AdminKeys).where(AdminKeys.api_key == api_key)
        key = self.db.execute(stmt).scalar_one_or_none()
        if key is not None:
            return AuthData(
                key=key.api_key,
                role=UserRole.ADMIN,
            )
        stmt = select(Team).where(Team.api_key == api_key)
        team = self.db.execute(stmt).scalar_one_or_none()
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


