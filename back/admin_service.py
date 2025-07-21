from sqlalchemy import select
from sqlalchemy.orm import Session
import uuid

from api_models import ChallengeUpdateRequest
from api_models.models import TeamCreateRequest, RoundCreateRequest, RoundTaskTypeCreateRequest
from db_models import Challenge, Team, Round, RoundTaskType
from typing import List


class AdminService:
    def __init__(self, db: Session):
        self.db = db

    def get_challenge(self, challenge_id: int) -> Challenge | None:
        stmt = select(Challenge).where(Challenge.id == challenge_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_all_challenges(self):
        return self.db.execute(select(Challenge)).scalars().all()

    def create_challenge(self, title: str, description: str):
        challenge = Challenge(title=title, description=description)
        self.db.add(challenge)
        self.db.commit()
        self.db.refresh(challenge)
        return challenge

    def update_challenge(self, challenge_id: int, update: ChallengeUpdateRequest):
        stmt = select(Challenge).where(Challenge.id == challenge_id)
        challenge = self.db.execute(stmt).scalar_one_or_none()
        if challenge:
            if update.title is not None:
                challenge.title = update.title
            if update.description is not None:
                challenge.description = update.description
            if update.deleted is not None:
                challenge.deleted = update.deleted
            if update.current_round_id is not None:
                challenge.current_round_id = update.current_round_id
            self.db.commit()
            self.db.refresh(challenge)
            return challenge
        return None

    def delete_challenge(self, challenge_id: int):
        stmt = select(Challenge).where(Challenge.id == challenge_id)
        challenge = self.db.execute(stmt).scalar_one_or_none()
        if challenge:
            challenge.deleted = True
            self.db.commit()
            return challenge
        return None

    def create_teams(self, challenge: Challenge, teams: List[TeamCreateRequest]):

        created_teams = []

        for team_data in teams:
            team_name = team_data.name
            members = team_data.members
            captain_contact = team_data.captain_contact

            api_key = str(uuid.uuid4())

            team = Team(
                api_key=api_key,
                challenge_id=challenge.id,
                name=team_name,
                members=members,
                captain_contact=captain_contact,
                total_score=0
            )

            self.db.add(team)
            self.db.flush()

            created_teams.append(team)

        self.db.commit()

        return created_teams

    def create_round(self, round_data: RoundCreateRequest) -> Round:
        # Create a new round
        round = Round(
            challenge_id=round_data.challenge_id,
            index=round_data.index,
            start_time=round_data.start_time,
            end_time=round_data.end_time,
            claim_by_type=round_data.claim_by_type,
            allow_resubmit=round_data.allow_resubmit,
            score_decay=round_data.score_decay,
            status=round_data.status
        )

        self.db.add(round)
        # Raises SQLAlchemyError: If the challenge_id does not exist (foreign key constraint)
        self.db.commit()
        self.db.refresh(round)

        return round

    def get_rounds_by_challenge(self, challenge_id: int):
        stmt = select(Round).where(Round.challenge_id == challenge_id)
        return self.db.execute(stmt).scalars().all()

    def get_round(self, round_id: int):
        stmt = select(Round).where(Round.id == round_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def update_round(self, round_id: int, round_data: RoundCreateRequest = None, status: str = None) -> Round | None:
        stmt = select(Round).where(Round.id == round_id)
        round = self.db.execute(stmt).scalar_one_or_none()

        if round is None:
            return None

        if round_data is not None:
            if round_data.start_time is not None:
                round.start_time = round_data.start_time
            if round_data.end_time is not None:
                round.end_time = round_data.end_time
            if round_data.claim_by_type is not None:
                round.claim_by_type = round_data.claim_by_type
            if round_data.allow_resubmit is not None:
                round.allow_resubmit = round_data.allow_resubmit
            if round_data.score_decay is not None:
                round.score_decay = round_data.score_decay
            if round_data.status is not None:
                round.status = round_data.status
        elif status is not None:
            round.status = status

        self.db.commit()
        self.db.refresh(round)

        return round

    def delete_round(self, round_id: int):
        stmt = select(Challenge).where(Challenge.current_round_id == round_id)
        challenge = self.db.execute(stmt).scalar_one_or_none()
        if challenge:
            challenge.current_round_id = None
            self.db.flush()

        stmt = select(Round).where(Round.id == round_id)
        round = self.db.execute(stmt).scalar_one_or_none()

        if round is None:
            return None

        self.db.delete(round)
        self.db.commit()

        return round

    def create_round_task_type(self, task_type_data: RoundTaskTypeCreateRequest) -> RoundTaskType:
        # Create a new round task type
        round_task_type = RoundTaskType(
            round_id=task_type_data.round_id,
            type=task_type_data.type,
            generator_url=task_type_data.generator_url,
            generator_settings=task_type_data.generator_settings,
            generator_secret=task_type_data.generator_secret
        )

        self.db.add(round_task_type)
        # Raises SQLAlchemyError: If the round_id does not exist (foreign key constraint)
        self.db.commit()
        self.db.refresh(round_task_type)

        return round_task_type

    def get_round_task_type(self, round_task_type_id: int):
        stmt = select(RoundTaskType).where(RoundTaskType.id == round_task_type_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_round_task_types_by_round(self, round_id: int):
        stmt = select(RoundTaskType).where(RoundTaskType.round_id == round_id)
        return self.db.execute(stmt).scalars().all()

    def update_round_task_type(self, task_type_id: int, task_type_data: RoundTaskTypeCreateRequest) -> RoundTaskType | None:
        stmt = select(RoundTaskType).where(RoundTaskType.id == task_type_id)
        round_task_type = self.db.execute(stmt).scalar_one_or_none()

        if round_task_type is None:
            return None

        if task_type_data.type is not None:
            round_task_type.type = task_type_data.type
        if task_type_data.generator_url is not None:
            round_task_type.generator_url = task_type_data.generator_url
        if task_type_data.generator_settings is not None:
            round_task_type.generator_settings = task_type_data.generator_settings
        if task_type_data.generator_secret is not None:
            round_task_type.generator_secret = task_type_data.generator_secret

        self.db.commit()
        self.db.refresh(round_task_type)

        return round_task_type

    def delete_round_task_type(self, round_task_type_id: int):
        stmt = select(RoundTaskType).where(RoundTaskType.id == round_task_type_id)
        round_task_type = self.db.execute(stmt).scalar_one_or_none()

        if round_task_type is None:
            return None

        self.db.delete(round_task_type)
        self.db.commit()

        return round_task_type

    def get_teams_by_challenge(self, challenge_id: int):
        stmt = select(Team).where(Team.challenge_id == challenge_id)
        return self.db.execute(stmt).scalars().all()

    def get_all_teams(self):
        stmt = select(Team)
        return self.db.execute(stmt).scalars().all()
