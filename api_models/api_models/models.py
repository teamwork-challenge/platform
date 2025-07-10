from dataclasses import dataclass
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime

class UserRole(str, Enum):
    ADMIN = "admin"
    PLAYER = "player"


class AuthData(BaseModel):
    key: str
    role: UserRole
    team_id: Optional[int] = None
    challenge_id: Optional[int] = None


class Challenge(BaseModel):
    id: int
    title: str
    description: str
    current_round_id: Optional[int] = None

    class Config:
        from_attributes = True


class ChallengeCreateRequest(BaseModel):
    title: str
    description: str

    class Config:
        from_attributes = True


class Task(BaseModel):
    title: str
    status: str = "PENDING"

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
    generator_url: str
    generator_settings: Optional[str] = None
    generator_secret: str

    class Config:
        from_attributes = True


class Round(BaseModel):
    id: int
    challenge_id: int
    index: int
    status: str = "draft"
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
    status: str = "draft"

    class Config:
        from_attributes = True


class RoundTaskTypeCreateRequest(BaseModel):
    round_id: int
    type: str
    generator_url: str
    generator_settings: Optional[str] = None
    generator_secret: str

    class Config:
        from_attributes = True


@dataclass
class Submission:
    """Submission information."""
    id: str
    status: str
    submitted_at: str
    task_id: Optional[str] = None
    answer: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Submission':
        """Create a Submission instance from a dictionary."""
        return cls(
            id=data.get('id', 'N/A'),
            status=data.get('status', 'N/A'),
            submitted_at=data.get('submitted_at', 'N/A'),
            task_id=data.get('task_id'),
            answer=data.get('answer')
        )


@dataclass
class Task:
    """Task information."""
    id: str
    type: str
    status: str
    score: int
    time_remaining: str
    claimed_at: str
    submissions: List[Submission] = None
    last_attempt_at: Optional[str] = None
    solved_at: Optional[str] = None

    def __post_init__(self):
        if self.submissions is None:
            self.submissions = []

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create a Task instance from a dictionary."""
        submissions = []
        if 'submissions' in data:
            submissions = [Submission.from_dict(s) for s in data.get('submissions', [])]

        return cls(
            id=data.get('id', 'N/A'),
            type=data.get('type', 'N/A'),
            status=data.get('status', 'N/A'),
            score=data.get('score', 0),
            time_remaining=data.get('time_remaining', 'N/A'),
            claimed_at=data.get('claimed_at', 'N/A'),
            submissions=submissions,
            last_attempt_at=data.get('last_attempt_at'),
            solved_at=data.get('solved_at')
        )


@dataclass
class TaskList:
    """List of tasks."""
    tasks: List[Task]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskList':
        """Create a TaskList instance from a dictionary."""
        tasks = [Task.from_dict(t) for t in data.get('tasks', [])]
        return cls(tasks=tasks)


@dataclass
class TypeStats:
    """Statistics for a task type."""
    total: int
    pending: int
    ac: int
    wa: int
    remaining: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TypeStats':
        """Create a TypeStats instance from a dictionary."""
        return cls(
            total=data.get('total', 0),
            pending=data.get('pending', 0),
            ac=data.get('ac', 0),
            wa=data.get('wa', 0),
            remaining=data.get('remaining', 0)
        )


@dataclass
class Dashboard:
    """Dashboard with task statistics."""
    round_id: int
    stats: Dict[str, TypeStats]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Dashboard':
        """Create a Dashboard instance from a dictionary."""
        stats = {}
        for task_type, type_stats in data.get('stats', {}).items():
            stats[task_type] = TypeStats.from_dict(type_stats)

        return cls(
            round_id=data.get('round_id', 0),
            stats=stats
        )


@dataclass
class TeamScore:
    """Team score information."""
    rank: int
    name: str
    total_score: int
    scores: Dict[str, int]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TeamScore':
        """Create a TeamScore instance from a dictionary."""
        return cls(
            rank=data.get('rank', 0),
            name=data.get('name', 'N/A'),
            total_score=data.get('total_score', 0),
            scores=data.get('scores', {})
        )


@dataclass
class Leaderboard:
    """Leaderboard with team scores."""
    round_id: int
    teams: List[TeamScore]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Leaderboard':
        """Create a Leaderboard instance from a dictionary."""
        teams = [TeamScore.from_dict(t) for t in data.get('teams', [])]
        return cls(
            round_id=data.get('round_id', 0),
            teams=teams
        )


@dataclass
class RoundList:
    """List of rounds."""
    rounds: List[Round]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RoundList':
        """Create a RoundList instance from a dictionary."""
        rounds = [Round.from_dict(r) for r in data.get('rounds', [])]
        return cls(rounds=rounds)
