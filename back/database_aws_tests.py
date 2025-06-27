from database import get_db_engine
from sqlalchemy import text
from sqlalchemy.orm import Session
import uuid

from back.models_orm import Base, AdminKeys, Team, Challenge, Task


def test_connection():
    """
    Read README.md to know how to make it work!
    """
    engine = get_db_engine()
    with engine.connect() as conn:
        # Check if the connection is successful
        res = conn.execute(text("SELECT table_name from information_schema.tables WHERE table_type = 'BASE TABLE' AND table_schema = 'public'"))
        print(res.all())

def recreate_db_tables():
    engine = get_db_engine()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(engine)
    create_test_data()

def create_test_data():
    """
    Create test data in the tables: AdminKeys, Teams, Challenges, Tasks
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
            api_key=admin_key1.api_key,
            challenge_id=challenge1.id,
            name="Test Team 1",
            members="Member 1, Member 2",
            total_score=100
        )
        team2 = Team(
            id=2,
            api_key=admin_key2.api_key,
            challenge_id=challenge2.id,
            name="Test Team 2",
            members="Member 3, Member 4",
            total_score=200
        )
        session.add_all([team1, team2])

        # Create 2 Tasks
        task1 = Task(
            title="Test Task 1",
            status="PENDING"
        )
        task2 = Task(
            title="Test Task 2",
            status="COMPLETED"
        )
        session.add_all([task1, task2])

        # Commit all changes
        session.commit()

        print("Test data created successfully!")
