from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import requests
import json
import uuid

from api_models import Task as ApiTask, Team as ApiTeam
from api_models.gen_models import GenRequest, GenResponse, TaskProgress, CheckRequest, CheckResult, CheckStatus
from api_models.models import SubmissionExtended
from db_models import Team, Task, Round, Challenge, RoundTaskType


class PlayerService:
    def __init__(self, db: Session):
        self.db = db

    def get_task(self, task_id: int) -> Task:
        stmt = select(Task).where(Task.id == task_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_team(self, team_id: int) -> Team:
        stmt = select(Team).where(Team.id == team_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def create_task(self, challenge_id: int, team_id: int, task_type: str) -> Task:
        round = self.ensure_valid_round(challenge_id)
        round_task_type = self.ensure_valid_task_type(round.id, task_type)
        team = self.ensure_valid_team(team_id)
        self.ensure_task_limit(team_id, round.id, task_type, round_task_type)
        
        # Create the task with PENDING status
        task = Task(
            title=f"{task_type} Task",
            status="PENDING",
            challenge_id=challenge_id,
            team_id=team_id,
            type=task_type,
            round_id=round.id
        )

        self.db.add(task)

        existing_tasks = self.get_existing_tasks(team_id, round.id, task_type)
        
        # Create task progress
        current_time = datetime.now(timezone.utc)

        task_progress = TaskProgress(
            task_index=len(existing_tasks),
            task_count=round_task_type.max_tasks_per_team or 0,
            elapsed_time=int((current_time - round.start_time).total_seconds() / 60),
            total_time=int((round.end_time - round.start_time).total_seconds() / 60)
        )
        
        # Generate and update task content
        self.generate_task_content(task, team, round, round_task_type, task_progress)
        
        return task
        
    def ensure_valid_round(self, challenge_id: int) -> Round:
        stmt = select(Round).where(Round.challenge_id == challenge_id)
        round = self.db.execute(stmt).scalar_one_or_none()
        
        if round is None:
            raise ValueError("No active round found for this challenge")
            
        if round.status.lower() != "published":
            raise ValueError("Current round is not published")
            
        if not round.claim_by_type:
            raise ValueError("Claiming tasks by type is not enabled for this round")
            
        current_time = datetime.now(timezone.utc)
        if current_time < round.start_time:
            raise ValueError("Round has not started yet")
            
        if current_time > round.end_time:
            raise ValueError("Round has already ended")
            
        return round
        
    def ensure_valid_task_type(self, round_id: int, task_type: str) -> RoundTaskType:
        if task_type is None:
            raise ValueError("Task type must be specified")
            
        stmt = select(RoundTaskType).where(
            (RoundTaskType.round_id == round_id) & 
            (RoundTaskType.type == task_type)
        )
        round_task_type = self.db.execute(stmt).scalar_one_or_none()
        
        if round_task_type is None:
            raise ValueError(f"Task type '{task_type}' is not available in this round")
            
        return round_task_type
        
    def ensure_valid_team(self, team_id: int) -> Team:
        stmt = select(Team).where(Team.id == team_id)
        team = self.db.execute(stmt).scalar_one_or_none()
        
        if team is None:
            raise ValueError("Team not found")
            
        return team
        
    def get_existing_tasks(self, team_id: int, round_id: int, task_type: str) -> list:
        stmt = select(Task).where(
            (Task.team_id == team_id) & 
            (Task.round_id == round_id) & 
            (Task.type == task_type)
        )
        return self.db.execute(stmt).scalars().all()
        
    def ensure_task_limit(self, team_id: int, round_id: int, task_type: str, round_task_type: RoundTaskType) -> None:
        if round_task_type.max_tasks_per_team is not None:
            existing_tasks = self.get_existing_tasks(team_id, round_id, task_type)
            
            if len(existing_tasks) >= round_task_type.max_tasks_per_team:
                raise ValueError(f"Maximum number of tasks of type '{task_type}' already taken")

    def generate_task_content(self, task: Task, team: Team, round: Round, round_task_type: RoundTaskType, task_progress: TaskProgress) -> None:
        # Create request for task generator
        gen_request = GenRequest(
            challenge=str(task.challenge_id),
            team=team.name,
            round=str(round.id),
            progress=task_progress,
            task_settings=round_task_type.generator_settings or ""
        )
        
        try:
            # Make request to task generator
            response = requests.post(
                f"{round_task_type.generator_url}/gen",
                headers={"Content-Type": "application/json", "X-API-KEY": round_task_type.generator_secret or ""},
                data=json.dumps(gen_request.model_dump())
            )
            
            # Handle HTTP errors
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as http_err:
                if response.status_code == 401 or response.status_code == 403:
                    raise ValueError(f"Authentication error with task generator: {http_err}")
                elif response.status_code == 404:
                    raise ValueError(f"Task generator endpoint not found: {round_task_type.generator_url}/gen")
                elif response.status_code >= 500:
                    raise ValueError(f"Task generator server error: {http_err}")
                else:
                    raise ValueError(f"HTTP error when calling task generator: {http_err}")
            
            # Parse response
            try:
                gen_response = GenResponse.model_validate(response.json())
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON response from task generator")
            except Exception as validation_err:
                raise ValueError(f"Invalid response format from task generator: {validation_err}")
            
            # Update task with generated data
            task.content = json.dumps({
                "statement_version": gen_response.statement_version,
                "score": gen_response.score,
                "input": gen_response.input,
                "checker_hint": gen_response.checker_hint
            })
            task.statement = gen_response.statement
            task.status = "ACTIVE"
            
            self.db.commit()
            self.db.refresh(task)
            
        except requests.exceptions.ConnectionError:
            raise ValueError(f"Could not connect to task generator at {round_task_type.generator_url}")
        except requests.exceptions.Timeout:
            raise ValueError(f"Connection to task generator timed out")
        except requests.exceptions.RequestException as req_err:
            raise ValueError(f"Error making request to task generator: {req_err}")
        except ValueError:
            # Re-raise ValueError exceptions
            raise
        except Exception as e:
            # Catch any other unexpected errors
            raise ValueError(f"Unexpected error generating task: {str(e)}")
        
    def submit_task_answer(self, task_id: int, team_id: int, answer: str) -> SubmissionExtended:
        """Submited an answer for the task.
        
        Args:
            task_id: The ID of the task to submit an answer for
            team_id: The ID of the team submitting the answer
            answer: The answer to submit
            
        Returns:
            A SubmissionExtended object with the submission details
            
        Raises:
            ValueError: If the task is not found, doesn't belong to the team,
                       is not in PENDING status, or the round is not active
        """
        # Get the task
        stmt = select(Task).where(Task.id == task_id)
        task = self.db.execute(stmt).scalar_one_or_none()
        
        # Check if the task exists
        if task is None:
            raise ValueError("Task not found")
            
        # Check if the task belongs to the team
        if task.team_id != team_id:
            raise ValueError("Task does not belong to this team")
            
        # Check if the task is in PENDING status
        if task.status != "PENDING":
            raise ValueError("Task is not in PENDING status")
            
        # Get the round
        stmt = select(Round).where(Round.id == task.round_id)
        round = self.db.execute(stmt).scalar_one_or_none()
        
        # Check if the round is active
        current_time = datetime.now(timezone.utc)
        if current_time < round.start_time:
            raise ValueError("Round has not started yet")
            
        if current_time > round.end_time:
            raise ValueError("Round has already ended")
            
        # Get the task type
        stmt = select(RoundTaskType).where(
            (RoundTaskType.round_id == round.id) & 
            (RoundTaskType.type == task.type)
        )
        round_task_type = self.db.execute(stmt).scalar_one_or_none()
        
        if round_task_type is None:
            raise ValueError(f"Task type '{task.type}' is not available in this round")
            
        # Parse the task content to get the checker_hint
        task_content = json.loads(task.content)
        checker_hint = task_content.get("checker_hint")
        
        # Create a check request
        check_request = CheckRequest(
            answer=answer,
            checker_hint=checker_hint
        )
        
        try:
            # Make request to task generator to check the answer
            response = requests.post(
                f"{round_task_type.generator_url}/check",
                headers={"Content-Type": "application/json"},
                data=json.dumps(check_request.model_dump())
            )
            response.raise_for_status()
            
            check_result = CheckResult.model_validate(response.json())

            if check_result is None:
                raise RuntimeError("No check result returned from task generator")
                
            # Create a submission ID
            submission_id = str(uuid.uuid4())
            
            # Get the current time
            submitted_at = datetime.now(timezone.utc).isoformat()
            
            # Update the task status and team score based on the check result
            if check_result.status == CheckStatus.ACCEPTED:
                # Answer is correct
                task.status = "ACCEPTED"
                
                # Get the team
                stmt = select(Team).where(Team.id == team_id)
                team = self.db.execute(stmt).scalar_one_or_none()
                
                # Update the team score
                score = int(float(task_content.get("score", "0")) * check_result.score)
                team.total_score += score
                
                # Create a submission response
                submission = SubmissionExtended(
                    id=submission_id,
                    status="ACCEPTED",
                    submitted_at=submitted_at,
                    task_id=str(task_id),
                    answer=answer,
                    score=score
                )
            else:
                # Answer is wrong
                task.status = "WRONG_ANSWER"
                
                # Create a submission response
                submission = SubmissionExtended(
                    id=submission_id,
                    status="WRONG_ANSWER",
                    submitted_at=submitted_at,
                    task_id=str(task_id),
                    answer=answer,
                    explanation=check_result.error
                )
                
            # Commit the changes to the database
            self.db.commit()
            
            return submission
            
        except Exception as e:
            # If there's an error, just raise it
            raise ValueError(f"Error checking answer: {str(e)}")