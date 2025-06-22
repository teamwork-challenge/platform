from pydantic import BaseModel
from enum import Enum
from typing import Optional

# Enum representing the role of a user.
# Used to distinguish between admin and player permissions.
class UserRole(str, Enum):
    ADMIN = "admin"
    PLAYER = "player"

# BaseModel performs automatic data validation
# and helps convert them to JSON format (serialization)

# class for describing API key with associated role and challenge
class ApiKey(BaseModel):
    key: str
    role: UserRole
    challenge_id: Optional[int] = None

# class for describing how a challenge should look
class Challenge(BaseModel):
    title: str
# class for describing how a task should look
class Task(BaseModel):
    title: str
    status: str = "PENDING"
