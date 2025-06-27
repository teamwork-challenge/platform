from pydantic import BaseModel
from enum import Enum
from typing import Optional

class UserRole(str, Enum):
    ADMIN = "admin"
    PLAYER = "player"

class AuthData(BaseModel):
    key: str
    role: UserRole
    team_id: Optional[int] = None
    challenge_id: Optional[int] = None


class ChallengeOut(BaseModel):
    id: int
    title: str
    description: str
    current_round_id: Optional[int] = None

    class Config:
        from_attributes = True

class ChallengeNew(BaseModel):
    title: str
    description: str

class Task(BaseModel):
    title: str
    status: str = "PENDING"
