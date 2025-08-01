import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

import requests

from api_models.models import Task, RoundTaskType, RoundTaskTypeCreateRequest, Team, Challenge, Round, RoundList, Submission, TaskList, Dashboard, Leaderboard, RoundCreateRequest
from config_manager import ConfigManager


class ApiClient:
    """Client for interacting with the Teamwork Challenge API."""

    def __init__(self, config_manager: ConfigManager):
        """Initialize the API client.

        Args:
            config_manager: Instance of ConfigManager for handling configuration.
        """
        self.config_manager = config_manager

        # Store headers as instance variable to avoid rebuilding for every request
        self._headers = self._build_headers()

    def save_api_key(self, api_key: str) -> None:
        """Save API key to config file."""
        self.config_manager.save_api_key(api_key)
        # Update headers with new API key
        self._headers = self._build_headers()

    def remove_api_key(self) -> None:
        """Remove API key from config file."""
        self.config_manager.remove_api_key()
        # Update headers without API key
        self._headers = self._build_headers()
        
    def _build_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        headers = {"Content-Type": "application/json"}
        api_key = self.config_manager.get_api_key()
        if api_key:
            headers["X-API-Key"] = api_key
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
        base_url = self.config_manager.get_base_url()
        url = f"{base_url}{endpoint}"

        print(f"Making {method} request to {url} with data: {data}")
        response = requests.request(method, url, headers=self._headers, json=data)
        response.raise_for_status()
        return response.json()


    # Team-related methods
    def auth(self) -> str:
        """Get team information."""
        data = self._make_request("GET", "/auth")
        return data

    # Team-related methods
    def get_team_info(self) -> Team:
        """Get team information."""
        data = self._make_request("GET", "/team")
        return Team.model_validate(data)

    def rename_team(self, new_name: str) -> Team:
        """Rename team."""
        data = self._make_request("PUT", "/team", {"name": new_name})
        return Team.model_validate(data)

    # Challenge-related methods
    def get_challenges(self) -> list[Challenge]:
        """Get challenge information."""
        data = self._make_request("GET", "/challenges")
        return [Challenge.model_validate(d) for d in data]

    # Challenge-related methods
    def get_challenge_info(self, challenge_id: Optional[int]) -> Challenge:
        """Get challenge information."""
        data = self._make_request("GET", f"/challenges/{challenge_id if challenge_id is not None else 'current'}")
        return Challenge.model_validate(data)

    def update_challenge(self, challenge_id: int, update_data: Any) -> Challenge:
        """Update a challenge."""
        data = self._make_request("PUT", f"/challenges/{challenge_id}", update_data.model_dump(exclude_unset=True))
        return Challenge.model_validate(data)

    def delete_challenge(self, challenge_id: int) -> dict:
        """Mark a challenge as deleted by setting the deleted flag."""
        # For challenges, we use a flag instead of actual deletion
        data = self._make_request("PUT", f"/challenges/{challenge_id}", {"deleted": True})
        return data

    # Round-related methods
    def get_round_info(self, round_id: Optional[int] = None) -> Round:
        """Get round information."""
        endpoint = f"/rounds/{round_id}" if round_id else "/rounds/current"
        data = self._make_request("GET", endpoint)
        return Round.model_validate(data)

    def list_rounds(self, challenge_id: Optional[int] = None) -> RoundList:
        """List all rounds for a challenge.
        
        Args:
            challenge_id: ID of the challenge to list rounds for. If None, uses the current challenge.
            
        Returns:
            List of rounds for the challenge
        """
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
        """Publish a round."""
        return self.update_round(round_id, {"status": "active"})

    def update_round(self, round_id: int, update_data: dict) -> Round:
        """Update a round."""
        data = self._make_request("PUT", f"/rounds/{round_id}", update_data)
        return Round.model_validate(data)

    def create_round(self, round_data: RoundCreateRequest) -> Round:
        """Create a new round.
        
        Args:
            round_data: Data for creating the round
            
        Returns:
            The created round
        """
        data = self._make_request("POST", "/rounds", round_data.model_dump(mode="json"))
        return Round.model_validate(data)
        
    def delete_round(self, round_id: int) -> dict:
        """Delete a round."""
        return self._make_request("DELETE", f"/rounds/{round_id}")

    # Task Type-related methods
    def get_round_task_types(self, round_id: int) -> list[RoundTaskType]:
        """Get all task types for a round.
        
        Args:
            round_id: ID of the round to get task types for
            
        Returns:
            List of task types for the round
        """
        data = self._make_request("GET", f"/task-types?round_id={round_id}")
        return [RoundTaskType.model_validate(d) for d in data]
    
    def get_round_task_type(self, task_type_id: int) -> RoundTaskType:
        """Get a specific task type.
        
        Args:
            task_type_id: ID of the task type to get
            
        Returns:
            The task type
        """
        data = self._make_request("GET", f"/task-types/{task_type_id}")
        return RoundTaskType.model_validate(data)
    
    def create_round_task_type(self, task_type_data: RoundTaskTypeCreateRequest) -> RoundTaskType:
        """Create a new task type.
        
        Args:
            task_type_data: Data for creating the task type
            
        Returns:
            The created task type
        """
        data = self._make_request(
            "POST", 
            "/task-types", 
            task_type_data.model_dump(mode="json")
        )
        return RoundTaskType.model_validate(data)
    
    def update_round_task_type(self, task_type_id: int, 
                              task_type_data: RoundTaskTypeCreateRequest) -> RoundTaskType:
        """Update a task type.
        
        Args:
            task_type_id: ID of the task type to update
            task_type_data: Data for updating the task type
            
        Returns:
            The updated task type
        """
        data = self._make_request(
            "PUT", 
            f"/task-types/{task_type_id}", 
            task_type_data.model_dump(mode="json")
        )
        return RoundTaskType.model_validate(data)
    
    def delete_round_task_type(self, task_type_id: int) -> dict:
        """Delete a task type.
        
        Args:
            task_type_id: ID of the task type to delete
            
        Returns:
            Response data
        """
        return self._make_request("DELETE", f"/task-types/{task_type_id}")

    # Task-related methods
    def claim_task(self, task_type: Optional[str] = None) -> Task:
        """Claim a new task."""
        data = {}
        if task_type:
            data["type"] = task_type
        response = self._make_request("POST", "/tasks", data)
        return Task.model_validate(response)

    def get_task_info(self, task_id: str) -> Task:
        """Get task information."""
        data = self._make_request("GET", f"/tasks/{task_id}")
        return Task.model_validate(data)

    def get_task_input(self, task_id: str) -> Dict[str, Any]:
        """Get task input."""
        # This method returns raw task input, which is not a model class
        return self._make_request("GET", f"/tasks/{task_id}/input")

    def submit_task_answer(self, task_id: str, answer: str) -> Submission:
        """Submit an answer for a task."""
        data = self._make_request("POST", f"/tasks/{task_id}/submit", {"answer": answer})
        return Submission.model_validate(data)

    def get_submission_info(self, submit_id: str) -> Submission:
        """Get submission information."""
        data = self._make_request("GET", f"/submissions/{submit_id}")
        return Submission.model_validate(data)

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
        return TaskList.model_validate(data)

    # Board-related methods
    def get_dashboard(self, round_id: Optional[int] = None) -> Dashboard:
        """Get dashboard with task statistics."""
        endpoint = "/dashboard"
        if round_id:
            endpoint += f"?round_id={round_id}"
        data = self._make_request("GET", endpoint)
        return Dashboard.model_validate(data)

    def get_leaderboard(self, round_id: Optional[int] = None) -> Leaderboard:
        """Get leaderboard with team scores."""
        endpoint = "/leaderboard"
        if round_id:
            endpoint += f"?round_id={round_id}"
        data = self._make_request("GET", endpoint)
        return Leaderboard.model_validate(data)
