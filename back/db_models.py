from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from api_models import TaskStatus, SubmissionStatus


class ChallengeDocument(BaseModel):
    id: str
    title: str
    description: str  # markdown
    current_round_id: Optional[str] = None


class TeamDocument(BaseModel):
    id: str
    challenge_id: str  # denormalized
    name: str
    members: str
    deleted: bool = False
    captain_contact: str


class APIKeyDocument(BaseModel):
    key: str
    challenge_id: str | None = None # denormalized
    role: str  # "player" | "admin"
    team_id: str | None = None


class TaskTypeDocument(BaseModel):
    type: str
    n_tasks: int
    generator_url: str
    generator_settings: str
    generator_secret: str
    score: int
    time_to_solve: int
    score_decay_with_time: bool
    n_attempts: int


class RoundDocument(BaseModel):
    id: str
    challenge_id: str  # denormalized
    published: bool
    claim_by_type: bool
    start_time: datetime
    end_time: datetime
    deleted: bool = False
    task_types: list[TaskTypeDocument]

    def get_task_type(self, task_type: str) -> TaskTypeDocument | None:
        for tt in self.task_types:
            if tt.type == task_type:
                return tt
        return None

class TaskDocument(BaseModel):
    id: str
    challenge_id: str  # denormalized
    team_id: str  # denormalized
    round_id: str  # denormalized
    type: str
    status: TaskStatus
    statement: str
    input: str
    checker_hint: str
    score: int
    claimed_at: datetime
    solved_at: Optional[datetime] = None


class SubmissionDocument(BaseModel):
    id: str
    challenge_id: str  # denormalized
    team_id: str  # denormalized
    round_id: str  # denormalized
    task_id: str
    status: SubmissionStatus
    submitted_at: datetime
    answer: str
    checker_output: str
    score: int


class TeamTaskDashboardDocument(BaseModel):
    task_type: str
    score: int
    ac: int
    wa: int
    pending: int


class TeamDashboardDocument(BaseModel):
    team_id: str
    challenge_id: str  # denormalized
    round_id: str  # denormalized
    score: int
    task_types: list[TeamTaskDashboardDocument]
