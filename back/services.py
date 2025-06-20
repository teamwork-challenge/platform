from fastapi import HTTPException
from repo import (
    get_all_challenges, get_challenge_by_id, create_challenge,
    update_challenge, delete_all_challenges,
    get_task_by_id, create_task
)

class AdminService:
    def get_challenges(self):
        return get_all_challenges()

    def get_challenge(self, challenge_id: int):
        challenge = get_challenge_by_id(challenge_id)
        if challenge is None:
            raise HTTPException(status_code=404, detail="Challenge not found")
        return challenge

    def create_challenge(self, title: str):
        return create_challenge(title)

    def update_challenge(self, challenge_id: int, title: str):
        updated = update_challenge(challenge_id, title)
        if updated is None:
            raise HTTPException(status_code=404, detail="Challenge not found")
        return {"message": "Challenge updated", "challenge": updated}

    def delete_all_challenges(self):
        deleted = delete_all_challenges()
        if deleted is None:
            raise HTTPException(status_code=404, detail="No challenges to delete")
        return {"message": "All challenges deleted", "deleted": deleted}

class PlayerService:
    def get_task(self, task_id: int):
        task = get_task_by_id(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return task

    def create_task(self, title: str, status: str = "PENDING"):
        return create_task(title, status)
