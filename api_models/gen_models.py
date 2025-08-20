from typing import List, Optional
from enum import StrEnum
from pydantic import BaseModel


# Models for /gen endpoint
class TaskProgress(BaseModel):
    """Task progress information"""
    task_index: int
    task_count: int
    elapsed_time: int
    total_time: int


class GenRequest(BaseModel):
    challenge_id: str
    team_id: str
    round_id: str
    task_id: Optional[str] = None
    progress: TaskProgress
    task_settings: str = ""


class GenResponse(BaseModel):
    statement_version: str
    statement: str = ""
    input: str
    checker_hint: str = ""


class CheckStatus(StrEnum):
    ACCEPTED = "ac"
    WRONG_ANSWER = "wa"


class CheckRequest(BaseModel):
    input: str
    checker_hint: str = ""
    answer: str
    task_id: Optional[str] = None


class CollaborativeScore(BaseModel):
    """Model for collaborative task score updates"""
    task_id: str
    score: float = 1.0


class CheckResult(BaseModel):
    """Result model for a single task check"""
    task_id: Optional[str] = None
    status: CheckStatus  # "AC" or "WA"
    score: float = 1.0
    error: str = ""
    collaborative_scores: Optional[List[CollaborativeScore]] = None


class CheckResponse(List[CheckResult]):
    pass