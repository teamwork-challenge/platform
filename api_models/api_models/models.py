from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from enum import StrEnum
from datetime import datetime


class DeleteResponse(BaseModel):
    deleted_id: str


class UserRole(StrEnum):
    ADMIN = "admin"
    PLAYER = "player"


class RoundStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"


class TaskStatus(StrEnum):
    PENDING = "pending"
    AC = "ac"
    WA = "wa"


class SubmissionStatus(StrEnum):
    AC = "ac"
    WA = "wa"


class AuthData(BaseModel):
    key: str
    role: UserRole
    team_id: Optional[str] = None
    challenge_id: Optional[str] = None
    round_id: Optional[str] = None


class Challenge(BaseModel):
    id: str
    title: str
    description: str
    deleted: bool
    current_round_id: Optional[str] = None


class ChallengeCreateRequest(BaseModel):
    title: str
    description: str


class ChallengeUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    deleted: Optional[bool] = None
    current_round_id: Optional[str] = None


class SubmitAnswerRequest(BaseModel):
    answer: str


class Submission(BaseModel):
    id: str
    status: SubmissionStatus
    submitted_at: datetime
    task_id: Optional[str] = None
    answer: Optional[str] = None
    explanation: Optional[str] = None
    score: Optional[int] = None


class Task(BaseModel):
    id: str
    title: str
    type: str
    status: TaskStatus = TaskStatus.PENDING
    score: int
    statement: Optional[str] = None
    input: Optional[str] = None
    claimed_at: Optional[datetime] = None
    submissions: List[Submission] = Field(default_factory=list)
    last_attempt_at: Optional[datetime] = None
    solved_at: Optional[datetime] = None


class TaskList(BaseModel):
    tasks: List[Task]


class Team(BaseModel):
    id: str
    challenge_id: str
    name: str
    members: str
    captain_contact: str
    api_key: str = ""


class TeamsImportResponse(BaseModel):
    challenge_id: str
    teams: List[Team]


class TeamCreateRequest(BaseModel):
    name: str
    members: str
    captain_contact: str


class TeamsImportRequest(BaseModel):
    challenge_id: str
    teams: List[TeamCreateRequest]


class TeamScore(BaseModel):
    rank: int
    name: str
    total_score: int
    scores: Dict[str, int]


class RoundTaskType(BaseModel):
    id: str
    round_id: str
    type: str
    max_tasks_per_team: int
    generator_url: str
    generator_settings: Optional[str] = None
    generator_secret: str
    score: int = 100
    time_to_solve: int


class Round(BaseModel):
    id: str
    challenge_id: str
    published: bool = False
    deleted: bool = False
    start_time: datetime
    end_time: datetime
    claim_by_type: bool = False
    task_types: Optional[List[RoundTaskType]] = None


class RoundCreateRequest(BaseModel):
    challenge_id: str
    start_time: datetime
    end_time: datetime
    claim_by_type: bool = False


class RoundUpdateRequest(BaseModel):
    start_time: datetime | None = None
    end_time: datetime | None = None
    claim_by_type: bool | None = None
    published: bool | None = None


class RoundList(BaseModel):
    rounds: List[Round]


class RoundTaskTypeCreateRequest(BaseModel):
    round_id: str
    type: str
    generator_url: str
    generator_settings: Optional[str] = None
    generator_secret: str
    max_tasks_per_team: Optional[int] = None
    score: Optional[int] = 100
    time_to_solve: int

class RoundTaskTypeUpdateRequest(BaseModel):
    round_id: str
    type: str
    generator_url: str
    generator_settings: Optional[str] = None
    generator_secret: str
    max_tasks_per_team: Optional[int] = None
    score: Optional[int] = 100
    time_to_solve: int


class TypeStats(BaseModel):
    """Statistics for a task type."""
    total: int
    pending: int
    ac: int
    wa: int
    remaining: int


class Dashboard(BaseModel):
    """Dashboard with task statistics."""
    round_id: str
    stats: Dict[str, TypeStats]


class Leaderboard(BaseModel):
    """Leaderboard with team scores."""
    round_id: str
    teams: List[TeamScore]
