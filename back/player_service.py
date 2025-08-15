from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
import requests
import json
from api_models import GenRequest, GenResponse, TaskProgress, CheckRequest, CheckResult, CheckStatus, CheckResponse
from api_models import Submission as ApiSubmission, SubmissionStatus, TaskStatus as ApiTaskStatus
from back.db_models import Team, Task, Round, RoundTaskType, Submission
import random
from pydantic import TypeAdapter

class TaskGenClient:
    """Client for interacting with task generator service."""
    
    def generate_task(self, generator_url: str, generator_secret: str, gen_request: GenRequest) -> GenResponse:
        """Generate task content by calling the task generator and return the generator response."""
        try:
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
            raise
        except Exception as e:
            raise RuntimeError(f"Unexpected error generating task: {str(e)}")

    def check_answer(self, generator_url: str, answer: str, checker_hint: str, input_text: str, task_id: str | None = None) -> CheckResponse:
        check_request = CheckRequest(
            input=input_text,
            answer=answer,
            checker_hint=checker_hint,
            task_id=task_id
        )

        try:
            response = requests.post(
                f"{generator_url}/check",
                headers={"Content-Type": "application/json"},
                data=json.dumps(check_request.model_dump())
            )
            response.raise_for_status()

            adapter = TypeAdapter(list[CheckResult])
            parsed = adapter.validate_python(response.json())
            check_response = CheckResponse(parsed)

            if len(check_response) == 0:
                raise RuntimeError("No check results returned from task generator")

            return check_response

        except Exception as e:
            raise RuntimeError(f"Error checking answer: {str(e)}")


class PlayerService:
    def __init__(self, db: Session):
        self.db = db
        self.task_gen_client = TaskGenClient()

    def get_task(self, task_id: int) -> Task | None:
        stmt = select(Task).where(Task.id == task_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_team(self, team_id: int) -> Team | None:
        stmt = select(Team).where(Team.id == team_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def create_task(self, challenge_id: int, team_id: int, task_type: str) -> Task:
        game_round = self.ensure_valid_round(challenge_id)
        round_task_type = self.ensure_valid_task_type(game_round.id, task_type)
        team = self.ensure_valid_team(team_id)
        self.ensure_task_limit(team_id, game_round.id, task_type, round_task_type)

        task = Task(
            title=f"{task_type} Task",
            status=ApiTaskStatus.PENDING,
            challenge_id=challenge_id,
            team_id=team_id,
            round_id=game_round.id,
            round_task_type_id=round_task_type.id
        )

        self.db.add(task)

        existing_tasks = self.get_existing_tasks(team_id, game_round.id, task_type)

        current_time = datetime.now()

        task_progress = TaskProgress(
            task_index=len(existing_tasks),
            task_count=round_task_type.max_tasks_per_team or 0,
            elapsed_time=int((current_time - game_round.start_time).total_seconds() / 60),
            total_time=int((game_round.end_time - game_round.start_time).total_seconds() / 60)
        )

        gen_response = self.generate_task_content(task, team, game_round, round_task_type, task_progress)

        # Update task with generated data
        task.statement_version = gen_response.statement_version
        task.score = round_task_type.score
        task.input = gen_response.input
        task.checker_hint = gen_response.checker_hint
        task.statement = gen_response.statement
        task.status = ApiTaskStatus.ACTIVE

        self.db.commit()
        self.db.refresh(task)

        return task

    def ensure_valid_round(self, challenge_id: int) -> Round:
        stmt = select(Round).where(Round.challenge_id == challenge_id)
        game_round = self.db.execute(stmt).scalar_one_or_none()

        if game_round is None:
            raise ValueError("No active round found for this challenge")

        if game_round.status.lower() != "published":
            raise ValueError("No current round available for this challenge")

        current_time = datetime.now()
        if current_time < game_round.start_time:
            raise ValueError("Round has not started yet")

        if current_time > game_round.end_time:
            raise ValueError("Round has already ended")

        return game_round

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

    def get_existing_tasks(self, team_id: int, round_id: int, task_type: str | None = None) -> list[Task]:
        condition = (Task.team_id == team_id) & (Task.round_id == round_id)
        if task_type is not None:
            condition &= Task.round_task_type.has(RoundTaskType.type == task_type)
        stmt = select(Task).where(condition)
        return list(self.db.execute(stmt).scalars().all())

    def ensure_task_limit(self, team_id: int, round_id: int, task_type: str, round_task_type: RoundTaskType) -> None:
        if round_task_type.max_tasks_per_team is not None:
            existing_tasks = self.get_existing_tasks(team_id, round_id, task_type)

            if len(existing_tasks) >= round_task_type.max_tasks_per_team:
                raise ValueError(f"Maximum number of tasks of type '{task_type}' already taken")

    def generate_task_content(self, task: Task, team: Team, game_round: Round, round_task_type: RoundTaskType,
                              task_progress: TaskProgress) -> GenResponse:
        """Generate task content by calling the task generator and return the generator response.
        The caller is responsible for updating the task with the response data."""

        gen_request = GenRequest(
            challenge=str(task.challenge_id),
            team=team.name,
            round=str(game_round.id),
            task_id=str(task.id),
            progress=task_progress,
            task_settings=round_task_type.generator_settings or ""
        )

        return self.task_gen_client.generate_task(
            round_task_type.generator_url,
            round_task_type.generator_secret,
            gen_request
        )

    def check_answer(self, answer: str, checker_hint: str, generator_url: str, input_text: str) -> CheckResponse:
        return self.task_gen_client.check_answer(generator_url, answer, checker_hint, input_text)

    def create_submission(self, task_id: int, team_id: int, answer: str,
                           check_result: CheckResult, task: Task) -> ApiSubmission:
        submitted_at = datetime.now(timezone.utc)

        if check_result.status == CheckStatus.ACCEPTED:
            task.status = ApiTaskStatus.AC

            stmt = select(Team).where(Team.id == team_id)
            team = self.db.execute(stmt).scalar_one()

            score = int(float(task.score or 0) * check_result.score)
            team.total_score += score

            # Create Submission
            db_submission = Submission(
                status=SubmissionStatus.AC,
                submitted_at=submitted_at,
                task_id=task_id,
                answer=answer,
                score=score
            )
        else:
            task.status = ApiTaskStatus.WA

            db_submission = Submission(
                status=SubmissionStatus.WA,
                submitted_at=submitted_at,
                task_id=task_id,
                answer=answer,
                explanation=check_result.error
            )

        self.db.add(db_submission)
        self.db.commit()
        
        # Convert to Pydantic
        api_submission = ApiSubmission(
            id=db_submission.id,
            status=db_submission.status,
            submitted_at=db_submission.submitted_at.isoformat(),
            task_id=db_submission.task_id,
            answer=db_submission.answer,
            explanation=db_submission.explanation,
            score=db_submission.score
        )
        
        return api_submission

    def ensure_valid_task(self, task_id: int, team_id: int) -> Task:
        stmt = select(Task).where(
            (Task.id == task_id) &
            (Task.team_id == team_id)
        )
        task = self.db.execute(stmt).scalar_one_or_none()

        if task is None:
            raise ValueError(f"Task with id {task_id} not found for team {team_id}")

        return task

    def submit_task_answer(self, task_id: int, team_id: int, answer: str) -> ApiSubmission:
        task = self.ensure_valid_task(task_id, team_id)
        self.ensure_valid_round(task.challenge_id)
        round_task_type = task.round_task_type

        # Check if the submission is within the time limit (handle naive vs aware datetimes)
        created_at = task.created_at
        if created_at.tzinfo is None or created_at.tzinfo.utcoffset(created_at) is None:
            # Assume naive timestamps are in UTC
            created_at = created_at.replace(tzinfo=timezone.utc)
        current_time = datetime.now(timezone.utc)
        deadline = created_at + timedelta(seconds=round_task_type.time_to_solve * 60)
        
        if current_time > deadline:
            raise ValueError(f"Time limit exceeded. The task had to be solved within {round_task_type.time_to_solve} minutes.")

        checker_hint = task.checker_hint or ""

        check_response = self.check_answer(answer, checker_hint, round_task_type.generator_url, task.input)

        submissions = []

        # Create a submission for each check result
        for check_result in check_response:
            # Process the main task submission
            submission = self.create_submission(task_id, team_id, answer, check_result, task)
            submissions.append(submission)
            
            # Process collaborative scores if present
            if check_result.collaborative_scores:
                for collab_score in check_result.collaborative_scores:
                    try:
                        collab_task_id = int(collab_score.task_id)
                        collab_task = self.get_task(collab_task_id)
                        if collab_task:
                            # Update the collaborative task score
                            collab_team = self.get_team(collab_task.team_id)
                            if collab_team:
                                score_update = int(float(collab_task.score or 0) * collab_score.score)
                                collab_team.total_score += score_update
                                self.db.commit()
                    except (ValueError, TypeError) as e:
                        # Log error but continue processing
                        print(f"Error processing collaborative score: {e}")

        # Return the first submission for backward compatibility
        return submissions[0]

    def get_random_task_type(self, game_round: Round, team_id: int) -> RoundTaskType:
        """Get a random task type for the current round that the team has not yet taken."""
        stmt = select(RoundTaskType).where(RoundTaskType.round_id == game_round.id)
        task_types = self.db.execute(stmt).scalars().all()

        if not task_types:
            raise ValueError("No task types available for this round")

        existing_tasks = self.get_existing_tasks(team_id, game_round.id)

        def get_probability(task_type: RoundTaskType) -> float:
            taken_tasks_count = len([t for t in existing_tasks if t.type == task_type.type])
            return max(0.0, task_type.max_tasks_per_team - taken_tasks_count)

        probs = list(map(get_probability, task_types))
        if not any(prob > 0 for prob in probs):
            raise ValueError("All tasks was already taken for this round")
        choices = random.choices(task_types, weights=probs, k=1)
        return choices[0]
