from sqlalchemy import select
from sqlalchemy.orm import Session
import uuid
from api_models.models import TeamRequest
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

    def update_challenge(self, challenge_id: int, title: str, description: str):
        stmt = select(Challenge).where(Challenge.id == challenge_id)
        challenge = self.db.execute(stmt).scalar_one_or_none()
        if challenge:
            challenge.title = title
            challenge.description = description
            self.db.commit()
            self.db.refresh(challenge)
            return challenge
        return None

    def delete_challenge(self, challenge_id: int):
        stmt = select(Challenge).where(Challenge.id == challenge_id)
        challenge = self.db.execute(stmt).scalar_one_or_none()
        if challenge:
            self.db.delete(challenge)
            self.db.commit()
            return challenge
        return None


    def create_teams(self, challenge_id: int, teams: List[TeamRequest]):

        # TODO: pass challenge as a parameter instead of challenge_id
        stmt = select(Challenge).where(Challenge.id == challenge_id)
        challenge = self.db.execute(stmt).scalar_one_or_none()

        # TODO: no need
        if challenge is None:
            return None

        created_teams = []

        for team_data in teams:

            team_name = team_data.name
            members = team_data.members
            captain_contact = team_data.captain_contact

            api_key = str(uuid.uuid4())

            team = Team(
                api_key=api_key,
                challenge_id=challenge_id,
                name=team_name,
                members=members,
                captain_contact=captain_contact,
                total_score=0
            )

            self.db.add(team)
            self.db.flush()

            # TODO: Use team object directly instead of creating a new dict
            created_teams.append({
                "team_id": team.id,
                "challenge_id": challenge_id,
                "name": team_name,
                "api_key": api_key,
                "members": members,
                "captain_contact": captain_contact,
            })

        self.db.commit()

        return created_teams

    def create_round(self, challenge_id: int, index: int, start_time: str, end_time: str,
                     claim_by_type: bool = False, allow_resubmit: bool = False,
                     score_decay: str = "no", status: str = "draft"):
        # TODO: Do not do this check manually. Set the Foreign key in the database model and DB will do it automatically.
        stmt = select(Challenge).where(Challenge.id == challenge_id)
        challenge = self.db.execute(stmt).scalar_one_or_none()

        # TODO: Do not return None in such cases. Raise an exception instead. (But due to prev comment, this code should be just deleted)
        if challenge is None:
            return None

        # Create a new round
        round = Round(
            challenge_id=challenge_id,
            index=index,
            start_time=start_time,
            end_time=end_time,
            claim_by_type=claim_by_type,
            allow_resubmit=allow_resubmit,
            score_decay=score_decay,
            status=status
        )

        self.db.add(round)
        self.db.commit()
        self.db.refresh(round)

        return round

    def get_rounds_by_challenge(self, challenge_id: int):
        stmt = select(Round).where(Round.challenge_id == challenge_id)
        return self.db.execute(stmt).scalars().all()

    def get_round(self, round_id: int):
        stmt = select(Round).where(Round.id == round_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def update_round(self, round_id: int, start_time: str = None,
                     end_time: str = None, claim_by_type: bool = None, allow_resubmit: bool = None, 
                     score_decay: str = None, status: str = None):

        stmt = select(Round).where(Round.id == round_id)
        round = self.db.execute(stmt).scalar_one_or_none()

        if round is None:
            return None

        if start_time is not None:
            round.start_time = start_time
        if end_time is not None:
            round.end_time = end_time
        if claim_by_type is not None:
            round.claim_by_type = claim_by_type
        if allow_resubmit is not None:
            round.allow_resubmit = allow_resubmit
        if score_decay is not None:
            round.score_decay = score_decay
        if status is not None:
            round.status = status

        self.db.commit()
        self.db.refresh(round)

        return round

    def delete_round(self, round_id: int):
        stmt = select(Round).where(Round.id == round_id)
        round = self.db.execute(stmt).scalar_one_or_none()

        if round is None:
            return None

        self.db.delete(round)
        self.db.commit()

        return round

    def create_round_task_type(self, round_id: int, type: str, generator_url: str,
                              generator_settings: str = None, generator_secret: str = None):
        stmt = select(Round).where(Round.id == round_id)
        round = self.db.execute(stmt).scalar_one_or_none()

        if round is None:
            return None

        # Create a new round task type
        round_task_type = RoundTaskType(
            round_id=round_id,
            type=type,
            generator_url=generator_url,
            generator_settings=generator_settings,
            generator_secret=generator_secret
        )

        self.db.add(round_task_type)
        self.db.commit()
        self.db.refresh(round_task_type)

        return round_task_type

    def get_round_task_type(self, round_task_type_id: int):
        stmt = select(RoundTaskType).where(RoundTaskType.id == round_task_type_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_round_task_types_by_round(self, round_id: int):
        stmt = select(RoundTaskType).where(RoundTaskType.round_id == round_id)
        return self.db.execute(stmt).scalars().all()

    def update_round_task_type(self, round_task_type_id: int, type: str = None,
                              generator_url: str = None, generator_settings: str = None,
                              generator_secret: str = None):
        stmt = select(RoundTaskType).where(RoundTaskType.id == round_task_type_id)
        round_task_type = self.db.execute(stmt).scalar_one_or_none()

        if round_task_type is None:
            return None

        if type is not None:
            round_task_type.type = type
        if generator_url is not None:
            round_task_type.generator_url = generator_url
        if generator_settings is not None:
            round_task_type.generator_settings = generator_settings
        if generator_secret is not None:
            round_task_type.generator_secret = generator_secret

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
