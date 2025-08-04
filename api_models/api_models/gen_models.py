from typing import List, Optional
from enum import Enum
from pydantic import BaseModel


# Models for /gen endpoint
class TaskProgress(BaseModel):
    """Task progress information"""
    task_index: int
    task_count: int
    elapsed_time: int
    total_time: int

class GenRequest(BaseModel):
    """Request model for the gen endpoint"""
    challenge: str
    team: str
    round: str
    progress: TaskProgress
    task_settings: str = ""

class GenResponse(BaseModel):
    """Response model for the gen endpoint"""
    statement_version: str
    statement: str = ""
    score: int
    input: str
    checker_hint: str = ""


# Models for /check endpoint
class CheckStatus(str, Enum):
    ACCEPTED = "AC"
    WRONG_ANSWER = "WA"


class CheckRequest(BaseModel):
    """Request model for the check endpoint"""
    input: str
    checker_hint: str = ""
    answer: str


class CheckResult(BaseModel):
    """Result model for a single task check"""
    task_id: Optional[str] = None
    status: CheckStatus  # "AC" or "WA"
    score: float = 1.0
    error: str = ""


class CheckResponse(List[CheckResult]):
    """Response model for the check endpoint"""
    pass