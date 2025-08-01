from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import requests
import json
import uuid
from enum import Enum, auto

from api_models import Task as ApiTask, Team as ApiTeam
from api_models.gen_models import GenRequest, GenResponse, TaskProgress, CheckRequest, CheckResult, CheckStatus
from api_models.models import Submission
from db_models import Team, Task, Round, Challenge, RoundTaskType


class TaskGenClient:
    """Client for interacting with task generator service."""
    
    def generate_task(self, generator_url: str, generator_secret: str, gen_request: GenRequest) -> GenResponse:
        """Generate task content by calling the task generator and return the generator response."""
        try:
            # Make request to task generator
            response = requests.post(
                f"{generator_url}/gen",
                headers={"Content-Type": "application/json", "X-API-KEY": generator_secret or ""},
                data=json.dumps(gen_request.model_dump())
            )

            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as http_err:
                if response.status_code == 401 or response.status_code == 403:
                    raise RuntimeError(f"Authentication error with task generator: {http_err}")
                elif response.status_code == 404:
                    raise RuntimeError(f"Task generator endpoint not found: {generator_url}/gen")
                elif response.status_code >= 500:
                    raise RuntimeError(f"Task generator server error: {http_err}")
                else:
                    raise RuntimeError(f"HTTP error when calling task generator: {http_err}")

            # Parse response
            try:
                gen_response = GenResponse.model_validate(response.json())
            except json.JSONDecodeError:
                raise RuntimeError("Invalid JSON response from task generator")
            except Exception as validation_err:
                raise RuntimeError(f"Invalid response format from task generator: {validation_err}")

            return gen_response

        except requests.exceptions.ConnectionError:
            raise RuntimeError(f"Could not connect to task generator at {generator_url}")
        except requests.exceptions.Timeout:
            raise RuntimeError(f"Connection to task generator timed out")
        except requests.exceptions.RequestException as req_err:
            raise RuntimeError(f"Error making request to task generator: {req_err}")
        except ValueError:
            # Re-raise ValueError exceptions for validation errors
            raise
        except Exception as e:
            # Catch any other unexpected errors
            raise RuntimeError(f"Unexpected error generating task: {str(e)}")
            
    def check_answer(self, generator_url: str, answer: str, checker_hint: str) -> CheckResult:
        """Check the answer with the task generator."""
        check_request = CheckRequest(
            answer=answer,
            checker_hint=checker_hint
        )

        try:
            response = requests.post(
                f"{generator_url}/check",
                headers={"Content-Type": "application/json"},
                data=json.dumps(check_request.model_dump())
            )
            response.raise_for_status()

            check_result = CheckResult.model_validate(response.json())

            if check_result is None:
                raise RuntimeError("No check result returned from task generator")

            return check_result

        except Exception as e:
            raise RuntimeError(f"Error checking answer: {str(e)}")


class TaskStatus(Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    ACCEPTED = "ACCEPTED"
    WRONG_ANSWER = "WRONG_ANSWER"


class PlayerService:
    def __init__(self, db: Session):
        self.db = db
        self.task_gen_client = TaskGenClient()

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
            status=TaskStatus.PENDING.value,
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

        # Generate task content
        gen_response = self.generate_task_content(task, team, round, round_task_type, task_progress)

        # Update task with generated data
        task.statement_version = gen_response.statement_version
        task.score = gen_response.score
        task.input = gen_response.input
        task.checker_hint = gen_response.checker_hint
        task.statement = gen_response.statement
        task.status = TaskStatus.ACTIVE.value

        self.db.commit()
        self.db.refresh(task)

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

    def get_existing_tasks(self, team_id: int, round_id: int, task_type: str) -> list[Task]:
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

    def generate_task_content(self, task: Task, team: Team, round: Round, round_task_type: RoundTaskType,
                              task_progress: TaskProgress) -> GenResponse:
        """Generate task content by calling the task generator and return the generator response.
        The caller is responsible for updating the task with the response data."""

        gen_request = GenRequest(
            challenge=str(task.challenge_id),
            team=team.name,
            round=str(round.id),
            progress=task_progress,
            task_settings=round_task_type.generator_settings or ""
        )

        return self.task_gen_client.generate_task(
            round_task_type.generator_url,
            round_task_type.generator_secret,
            gen_request
        )

    def check_answer(self, answer: str, checker_hint: str, generator_url: str) -> CheckResult:
        """Check the answer with the task generator."""
        return self.task_gen_client.check_answer(generator_url, answer, checker_hint)

    def create_submission(self, task_id: int, team_id: int, answer: str,
                           check_result: CheckResult, task: Task) -> Submission:
        """Create a submission based on the check result."""
        submission_id = str(uuid.uuid4())
        submitted_at = datetime.now(timezone.utc).isoformat()

        if check_result.status == CheckStatus.ACCEPTED:
            task.status = TaskStatus.ACCEPTED.value

            stmt = select(Team).where(Team.id == team_id)
            team = self.db.execute(stmt).scalar_one_or_none()

            score = int(float(task.score or 0) * check_result.score)
            team.total_score += score

            submission = Submission(
                id=submission_id,
                status=TaskStatus.ACCEPTED.value,
                submitted_at=submitted_at,
                task_id=str(task_id),
                answer=answer,
                score=score
            )
        else:
            task.status = TaskStatus.WRONG_ANSWER.value

            submission = Submission(
                id=submission_id,
                status=TaskStatus.WRONG_ANSWER.value,
                submitted_at=submitted_at,
                task_id=str(task_id),
                answer=answer,
                explanation=check_result.error
            )

        self.db.commit()
        return submission

    def ensure_valid_task(self, task_id: int, team_id: int) -> Task:
        stmt = select(Task).where(
            (Task.id == task_id) &
            (Task.team_id == team_id)
        )
        task = self.db.execute(stmt).scalar_one_or_none()

        if task is None:
            raise ValueError(f"Task with id {task_id} not found for team {team_id}")

        return task

    def submit_task_answer(self, task_id: int, team_id: int, answer: str) -> Submission:
        task = self.ensure_valid_task(task_id, team_id)
        round = self.ensure_valid_round(task.challenge_id)
        round_task_type = self.ensure_valid_task_type(round.id, task.type)

        checker_hint = task.checker_hint

        check_result = self.check_answer(answer, checker_hint, round_task_type.generator_url)

        return self.create_submission(task_id, team_id, answer, check_result, task)