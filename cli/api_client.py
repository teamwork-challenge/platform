import logging
from typing import Optional, Dict, Any

import requests

from api_models import Task, RoundTaskType, RoundTaskTypeCreateRequest, Team, Challenge, Round, RoundList, Submission, \
    TaskList, Dashboard, Leaderboard, RoundCreateRequest, RoundUpdateRequest, RoundStatus, DeleteResponse
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

    def _make_request(self, method: str, endpoint: str, data: Dict[str, Any] | None = None) -> Any:
        """Make a request to the API."""
        base_url = self.config_manager.get_base_url()
        url = f"{base_url}{endpoint}"

        logging.info("Make request: %s %s. Data: %s", method, url, data)
        response = requests.request(method, url, headers=self._headers, json=data)
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
        data = self._make_request("PUT", "/team", {"name": new_name})
        return Team.model_validate(data)

    # Challenge-related methods
    def get_challenges(self) -> list[Challenge]:
        data = self._make_request("GET", "/challenges")
        return [Challenge.model_validate(d) for d in data]

    # Challenge-related methods
    def get_challenge_info(self, challenge_id: Optional[int]) -> Challenge:
        data = self._make_request("GET", f"/challenges/{challenge_id if challenge_id is not None else 'current'}")
        return Challenge.model_validate(data)

    def update_challenge(self, challenge_id: int, update_data: Any) -> Challenge:
        data = self._make_request("PUT", f"/challenges/{challenge_id}", update_data.model_dump(exclude_unset=True))
        return Challenge.model_validate(data)

    def delete_challenge(self, challenge_id: int) -> Challenge:
        """Mark a challenge as deleted by setting the deleted flag."""
        # For challenges, we use a flag instead of actual deletion
        data = self._make_request("PUT", f"/challenges/{challenge_id}", {"deleted": True})
        return Challenge.model_validate(data)

    # Round-related methods
    def get_round_info(self, round_id: Optional[int] = None) -> Round:
        endpoint = f"/rounds/{round_id}" if round_id else "/rounds/current"
        data = self._make_request("GET", endpoint)
        return Round.model_validate(data)

    def list_rounds(self, challenge_id: Optional[int] = None) -> RoundList:
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

    def publish_round(self, round_id: int) -> Round:
        # First, get the round info to get the challenge_id and other required fields
        round_info = self.get_round_info(round_id)
        # Create an update request with all required fields
        update_data = RoundUpdateRequest(
            status=RoundStatus.PUBLISHED,
            index=round_info.index,
            start_time=round_info.start_time,
            end_time=round_info.end_time,
            claim_by_type=round_info.claim_by_type,
            allow_resubmit=round_info.allow_resubmit,
            score_decay=round_info.score_decay
        )
        return self.update_round(round_id, update_data)

    def update_round(self, round_id: int, update_data: RoundUpdateRequest) -> Round:
        # First, get the round info to get the challenge_id and other required fields
        round_info = self.get_round_info(round_id)
        
        # Create a dictionary with all the required fields from the existing round
        # Convert datetime objects to ISO format strings
        data_dict = {
            "challenge_id": round_info.challenge_id,
            "index": round_info.index,
            "start_time": (
                round_info.start_time.isoformat()
                if hasattr(round_info.start_time, "isoformat")
                else round_info.start_time
            ),
            "end_time": (
                round_info.end_time.isoformat()
                if hasattr(round_info.end_time, "isoformat")
                else round_info.end_time
            ),
            "claim_by_type": round_info.claim_by_type,
            "allow_resubmit": round_info.allow_resubmit,
            "score_decay": round_info.score_decay,
            "status": round_info.status
        }
        
        # Update with the new values
        update_dict = update_data.model_dump(mode="json", exclude_none=True)
        data_dict.update(update_dict)
        
        # Make the request with all required fields
        data = self._make_request("PUT", f"/rounds/{round_id}", data_dict)
        return Round.model_validate(data)

    def create_round(self, round_data: RoundCreateRequest) -> Round:
        data = self._make_request("POST", "/rounds", round_data.model_dump(mode="json"))
        return Round.model_validate(data)
        
    def delete_round(self, round_id: int) -> DeleteResponse:
        return DeleteResponse.model_validate(self._make_request("DELETE", f"/rounds/{round_id}"))

    # Task Type-related methods
    def get_round_task_types(self, round_id: int) -> list[RoundTaskType]:
        data = self._make_request("GET", f"/task-types?round_id={round_id}")
        return [RoundTaskType.model_validate(d) for d in data]
    
    def get_round_task_type(self, task_type_id: int) -> RoundTaskType:
        """Get a specific task type."""
        data = self._make_request("GET", f"/task-types/{task_type_id}")
        return RoundTaskType.model_validate(data)
    
    def create_round_task_type(self, task_type_data: RoundTaskTypeCreateRequest) -> RoundTaskType:
        data = self._make_request(
            "POST", 
            "/task-types",
            task_type_data.model_dump(mode="json")
        )
        return RoundTaskType.model_validate(data)
    
    def update_round_task_type(self, task_type_id: int,
                               task_type_data: RoundTaskTypeCreateRequest) -> RoundTaskType:
        data = self._make_request(
            "PUT", 
            f"/task-types/{task_type_id}",
            task_type_data.model_dump(mode="json")
        )
        return RoundTaskType.model_validate(data)
    
    def delete_round_task_type(self, task_type_id: int) -> RoundTaskType:
        return RoundTaskType.model_validate(self._make_request("DELETE", f"/task-types/{task_type_id}"))

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
        data = self._make_request("POST", f"/tasks/{task_id}/submission", {"answer": answer})
        return Submission.model_validate(data)

    def get_submission_info(self, submit_id: str) -> Submission:
        data = self._make_request("GET", f"/submissions/{submit_id}")
        return Submission.model_validate(data)

    def list_tasks(self,
                    status: Optional[str] = None,
                    task_type: Optional[str] = None,
                    round_id: Optional[int] = None,
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
    def get_dashboard(self, round_id: Optional[int] = None) -> Dashboard:
        """Get a dashboard with task statistics."""
        endpoint = "/dashboard"
        if round_id:
            endpoint += f"?round_id={round_id}"
        data = self._make_request("GET", endpoint)
        return Dashboard.model_validate(data)

    def get_leaderboard(self, round_id: Optional[int] = None) -> Leaderboard:
        """Get a leaderboard with team scores."""
        endpoint = "/leaderboard"
        if round_id:
            endpoint += f"?round_id={round_id}"
        data = self._make_request("GET", endpoint)
        return Leaderboard.model_validate(data)
