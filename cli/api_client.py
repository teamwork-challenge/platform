import json
import logging
from typing import Optional, Dict, Any

import requests

from api_models import Task, RoundTaskType, Team, Challenge, Round, RoundList, Submission, \
    TaskList, Dashboard, Leaderboard, DeleteResponse
from cli.config_manager import ConfigManager


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

    def _resolve_task_type_location(self, task_type_id: str) -> tuple[str, str]:
        """Find (round_id, challenge_id) for a given task_type_id by scanning challenges and rounds.
        This is used for admin endpoints that require explicit IDs.
        """
        challenges = self.get_challenges()
        for ch in challenges:
            # List rounds for this challenge
            rounds = self.list_rounds(ch.id).rounds
            for rd in rounds:
                # List task types for this round under this challenge
                try:
                    types = self._make_request("GET", f"/task-types?round_id={rd.id}&challenge_id={ch.id}")
                except requests.HTTPError:
                    continue
                for tt in types:
                    if str(tt.get("id", "")) == task_type_id:
                        return rd.id, ch.id
        raise requests.HTTPError(f"Task type not found: {task_type_id}")

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

    # Challenge-related methods
    def get_challenges(self) -> list[Challenge]:
        data = self._make_request("GET", "/challenges")
        return [Challenge.model_validate(d) for d in data]

    # Challenge-related methods
    def get_challenge_info(self, challenge_id: Optional[str]) -> Challenge:
        data = self._make_request("GET", f"/challenges/{challenge_id if challenge_id is not None else 'current'}")
        return Challenge.model_validate(data)

    def update_challenge(self, challenge: Challenge) -> Challenge:
        data = self._make_request("PUT", f"/challenges/{challenge.id}", challenge.model_dump_json(exclude_unset=True))
        return Challenge.model_validate(data)

    def delete_challenge(self, challenge_id: str) -> Challenge:
        """Mark a challenge as deleted by setting the deleted flag."""
        # For challenges, we use a flag instead of actual deletion
        data = self._make_request("PUT", f"/challenges/{challenge_id}", json.dumps({"deleted": True}))
        return Challenge.model_validate(data)

    # Round-related methods
    def get_round_info(self, round_id: Optional[str] = None) -> Round:
        if not round_id:
            data = self._make_request("GET", "/rounds/current")
            return Round.model_validate(data)
        data = self._make_request("GET", f"/rounds/{round_id}")
        return Round.model_validate(data)


    def list_rounds(self, challenge_id: Optional[str] = None) -> RoundList:
        """List all rounds for a challenge."""
        if challenge_id is None:
            # Get the current challenge ID
            challenge = self.get_challenge_info(None)
            challenge_id = challenge.id
            
        endpoint = f"/rounds?challenge_id={challenge_id}"
        data = self._make_request("GET", endpoint)
        # Wrap the list of rounds in a dictionary with a "rounds" key
        # to match the RoundList model's expected structure
        return RoundList.model_validate({"rounds": data})

    def update_round(self, new_round: Round) -> Round:
        round_json = new_round.model_dump_json(exclude_none=True)
        # Make the request with all required fields and required challenge_id param
        endpoint = f"/rounds/{new_round.id}"
        data = self._make_request("PUT", endpoint, round_json)
        return Round.model_validate(data)

    def delete_round(self, challenge_id: str, round_id: str) -> DeleteResponse:
        endpoint = f"/rounds/{round_id}?challenge_id={challenge_id}"
        return DeleteResponse.model_validate(self._make_request("DELETE", endpoint))

    # Task Type-related methods
    def get_round_task_types(self, round_id: str) -> list[RoundTaskType]:
        round_info = self.get_round_info(round_id)
        data = self._make_request("GET", f"/task-types?round_id={round_id}&challenge_id={round_info.challenge_id}")
        return [RoundTaskType.model_validate(d) for d in data]
    
    # Task-related methods
    def claim_task(self, task_type: Optional[str] = None) -> Task:
        query = "" if task_type is None else f"?task_type={task_type}"
        response = self._make_request("POST", f"/tasks{query}")
        return Task.model_validate(response)

    def get_task_info(self, task_id: str) -> Task:
        data = self._make_request("GET", f"/tasks/{task_id}")
        return Task.model_validate(data)

    def get_task_input(self, task_id: str) -> str:
        """Get task input. Fetches a task and returns its input field."""
        data = self._make_request("GET", f"/tasks/{task_id}")
        # The response is a Task-like dict; extract 'input' if present
        return str(data.get("input", ""))

    def submit_task_answer(self, task_id: str, answer: str) -> Submission:
        data = self._make_request("POST", f"/tasks/{task_id}/submission", json.dumps({"answer": answer}))
        return Submission.model_validate(data)

    def get_submission_info(self, submit_id: str) -> Submission:
        data = self._make_request("GET", f"/submissions/{submit_id}")
        return Submission.model_validate(data)

    def list_tasks(self,
                    status: Optional[str] = None,
                    task_type: Optional[str] = None,
                    round_id: Optional[str] = None,
                    since: Optional[str] = None) -> TaskList:
        """List tasks with optional filters."""
        params = []
        if status:
            params.append(f"status={status}")
        if task_type:
            params.append(f"task_type={task_type}")
        if round_id is not None:
            params.append(f"round_id={round_id}")
        if since:
            params.append(f"since={since}")
        query = ("?" + "&".join(params)) if params else ""
        data = self._make_request("GET", f"/tasks/{query}")
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
