from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import requests
import json

from api_models import Task as ApiTask, Team as ApiTeam
from api_models.gen_models import GenRequest, GenResponse, TaskProgress
from db_models import Team, Task, Round, Challenge, RoundTaskType


class PlayerService:
    def __init__(self, db: Session):
        self.db = db

    def get_task(self, task_id: int):
        stmt = select(Task).where(Task.id == task_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_team(self, team_id: int) -> Team:
        stmt = select(Team).where(Team.id == team_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def create_task(self, challenge_id: int, team_id: int, task_type: str) -> Task:
        # Get the current round for the challenge
        stmt = select(Round).where(Round.challenge_id == challenge_id)
        round = self.db.execute(stmt).scalar_one_or_none()
        
        # Check if a round exists
        if round is None:
            raise ValueError("No active round found for this challenge")
            
        # Check if a round is published
        if round.status.lower() != "published":
            raise ValueError("Current round is not published")
            
        # Check if claim_by_type is enabled
        if not round.claim_by_type:
            raise ValueError("Claiming tasks by type is not enabled for this round")
            
        # Check if a round has started
        current_time = datetime.now(timezone.utc)
        if current_time < round.start_time:
            raise ValueError("Round has not started yet")
            
        # Check if a round has ended
        if current_time > round.end_time:
            raise ValueError("Round has already ended")
            
        # Check if task_type is valid for this round
        if task_type is None:
            raise ValueError("Task type must be specified")
            
        # Get the task type from the round
        stmt = select(RoundTaskType).where(
            (RoundTaskType.round_id == round.id) & 
            (RoundTaskType.type == task_type)
        )
        round_task_type = self.db.execute(stmt).scalar_one_or_none()
        
        if round_task_type is None:
            raise ValueError(f"Task type '{task_type}' is not available in this round")
        
        # Check if the team has already taken the maximum number of tasks of this type
        if round_task_type.max_tasks_per_team is not None:
            stmt = select(Task).where(
                (Task.team_id == team_id) & 
                (Task.round_id == round.id) & 
                (Task.type == task_type)
            )
            existing_tasks_count = len(self.db.execute(stmt).scalars().all())
            
            if existing_tasks_count >= round_task_type.max_tasks_per_team:
                raise ValueError(f"Maximum number of tasks of type '{task_type}' already taken")
        
        # Get team information
        stmt = select(Team).where(Team.id == team_id)
        team = self.db.execute(stmt).scalar_one_or_none()
        if team is None:
            raise ValueError("Team not found")
            
        # Create the task with PENDING status to capture ownership
        task = Task(
            title=f"{task_type} Task",
            status="PENDING",
            challenge_id=challenge_id,
            team_id=team_id,
            type=task_type,
            round_id=round.id
        )
        
        self.db.add(task)
        
        # Get the count of existing tasks of this type for the team
        stmt = select(Task).where(
            (Task.team_id == team_id) & 
            (Task.round_id == round.id) & 
            (Task.type == task_type)
        )
        existing_tasks = self.db.execute(stmt).scalars().all()
        
        # Create task progress information
        task_progress = TaskProgress(
            task_index=len(existing_tasks),
            task_count=round_task_type.max_tasks_per_team or 0,
            elapsed_time=int((current_time - round.start_time).total_seconds() / 60),
            total_time=int((round.end_time - round.start_time).total_seconds() / 60)
        )
        
        # Create request for task generator
        gen_request = GenRequest(
            challenge=str(challenge_id),
            team=team.name,
            round=str(round.id),
            progress=task_progress,
            task_settings=round_task_type.generator_settings or ""
        )
        
        try:
            # Make request to task generator
            response = requests.post(
                f"{round_task_type.generator_url}/gen",
                headers={"Content-Type": "application/json"},
                data=json.dumps(gen_request.model_dump())
            )
            response.raise_for_status()
            
            # Parse response
            gen_response = GenResponse.model_validate(response.json())
            
            # Update task with generated data
            task.content = json.dumps({
                "statement_version": gen_response.statement_version,
                "score": gen_response.score,
                "input": gen_response.input,
                "checker_hint": gen_response.checker_hint
            })
            task.status = "ACTIVE"
            
            self.db.commit()
            self.db.refresh(task)
            
        except Exception as e:
            # If there's an error, just raise it - no need to delete as we haven't committed
            raise ValueError(f"Error generating task: {str(e)}")

        return task