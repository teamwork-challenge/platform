from database import get_db_engine
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from db_models import Base, AdminKeys, Team, Challenge, Task, Round, RoundTaskType
from api_models.models import RoundStatus, TaskStatus


def test_connection():
    """
    Read README.md to know how to make it work!
    """
    engine = get_db_engine()
    with engine.connect() as conn:
        # Check if the connection is successful
        res = conn.execute(text("SELECT table_name from information_schema.tables WHERE table_type = 'BASE TABLE' AND table_schema = 'public'"))
        print(res.all())


def test_recreate_db_tables():
    engine = get_db_engine()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(engine)
    create_test_data()


def create_test_data():
    """
    Create test data in the tables: AdminKeys, Teams, Challenges, Rounds, RoundTaskTypes, Tasks
    Creates 2 objects per each table
    """
    engine = get_db_engine()
    with Session(engine) as session:
        # Create 2 AdminKeys
        admin_key1 = AdminKeys(
            api_key="admin1",
            owner="Test Admin 1"
        )
        admin_key2 = AdminKeys(
            api_key="admin2",
            owner="Test Admin 2"
        )
        session.add_all([admin_key1, admin_key2])
        session.flush()  # Flush to get the generated IDs
        session.commit()

        # Create 2 Challenges
        challenge1 = Challenge(
            title="Test Challenge 1",
            description="Description for test challenge 1"
        )
        challenge2 = Challenge(
            title="Test Challenge 2",
            description="Description for test challenge 2"
        )
        session.add_all([challenge1, challenge2])
        session.flush()  # Flush to get the generated IDs

        # Create 2 Teams
        team1 = Team(
            id=1,
            api_key="team1",
            challenge_id=challenge1.id,
            name="Test Team 1",
            members="Member 1, Member 2",
            captain_contact="@xoposhiy",
            total_score=100
        )
        team2 = Team(
            id=2,
            api_key="team2",
            challenge_id=challenge2.id,
            name="Test Team 2",
            members="Member 3, Member 4",
            captain_contact="@xoposhiy",
            total_score=200
        )
        session.add_all([team1, team2])

        # Create 2 Rounds
        now = datetime.now(timezone.utc)
        round1 = Round(
            id=1,
            challenge_id=challenge1.id,
            index=1,
            status=RoundStatus.DRAFT,
            start_time=now,
            end_time=now + timedelta(hours=2000),
            claim_by_type=False,
            allow_resubmit=True,
            score_decay="no"
        )
        round2 = Round(
            id=2,
            challenge_id=challenge2.id,
            index=1,
            status=RoundStatus.PUBLISHED,
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=2000),
            claim_by_type=True,
            allow_resubmit=False,
            score_decay="linear"
        )
        session.add_all([round1, round2])
        session.flush()  # Flush to get the generated IDs

        # Set current round for challenge1
        challenge1.current_round_id = round1.id
        session.flush()

        # Create RoundTaskTypes
        round_task_type1 = RoundTaskType(
            round_id=round1.id,
            type="a_plus_b",
            generator_url="http://localhost:8000/a_plus_b",
            generator_settings=None,
            generator_secret="twc",
            max_tasks_per_team=3
        )
        round_task_type2 = RoundTaskType(
            round_id=round2.id,
            type="right_time",
            generator_url="http://localhost:8000/right_time",
            generator_settings="complication2:1,complication3:2,complication4:3",
            generator_secret="twc",
            max_tasks_per_team=5
        )
        session.add_all([round_task_type1, round_task_type2])
        session.flush()

        # Create 2 Tasks
        task1 = Task(
            title="Test Task 1",
            status=TaskStatus.PENDING,
            challenge_id=challenge1.id,
            team_id=team1.id,
            round_id=round1.id,
            type="a_plus_b",
            content="{\"input\": \"1 2\"}",
            statement="Given two integers a and b, find their sum a + b."
        )
        task2 = Task(
            title="Test Task 2",
            status=TaskStatus.AC,
            challenge_id=challenge2.id,
            team_id=team2.id,
            round_id=round2.id,
            type="right_time",
            content="{\"input\": \"12:00\"}",
            statement="Send the answer back exactly in the moment of time, specified in the task input."
        )
        session.add_all([task1, task2])

        # Commit all changes
        session.commit()

        print("Test data created successfully!")


# Run the test_recreate_db_tables function when this script is executed directly
if __name__ == "__main__":
    test_recreate_db_tables()
