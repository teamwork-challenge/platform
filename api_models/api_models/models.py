from dataclasses import dataclass

from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime


class UserRole(str, Enum):
    ADMIN = "admin"
    PLAYER = "player"


class RoundStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    AC = "AC"
    WA = "WA"


class SubmissionStatus(str, Enum):
    AC = "AC"
    WA = "WA"


class Submission(BaseModel):
    """Submission information."""
    id: str
    status: SubmissionStatus
    submitted_at: str
    task_id: Optional[str] = None
    answer: Optional[str] = None

    class Config:
        from_attributes = True


class AuthData(BaseModel):
    key: str
    role: UserRole
    team_id: Optional[int] = None
    challenge_id: Optional[int] = None
    round_id: Optional[int] = None


class Challenge(BaseModel):
    id: int
    title: str
    description: str
    current_round_id: Optional[int] = None
    deleted: bool = False

    class Config:
        from_attributes = True


class ChallengeCreateRequest(BaseModel):
    title: str
    description: str

    class Config:
        from_attributes = True


class ChallengeUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    deleted: Optional[bool] = None
    current_round_id: Optional[int] = None

    class Config:
        from_attributes = True


class Task(BaseModel):
    id: str
    title: str
    type: str
    status: TaskStatus = TaskStatus.PENDING
    score: int
    time_remaining: str
    statement: Optional[str] = None
    input: Optional[str] = None
    submissions: List[Submission] = []
    last_attempt_at: Optional[str] = None
    solved_at: Optional[str] = None

    class Config:
        from_attributes = True


class Team(BaseModel):
    id: int
    challenge_id: int
    name: str
    members: str
    captain_contact: str
    api_key: str
    total_score: int

    class Config:
        from_attributes = True


class TeamsImportResponse(BaseModel):
    challenge_id: int
    teams: List[Team]

    class Config:
        from_attributes = True


class TeamCreateRequest(BaseModel):
    name: str
    members: str
    captain_contact: str

    class Config:
        from_attributes = True


class TeamsImportRequest(BaseModel):
    challenge_id: int
    teams: List[TeamCreateRequest]

    class Config:
        from_attributes = True


class RoundTaskType(BaseModel):
    id: int
    round_id: int
    type: str
    max_tasks_per_team: int
    generator_url: str
    generator_settings: Optional[str] = None
    generator_secret: str

    class Config:
        from_attributes = True


class Round(BaseModel):
    id: int
    challenge_id: int
    index: int
    status: RoundStatus = RoundStatus.DRAFT
    start_time: datetime
    end_time: datetime
    claim_by_type: bool = False
    allow_resubmit: bool = False
    score_decay: str = "no"
    task_types: Optional[List[RoundTaskType]] = None

    class Config:
        from_attributes = True


class RoundCreateRequest(BaseModel):
    challenge_id: int
    index: int
    start_time: datetime
    end_time: datetime
    claim_by_type: bool = False
    allow_resubmit: bool = False
    score_decay: str = "no"
    status: RoundStatus = RoundStatus.DRAFT

    class Config:
        from_attributes = True


class RoundTaskTypeCreateRequest(BaseModel):
    round_id: int
    type: str
    generator_url: str
    generator_settings: Optional[str] = None
    generator_secret: str
    max_tasks_per_team: Optional[int] = None

    class Config:
        from_attributes = True


class SubmissionExtended(BaseModel):
    """Extended submission information with the explanation and score."""
    id: str
    status: str
    submitted_at: str
    task_id: Optional[str] = None
    answer: Optional[str] = None
    explanation: Optional[str] = None
    score: Optional[int] = None
    
    class Config:
        from_attributes = True


class TaskList(BaseModel):
    """List of tasks."""
    tasks: List[Task]

    class Config:
        from_attributes = True


class TypeStats(BaseModel):
    """Statistics for a task type."""
    total: int
    pending: int
    ac: int
    wa: int
    remaining: int

    class Config:
        from_attributes = True


class Dashboard(BaseModel):
    """Dashboard with task statistics."""
    round_id: int
    stats: Dict[str, TypeStats]

    class Config:
        from_attributes = True


class TeamScore(BaseModel):
    """Team score information."""
    rank: int
    name: str
    total_score: int
    scores: Dict[str, int]

    class Config:
        from_attributes = True


class Leaderboard(BaseModel):
    """Leaderboard with team scores."""
    round_id: int
    teams: List[TeamScore]

    class Config:
        from_attributes = True


class RoundList(BaseModel):
    """List of rounds."""
    rounds: List[Round]

    class Config:
        from_attributes = True


class SubmitAnswerRequest(BaseModel):
    """Request model for submitting an answer to a task."""
    answer: str

    class Config:
        from_attributes = True
