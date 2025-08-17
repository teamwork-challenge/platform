from typing import Sequence, List

import sqlalchemy
from sqlalchemy import select
from sqlalchemy.orm import Session

from api_models import ChallengeUpdateRequest
from api_models import RoundCreateRequest, RoundTaskTypeCreateRequest
from back.db_models import Challenge, Round, RoundTaskType


class ChallengeService:
    def __init__(self, db: Session):
        self.db = db

    # Challenge CRUD
    def get_challenge(self, challenge_id: int) -> Challenge | None:
        stmt = select(Challenge).where(Challenge.id == challenge_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_all_challenges(self) -> Sequence[Challenge]:
        return self.db.execute(select(Challenge)).scalars().all()

    def create_challenge(self, title: str, description: str) -> Challenge:
        challenge = Challenge(title=title, description=description)
        self.db.add(challenge)
        self.db.commit()
        self.db.refresh(challenge)
        return challenge

    def update_challenge(self, challenge_id: int, update: ChallengeUpdateRequest) -> Challenge | None:
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

    def delete_challenge(self, challenge_id: int) -> Challenge | None:
        stmt = select(Challenge).where(Challenge.id == challenge_id)
        challenge = self.db.execute(stmt).scalar_one_or_none()
        if challenge:
            challenge.deleted = True
            self.db.commit()
            return challenge
        return None

    # Rounds
    def create_round(self, round_data: RoundCreateRequest) -> Round:
        game_round = Round(
            challenge_id=round_data.challenge_id,
            index=round_data.index,
            start_time=round_data.start_time,
            end_time=round_data.end_time,
            claim_by_type=round_data.claim_by_type,
            allow_resubmit=round_data.allow_resubmit,
            score_decay=round_data.score_decay,
            status=round_data.status
        )

        self.db.add(game_round)
        # Raises SQLAlchemyError if challenge_id does not exist
        self.db.commit()
        self.db.refresh(game_round)

        return game_round

    def get_rounds_by_challenge(self, challenge_id: int) -> Sequence[Round]:
        stmt = select(Round).where(Round.challenge_id == challenge_id)
        return self.db.execute(stmt).scalars().all()

    def get_round(self, round_id: int) -> Round | None:
        stmt = select(Round).where(Round.id == round_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def update_round(self, round_id: int, round_data: RoundCreateRequest) -> Round | None:
        stmt = select(Round).where(Round.id == round_id)
        game_round = self.db.execute(stmt).scalar_one_or_none()

        if game_round is None:
            return None

        if round_data.start_time is not None:
            game_round.start_time = round_data.start_time
        if round_data.end_time is not None:
            game_round.end_time = round_data.end_time
        if round_data.claim_by_type is not None:
            game_round.claim_by_type = round_data.claim_by_type
        if round_data.allow_resubmit is not None:
            game_round.allow_resubmit = round_data.allow_resubmit
        if round_data.score_decay is not None:
            game_round.score_decay = round_data.score_decay
        if round_data.status is not None:
            game_round.status = round_data.status

        self.db.commit()
        self.db.refresh(game_round)

        return game_round

    def delete_round(self, round_id: int) -> None:
        round_stmt = sqlalchemy.delete(Round).where(Round.id == round_id)
        self.db.execute(round_stmt)
        self.db.commit()

    # Round Task Types
    def create_round_task_type(self, task_type_data: RoundTaskTypeCreateRequest) -> RoundTaskType:
        round_task_type = RoundTaskType(
            round_id=task_type_data.round_id,
            type=task_type_data.type,
            generator_url=task_type_data.generator_url,
            generator_settings=task_type_data.generator_settings,
            generator_secret=task_type_data.generator_secret,
            max_tasks_per_team=task_type_data.max_tasks_per_team,
            time_to_solve=task_type_data.time_to_solve
        )

        self.db.add(round_task_type)
        self.db.commit()
        self.db.refresh(round_task_type)

        return round_task_type

    def get_round_task_type(self, round_task_type_id: int) -> RoundTaskType | None:
        stmt = select(RoundTaskType).where(RoundTaskType.id == round_task_type_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_round_task_types_by_round(self, round_id: int) -> Sequence[RoundTaskType]:
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
        if task_type_data.max_tasks_per_team is not None:
            round_task_type.max_tasks_per_team = task_type_data.max_tasks_per_team
        if task_type_data.time_to_solve is not None:
            round_task_type.time_to_solve = task_type_data.time_to_solve

        self.db.commit()
        self.db.refresh(round_task_type)

        return round_task_type

    def delete_round_task_type(self, round_task_type_id: int) -> RoundTaskType | None:
        stmt = select(RoundTaskType).where(RoundTaskType.id == round_task_type_id)
        round_task_type = self.db.execute(stmt).scalar_one_or_none()

        if round_task_type is None:
            return None

        self.db.delete(round_task_type)
        self.db.commit()

        return round_task_type
