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
    current_round_id: Optional[str] = None


class ChallengeCreateRequest(BaseModel):
    title: str
    description: str


class ChallengeUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    current_round_id: Optional[str] = None


class SubmitAnswerRequest(BaseModel):
    answer: str


class Submission(BaseModel):
    id: str
    status: SubmissionStatus
    submitted_at: datetime
    task_id: str
    answer: str
    checker_output: str
    score: int


class Task(BaseModel):
    id: str
    type: str
    status: TaskStatus = TaskStatus.PENDING
    score: int
    statement: str
    input: str
    claimed_at: datetime
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
    type: str
    n_tasks: int
    generator_url: str
    generator_settings: str
    generator_secret: str
    score: int
    time_to_solve: int


class Round(BaseModel):
    id: str
    challenge_id: str
    published: bool
    start_time: datetime
    end_time: datetime
    claim_by_type: bool
    task_types: Optional[List[RoundTaskType]] = None


class RoundList(BaseModel):
    rounds: List[Round]


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
