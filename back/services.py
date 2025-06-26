from repo import Repo

class AdminService:
    def __init__(self, repo: Repo):
        self.repo = repo

    def get_challenge(self, challenge_id: int):
        return self.repo.get_challenge_by_id(challenge_id)

    def get_all_challenges(self):
        return self.repo.get_all_challenges()

    def create_challenge(self, title: str):
        return self.repo.create_challenge(title)

    def update_challenge(self, challenge_id: int, title: str):
        return self.repo.update_challenge(challenge_id, title)

    def delete_challenge(self, challenge_id: int):
        return self.repo.delete_challenge(challenge_id)


class PlayerService:
    def __init__(self, repo: Repo):
        self.repo = repo

    def get_task(self, task_id: int):
        return self.repo.get_task_by_id(task_id)

    def create_task(self, challenge_id: int, title: str, status: str = "PENDING"):
        return self.repo.create_task(title, status)
