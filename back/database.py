from sqlalchemy import create_engine
import json
import boto3
from botocore.exceptions import ClientError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from typing import Generator

from db_models import Base


def get_connection_string():
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


def get_db_engine():
    engine = create_engine(
        get_connection_string(),
        pool_size=5,  # Default number of connections to maintain
        max_overflow=10,  # Maximum number of connections to allow in addition to pool_size
        pool_timeout=30,  # Seconds to wait before giving up on getting a connection
        pool_recycle=1800,  # Recycle connections after 30 minutes to avoid stale connections
        # Query execution settings
        connect_args={
            "connect_timeout": 10,  # Connection timeout in seconds
            "application_name": "platform-api"  # Identify application in AWS monitoring
        }
    )
    return engine

def get_test_db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    return engine


def get_test_db_session(create_tables=True):
    engine = get_test_db_engine()
    Base.metadata.create_all(engine) if create_tables else None
    return Session(bind=engine, autocommit=False, autoflush=False)

SessionLocal = sessionmaker(bind=get_db_engine(), autoflush=False, autocommit=False)

def get_db_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
