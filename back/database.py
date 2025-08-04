from sqlalchemy import create_engine
import json
import boto3
import os
from botocore.exceptions import ClientError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from typing import Generator
from sqlalchemy.engine import Engine
from back.db_models import Base, AdminKeys, Team, Challenge, Task, Round, RoundTaskType
from api_models import RoundStatus, TaskStatus
from datetime import datetime, timedelta, timezone


def get_connection_string() -> str:
    secret_name = "rds-db-credentials/cluster-H2HS3S7S4UFREZFDQIJEL4JBZY/postgres/1750785162158"
    region_name = "eu-north-1"
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e
    secret = json.loads(response['SecretString'])
    conn_string = f"postgresql://{secret['username']}:{secret['password']}@{secret['host']}:{secret['port']}/{secret['dbInstanceIdentifier']}"
    return conn_string


def get_db_engine() -> Engine:
    """
    Returns a database engine.
    - Uses in-memory SQLite
    - Falls back to PostgreSQL (AWS Secrets Manager) if in prod environment.
    Control via env:
      STAGE=prod
    """
    stage = (os.environ.get("STAGE") or "").lower()

    use_sqlite = stage != "prod"

    if use_sqlite:
        print("Using SQLite in-memory database for testing")
        return get_test_db_engine()
    print("Using PostgreSQL")
    return create_engine(
            get_connection_string(),
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,
            connect_args={
                "connect_timeout": 10,
                "application_name": "platform-api",
            },
        )

def get_test_db_engine() -> Engine:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    create_test_data(engine)
    return engine


def get_test_db_session(create_tables: bool = True) -> Session:
    engine = get_test_db_engine()
    Base.metadata.create_all(engine) if create_tables else None
    return Session(bind=engine, autocommit=False, autoflush=False)

def create_test_data(engine: Engine | None = None) -> None:
    """
    Create test data in the tables: AdminKeys, Teams, Challenges, Rounds, RoundTaskTypes, Tasks
    Creates 2 objects per each table
    """
    if engine is None:
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
        session.flush()

        # Create 2 Teams
        team1 = Team(
            api_key="team1",
            challenge_id=challenge1.id,
            name="Test Team 1",
            members="Member 1, Member 2",
            captain_contact="@xoposhiy",
            total_score=100
        )
        team2 = Team(
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
        session.flush()

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
            input="1 2",
            statement_version="1.0",
            score=100,
            statement="Given two integers a and b, find their sum a + b."
        )
        task2 = Task(
            title="Test Task 2",
            status=TaskStatus.AC,
            challenge_id=challenge2.id,
            team_id=team2.id,
            round_id=round2.id,
            type="right_time",
            input="12:00",
            statement_version="1.0",
            score=200,
            statement="Send the answer back exactly in the moment of time, specified in the task input."
        )
        session.add_all([task1, task2])

        session.commit()

        print("Test data created successfully!")

SessionLocal = sessionmaker(bind=get_db_engine(), autoflush=False, autocommit=False)

def get_db_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

