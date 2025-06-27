import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

import requests

import api_models.api_models.models
from api_models import *


class ApiClient:
    """Client for interacting with the Teamwork Challenge API."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """Initialize the API client.

        Args:
            api_key: API key for authentication. If not provided, tries to load from config file.
            base_url: Base URL for the API. If not provided, uses the CHALLENGE_API_URL
                      environment variable or defaults to http://localhost:8000.
        """
        # TODO: Store base Url in the config, not in environment variable. Use the same config file as for the API key.
        self.base_url = base_url or os.environ.get("CHALLENGE_API_URL", "http://127.0.0.1:8088")
        self.api_key = api_key
        self.config_path = Path.home() / ".challenge" / "config.json"

        # If api_key is not provided, try to load it from config file
        if not self.api_key:
            self._load_api_key()

    # TODO: Move api key storage outside of this class to separate ConfigManager or similar. ApiClient should focus on API interactions.
    def _load_api_key(self) -> None:
        """Load API key from config file."""
        if not self.config_path.exists():
            return

        try:
            with open(self.config_path) as f:
                config = json.load(f)
                self.api_key = config.get("api_key")
        except (json.JSONDecodeError, FileNotFoundError):
            pass

    def save_api_key(self, api_key: str) -> None:
        """Save API key to config file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        config = {}
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    config = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass

        config["api_key"] = api_key
        self.api_key = api_key

        with open(self.config_path, "w") as f:
            json.dump(config, f)

    def remove_api_key(self):
        with open(self.config_path) as f:
            config = json.load(f)

        if "api_key" in config:
            del config["api_key"]
            self.api_key = None

            with open(self.config_path, "w") as f:
                json.dump(config, f)

    def _build_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    def _make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None):
        """Make a request to the API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., /tasks)
            data: Request data (for POST, PUT)

        Returns:
            Response data as a dictionary

        Raises:
            Exception: If the request fails
        """
        url = f"{self.base_url}{endpoint}"

        # print(f"Making {method} request to {url} with data: {data}")

        # TODO: Do not rebuild headers for every request, store them in an instance variable
        headers = self._build_headers()

        # TODO use requests.request(...) method to avoid `if` and code duplication
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()
        return response.json()


    # Team-related methods
    def get_team_info(self) -> Team:
        """Get team information."""
        data = self._make_request("GET", "/team")
        return Team.model_validate(data)

    def rename_team(self, new_name: str) -> Team:
        """Rename team."""
        data = self._make_request("PUT", "/team", {"name": new_name})
        return Team.from_dict(data)

    # Challenge-related methods
    def get_challenges(self) -> list[api_models.api_models.models.Challenge]:
        """Get challenge information."""
        data = self._make_request("GET", "/challenges")
        return [Challenge.from_dict(d) for d in data]

    # Challenge-related methods
    def get_challenge_info(self) -> Challenge:
        """Get challenge information."""
        data = self._make_request("GET", "/challenge")
        return Challenge.from_dict(data)

    # Round-related methods
    def get_round_info(self, round_id: Optional[int] = None) -> Round:
        """Get round information."""
        endpoint = f"/rounds/{round_id}" if round_id else "/rounds/current"
        data = self._make_request("GET", endpoint)
        return Round.from_dict(data)

    def list_rounds(self) -> RoundList:
        """List all rounds."""
        data = self._make_request("GET", "/rounds")
        return RoundList.from_dict(data)

    # Task-related methods
    def claim_task(self, task_type: Optional[str] = None) -> Task:
        """Claim a new task."""
        data = {}
        if task_type:
            data["type"] = task_type
        response = self._make_request("POST", "/tasks/claim", data)
        return Task.from_dict(response)

    def get_task_info(self, task_id: str) -> Task:
        """Get task information."""
        data = self._make_request("GET", f"/tasks/{task_id}")
        return Task.from_dict(data)

    def get_task_input(self, task_id: str) -> Dict[str, Any]:
        """Get task input."""
        # This method returns raw task input, which is not a model class
        return self._make_request("GET", f"/tasks/{task_id}/input")

    def submit_task_answer(self, task_id: str, answer: str) -> Submission:
        """Submit an answer for a task."""
        data = self._make_request("POST", f"/tasks/{task_id}/submit", {"answer": answer})
        return Submission.from_dict(data)

    def get_submission_info(self, submit_id: str) -> Submission:
        """Get submission information."""
        data = self._make_request("GET", f"/submissions/{submit_id}")
        return Submission.from_dict(data)

    def list_tasks(self, status: Optional[str] = None, task_type: Optional[str] = None, 
                  round_id: Optional[int] = None, since: Optional[str] = None) -> TaskList:
        """List tasks."""
        params = {}
        if status:
            params["status"] = status
        if task_type:
            params["type"] = task_type
        if round_id:
            params["round_id"] = round_id
        if since:
            params["since"] = since

        # In a real implementation, we would add these params to the request
        data = self._make_request("GET", "/tasks")
        return TaskList.from_dict(data)

    # Board-related methods
    def get_dashboard(self, round_id: Optional[int] = None) -> Dashboard:
        """Get dashboard with task statistics."""
        endpoint = "/dashboard"
        if round_id:
            endpoint += f"?round_id={round_id}"
        data = self._make_request("GET", endpoint)
        return Dashboard.from_dict(data)

    def get_leaderboard(self, round_id: Optional[int] = None) -> Leaderboard:
        """Get leaderboard with team scores."""
        endpoint = "/leaderboard"
        if round_id:
            endpoint += f"?round_id={round_id}"
        data = self._make_request("GET", endpoint)
        return Leaderboard.from_dict(data)
