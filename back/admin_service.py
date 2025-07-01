from sqlalchemy import select
from sqlalchemy.orm import Session
import uuid

from db_models import Challenge, Team


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

    def create_team_api_key(self, team_id: int, challenge_id: int):
        # Check if the team exists
        stmt = select(Team).where(Team.id == team_id, Team.challenge_id == challenge_id)
        team = self.db.execute(stmt).scalar_one_or_none()

        if team is None:
            return None

        # Generate a new API key
        new_api_key = str(uuid.uuid4())

        # Update the team's API key
        team.api_key = new_api_key
        self.db.commit()
        self.db.refresh(team)

        return team
