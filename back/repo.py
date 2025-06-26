class Repo:
    def __init__(self):
# demo mini database
        self.challenges = [
            {"id": 1, "title": "Teamwork Programming Challenge 2025"},
        ]

        self.tasks = [
            {"id": 1, "title": "First task", "status": "PENDING"},
            {"id": 2, "title": "Second task", "status": "AC"},
        ]

# API keys with associated roles, challenges
        self.api_keys = [
            {"key": "admin_key_123", "role": "admin", "challenge_id": None},
            {"key": "player_key_456", "role": "player", "challenge_id": 1},
        ]

# challenge methods
    def get_all_challenges(self):
        return self.challenges

    def get_challenge_by_id(self, challenge_id: int):
        for challenge in self.challenges:
            if challenge["id"] == challenge_id:
                return challenge
        return None

    def create_challenge(self, title: str):
        challenge_obj = {
            "id": len(self.challenges) + 1,
            "title": title
        }
        self.challenges.append(challenge_obj)
        return challenge_obj

    def delete_challenge(self, challenge_id: int):
        deleted = None
        for i, challenge in enumerate(self.challenges):
            if challenge["id"] == challenge_id:
                deleted = self.challenges.pop(i)
                break
        return deleted

    def update_challenge(self, challenge_id: int, title: str):
        for challenge in self.challenges:
            if challenge["id"] == challenge_id:
                challenge["title"] = title
                return challenge
        return None

# task methods
    def get_task_by_id(self, task_id: int):
        for task in self.tasks:
            if task["id"] == task_id:
                return task
        return None

    def create_task(self, title: str, status: str = "PENDING"):
        task_obj = {
            "id": len(self.tasks) + 1,
            "title": title,
            "status": status
        }
        self.tasks.append(task_obj)
        return task_obj

# API key methods
    def validate_api_key(self, api_key: str):
        for key_data in self.api_keys:
            if key_data["key"] == api_key:
                return key_data
        return None

    def get_role_from_api_key(self, api_key: str):
        key_data = self.validate_api_key(api_key)
        if key_data:
            return key_data["role"]
        return None

    def get_challenge_from_api_key(self, api_key: str):
        key_data = self.validate_api_key(api_key)
        if key_data:
            return key_data["challenge_id"]
        return None
