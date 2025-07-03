from sqlalchemy import select
from sqlalchemy.orm import Session
import uuid
import csv
from io import StringIO

from db_models import Challenge, Team, Round


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


    def create_teams(self, challenge_id: int, csv_content: str):
        """
        CSV format:
        Team name, List of participants, Captain's Contact
        """
        stmt = select(Challenge).where(Challenge.id == challenge_id)
        challenge = self.db.execute(stmt).scalar_one_or_none()

        if challenge is None:
            return None

        csv_file = StringIO(csv_content)
        csv_reader = csv.reader(csv_file)

        created_teams = []

        for row in csv_reader:
            if len(row) < 3:
                continue

            team_name = row[0].strip()
            members = row[1].strip()
            captain_contact = row[2].strip()

            # Generate a new API key
            api_key = str(uuid.uuid4())

            # Create a new team
            team = Team(
                api_key=api_key,
                challenge_id=challenge_id,
                name=team_name,
                members=members,
                captain_contact=captain_contact,
                total_score=0
            )

            self.db.add(team)
            self.db.flush()  # Flush to get the ID without committing

            created_teams.append({
                "team_id": team.id,
                "challenge_id": challenge_id,
                "name": team_name,
                "api_key": api_key,
                "members": members,
                "captain_contact": captain_contact,
            })

        # Commit all changes
        self.db.commit()

        return created_teams

    def create_round(self, challenge_id: int, start_time: str, end_time: str,
                     task_generator: str = None, task_settings: str = None):
        stmt = select(Challenge).where(Challenge.id == challenge_id)
        challenge = self.db.execute(stmt).scalar_one_or_none()

        if challenge is None:
            return None

        # Create a new round
        round = Round(
            challenge_id=challenge_id,
            start_time=start_time,
            end_time=end_time,
            task_generator=task_generator,
            task_settings=task_settings
        )

        self.db.add(round)
        self.db.commit()
        self.db.refresh(round)

        return round

    def get_round(self, round_id: int):
        stmt = select(Round).where(Round.id == round_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_rounds_by_challenge(self, challenge_id: int):
        stmt = select(Round).where(Round.challenge_id == challenge_id)
        return self.db.execute(stmt).scalars().all()

    def update_round(self, round_id: int, start_time: str = None,
                     end_time: str = None, task_generator: str = None, task_settings: str = None):
        stmt = select(Round).where(Round.id == round_id)
        round = self.db.execute(stmt).scalar_one_or_none()

        if round is None:
            return None

        if start_time is not None:
            round.start_time = start_time
        if end_time is not None:
            round.end_time = end_time
        if task_generator is not None:
            round.task_generator = task_generator
        if task_settings is not None:
            round.task_settings = task_settings

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
