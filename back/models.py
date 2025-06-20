from pydantic import BaseModel

# BaseModel performs automatic data validation
# and helps convert them to JSON format (serialization)

# class for describing how a challenge should look
class Challenge(BaseModel):
    title: str
# class for describing how a task should look
class Task(BaseModel):
    title: str
    status: str = "PENDING"
