# back/database.py
from sqlalchemy import create_engine, Column, Integer, String, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Connection to AWS Aurora Serverless v2
# Format: postgresql://username:password@endpoint:port/database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/platform")

# Configure engine with parameters optimized for Aurora Serverless v2
engine = create_engine(
    DATABASE_URL,
    # Connection pooling settings
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

# Session factory for database operations
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all ORM models
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
