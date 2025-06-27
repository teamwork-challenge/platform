from sqlalchemy import select
from sqlalchemy.orm import Session

from api_models import Task, Team
from db_models import Team, Task


class PlayerService:
    def __init__(self, db: Session):
        self.db = db

    def get_task(self, task_id: int):
        stmt = select(Task).where(Task.id == task_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_team(self, team_id: int) -> Team:
        stmt = select(Team).where(Team.id == team_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def create_task(self, challenge_id: int, team_id: int, task_type: str) -> Task:
        return None
