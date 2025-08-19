import json
import logging
from typing import Optional, Dict, Any, List

import requests

from api_models import Task, Team, Challenge, Round, Submission, \
    TaskList, Dashboard, Leaderboard, DeleteResponse, SubmitAnswerRequest, TeamsImportRequest, TeamsImportResponse
from cli.config_manager import ConfigManager


def _build_round_path(challenge_id: Optional[str], round_id: Optional[str], rest_path: str) -> str:
    ch = challenge_id or "current"
    rd = round_id or "current"
    return f"/challenges/{ch}/rounds/{rd}{rest_path}"


class ApiClient:
    """Client for interacting with the Teamwork Challenge API."""

    def __init__(self, config_manager: ConfigManager):
        """Initialize the API client."""
        self.config_manager = config_manager

        # Store headers as instance variable to avoid rebuilding for every request
        self._headers = self._build_headers()

    def save_api_key(self, api_key: str) -> None:
        """Save API key to config file."""
        self.config_manager.save_api_key(api_key)
        # Update headers with a new API key
        self._headers = self._build_headers()

    def remove_api_key(self) -> None:
        """Remove an API key from the config file."""
        self.config_manager.remove_api_key()
        # Update headers without an API key
        self._headers = self._build_headers()
        
    def _build_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        headers = {"Content-Type": "application/json"}
        api_key = self.config_manager.get_api_key()
        if api_key:
            headers["X-API-Key"] = api_key
        return headers

    def logged_in(self) -> bool:
        """Check if the user is logged in by verifying if an API key is set."""
        return self.config_manager.get_api_key() is not None

    def _make_request(self, method: str, endpoint: str, data: str | None = None) -> Any:
        """Make a request to the API."""
        base_url = self.config_manager.get_base_url()
        url = f"{base_url}{endpoint}"

        logging.info("Make request: %s %s. Data: %s", method, url, data)
        response = requests.request(method, url, headers=self._headers, data=data)
        res = response.text
        logging.info("Received response: %s %s", response.status_code, res)
        if 400 <= response.status_code <= 500:
            raise requests.HTTPError(f"{res} (status code: {response.status_code})")
        response.raise_for_status()
        return response.json()

    # Team-related methods
    def auth(self) -> str:
        data = self._make_request("GET", "/auth")
        return str(data)

    # Team-related methods
    def get_team_info(self) -> Team:
        data: Any = self._make_request("GET", "/team")
        return Team.model_validate(data)

    def rename_team(self, new_name: str) -> Team:
        data = self._make_request("PUT", "/team", json.dumps({"name": new_name}))
        return Team.model_validate(data)

    def create_teams(self, request: TeamsImportRequest) -> TeamsImportResponse:
        data = self._make_request("POST", "/teams", request.model_dump_json())
        return TeamsImportResponse.model_validate(data)

    def get_teams(self, challenge_id: Optional[str] = None) -> list[Team]:
        """List teams for the specified or current challenge."""
        ch = challenge_id or "current"
        data = self._make_request("GET", f"/challenges/{ch}/teams")
        return [Team.model_validate(d) for d in data]

    # Challenge-related methods
    def get_challenges(self) -> list[Challenge]:
        data = self._make_request("GET", "/challenges")
        return [Challenge.model_validate(d) for d in data]

    # Challenge-related methods
    def get_challenge_info(self, challenge_id: Optional[str] = None) -> Challenge:
        data = self._make_request("GET", f"/challenges/{challenge_id if challenge_id is not None else 'current'}")
        return Challenge.model_validate(data)

    def put_challenge(self, challenge: Challenge) -> Challenge:
        data = self._make_request("PUT", f"/challenges/{challenge.id}", challenge.model_dump_json(exclude_unset=True))
        return Challenge.model_validate(data)

    # Round-related methods
    def get_round(self, challenge_id: str | None, round_id: str | None) -> Round:
        data = self._make_request("GET", _build_round_path(challenge_id, round_id, ""))
        return Round.model_validate(data)

    def list_rounds(self, challenge_id: Optional[str] = None) -> List[Round]:
        """List all rounds for a challenge."""
        challenge_id = challenge_id or "current"
        endpoint = f"/challenges/{challenge_id}/rounds"
        data = self._make_request("GET", endpoint)
        return [Round.model_validate(d) for d in data]

    def update_round(self, new_round: Round) -> Round:
        round_json = new_round.model_dump_json(exclude_none=True)
        data = self._make_request("PUT", _build_round_path(new_round.challenge_id, new_round.id, ""), round_json)
        return Round.model_validate(data)

    def delete_round(self, challenge_id: str, round_id: str) -> DeleteResponse:
        response = self._make_request("DELETE", _build_round_path(challenge_id, round_id, ""))
        return DeleteResponse.model_validate(response)

    # Task-related methods
    def claim_task(self, task_type: Optional[str] = None, challenge_id: Optional[str] = None, round_id: Optional[str] = None) -> Task:
        query = "" if task_type is None else f"?task_type={task_type}"
        response = self._make_request("POST", _build_round_path(challenge_id, round_id, f"/tasks{query}"))
        return Task.model_validate(response)

    def get_task_info(self, task_id: str, challenge_id: Optional[str] = None, round_id: Optional[str] = None) -> Task:
        data = self._make_request("GET", _build_round_path(challenge_id, round_id, f"/tasks/{task_id}"))
        return Task.model_validate(data)

    def get_task_input(self, task_id: str, challenge_id: Optional[str] = None, round_id: Optional[str] = None) -> str:
        """Get task input. Fetches a task and returns its input field."""
        data = self._make_request("GET", _build_round_path(challenge_id, round_id, f"/tasks/{task_id}"))
        # The response is a Task-like dict; extract 'input' if present
        return str(data.get("input", ""))

    def submit_task_answer(self, submission: SubmitAnswerRequest, challenge_id: Optional[str] = None, round_id: Optional[str] = None) -> Submission:
        data = self._make_request("POST", _build_round_path(challenge_id, round_id, f"/submissions"), submission.model_dump_json())
        return Submission.model_validate(data)

    def get_submission_info(self, submission_id: str, challenge_id: Optional[str] = None, round_id: Optional[str] = None) -> Submission:
        data = self._make_request("GET", _build_round_path(challenge_id, round_id, f"/submissions/{submission_id}"))
        return Submission.model_validate(data)

    def list_tasks(self,
                    status: Optional[str] = None,
                    task_type: Optional[str] = None,
                    round_id: Optional[str] = None,
                    since: Optional[str] = None,
                    challenge_id: Optional[str] = None) -> TaskList:
        """List tasks with optional filters within a round."""
        params: list[str] = []
        if status:
            params.append(f"status={status}")
        if task_type:
            params.append(f"task_type={task_type}")
        if since:
            params.append(f"since={since}")
        query = ("?" + "&".join(params)) if params else ""
        data = self._make_request("GET", _build_round_path(challenge_id, round_id, "/tasks" + query))
        return TaskList.model_validate({"tasks": data})

    # Board-related methods
    def get_dashboard(self, round_id: Optional[str] = None) -> Dashboard:
        """Get a dashboard with task statistics."""
        endpoint = "/dashboard"
        if round_id:
            endpoint += f"?round_id={round_id}"
        data = self._make_request("GET", endpoint)
        return Dashboard.model_validate(data)

    def get_leaderboard(self, round_id: Optional[str] = None) -> Leaderboard:
        """Get a leaderboard with team scores."""
        endpoint = "/leaderboard"
        if round_id:
            endpoint += f"?round_id={round_id}"
        data = self._make_request("GET", endpoint)
        return Leaderboard.model_validate(data)
