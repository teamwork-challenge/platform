from repo import (
    get_all_challenges, get_challenge_by_id, create_challenge,
    update_challenge, delete_all_challenges,
    get_task_by_id, create_task
)

class AdminService:
    def get_challenges(self):
        return get_all_challenges()

    def get_challenge(self, challenge_id: int):
        return get_challenge_by_id(challenge_id)

    def create_challenge(self, title: str):
        return create_challenge(title)

    def update_challenge(self, challenge_id: int, title: str):
        return update_challenge(challenge_id, title)

    def delete_all_challenges(self):
        return delete_all_challenges()

class PlayerService:
    def get_task(self, task_id: int):
        return get_task_by_id(task_id)

    def create_task(self, title: str, status: str = "PENDING"):
        return create_task(title, status)
