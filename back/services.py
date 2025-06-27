from sqlalchemy.orm import Session
from sqlalchemy import select

from models import AuthData, UserRole
from models_orm import Challenge, Task, AdminKeys, Team


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
            return AuthData(
                key=team.api_key,
                role=UserRole.PLAYER,
                team_id=team.id,
                challenge_id=team.challenge_id,
            )
        return None


class AdminService:
    def __init__(self, db: Session):
        self.db = db

    def get_challenge(self, challenge_id: int) -> Challenge | None:
        stmt = select(Challenge).where(Challenge.id == challenge_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_all_challenges(self):
        return self.db.execute(select(Challenge)).scalars().all()

    def create_challenge(self, title: str, description: str):
        challenge = Challenge(title=title, description=description)
        self.db.add(challenge)
        self.db.commit()
        self.db.refresh(challenge)
        return challenge


    def update_challenge(self, challenge_id: int, title: str, description: str):
        stmt = select(Challenge).where(Challenge.id == challenge_id)
        challenge = self.db.execute(stmt).scalar_one_or_none()
        if challenge:
            challenge.title = title
            challenge.description = description
            self.db.commit()
            self.db.refresh(challenge)
            return challenge
        return None

    def delete_challenge(self, challenge_id: int):
        stmt = select(Challenge).where(Challenge.id == challenge_id)
        challenge = self.db.execute(stmt).scalar_one_or_none()
        if challenge:
            self.db.delete(challenge)
            self.db.commit()
            return challenge
        return None
from models_orm import Task

class PlayerService:
    def __init__(self, db: Session):
        self.db = db

    def get_task(self, task_id: int):
        stmt = select(Task).where(Task.id == task_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def create_task(self, challenge_id: int, title: str, status: str = "PENDING"):
        return None
