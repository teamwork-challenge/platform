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
            status="PENDING", # TODO use enums!
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
        return self.db.execute(stmt).scalars().all() # TODO: fix types!
        
    def ensure_task_limit(self, team_id: int, round_id: int, task_type: str, round_task_type: RoundTaskType) -> None:
        if round_task_type.max_tasks_per_team is not None:
            existing_tasks = self.get_existing_tasks(team_id, round_id, task_type)
            
            if len(existing_tasks) >= round_task_type.max_tasks_per_team:
                raise ValueError(f"Maximum number of tasks of type '{task_type}' already taken")

    # TODO: convert it to function that returns generator response. Handle all task modifications on the calling site.
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
            
            #TODO: Do not use ValueError — they are used for validation errors of back client requests. Here nothing is wrong with user request — the configuration of the tasks is wrong. So use RuntimeError to end up with 500-http-error instead of 400.
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
            task.status = "ACTIVE" # TODO no need this status. PENDING is enough.
            
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

    #TODO: Duplication? See ensure_valid_round, ensure_valid_task_type, etc
    def _validate_task_type(self, round_id: int, task_type: str) -> RoundTaskType:
        """Validate that the task type is available in the round."""
        stmt = select(RoundTaskType).where(
            (RoundTaskType.round_id == round_id) &
            (RoundTaskType.type == task_type)
        )
        round_task_type = self.db.execute(stmt).scalar_one_or_none()

        if round_task_type is None:
            raise ValueError(f"Task type '{task_type}' is not available in this round")

        return round_task_type

    def _check_answer(self, answer: str, checker_hint: str, generator_url: str) -> CheckResult:
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
            raise ValueError(f"Error checking answer: {str(e)}")  #TODO: Do not use ValueError here — they are used for validation errors of back client requests. Here nothing is wrong with user request — the configuration of the tasks is wrong. So use RuntimeError to end up with 500-http-error instead of 400.


    def _create_submission(self, task_id: int, team_id: int, answer: str,
                           check_result: CheckResult, task_content: dict, task: Task) -> SubmissionExtended:
        """Create a submission based on the check result."""
        submission_id = str(uuid.uuid4())
        submitted_at = datetime.now(timezone.utc).isoformat()

        if check_result.status == CheckStatus.ACCEPTED:
            task.status = "ACCEPTED" #TODO use enums instead of strings

            stmt = select(Team).where(Team.id == team_id)
            team = self.db.execute(stmt).scalar_one_or_none()

            score = int(float(task_content.get("score", "0")) * check_result.score)
            team.total_score += score

            submission = SubmissionExtended(
                id=submission_id,
                status="ACCEPTED",
                submitted_at=submitted_at,
                task_id=str(task_id),
                answer=answer,
                score=score
            )
        else:
            task.status = "WRONG_ANSWER"

            submission = SubmissionExtended(
                id=submission_id,
                status="WRONG_ANSWER",
                submitted_at=submitted_at,
                task_id=str(task_id),
                answer=answer,
                explanation=check_result.error
            )

        self.db.commit()
        return submission

    def submit_task_answer(self, task_id: int, team_id: int, answer: str) -> SubmissionExtended:
        """Submit an answer for the task."""
        task = self._validate_task(task_id, team_id) #TODO: ?!? no such function in this class!
        round = self._validate_round(task.round_id)
        round_task_type = self._validate_task_type(round.id, task.type)

        task_content = json.loads(task.content)
        checker_hint = task_content.get("checker_hint")

        check_result = self._check_answer(answer, checker_hint, round_task_type.generator_url)

        return self._create_submission(task_id, team_id, answer, check_result, task_content, task)