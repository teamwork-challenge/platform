from fastapi import HTTPException

# demo mini database
challenges = [
    {"id": 1, "title": "Teamwork Programming Challenge 2025"},
]

tasks = [
    {"id": 1, "title": "First task", "status": "PENDING"},
    {"id": 2, "title": "Second task", "status": "AC"},
]

# challenge functions
def get_all_challenges():
    return challenges

def get_challenge_by_id(challenge_id: int):
    for challenge in challenges:
        if challenge["id"] == challenge_id:
            return challenge
    return None

def create_challenge(title: str):
    challenge_obj = {
        "id": len(challenges) + 1,
        "title": title
    }
    challenges.append(challenge_obj)
    return challenge_obj

def delete_all_challenges():
    if not challenges:
        return None
    deleted = challenges.copy()
    challenges.clear()
    return deleted

def update_challenge(challenge_id: int, title: str):
    for challenge in challenges:
        if challenge["id"] == challenge_id:
            challenge["title"] = title
            return challenge
    return None

# task functions
def get_task_by_id(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task
    return None

def create_task(title: str, status: str = "PENDING"):
    task_obj = {
        "id": len(tasks) + 1,
        "title": title,
        "status": status
    }
    tasks.append(task_obj)
    return task_obj
