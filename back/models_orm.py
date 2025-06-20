# back/models_orm.py
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from database import Base

class Challenge(Base):
    """SQLAlchemy ORM model for challenges table"""
    __tablename__ = "challenges"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self):
        """Convert ORM object to dictionary for API response"""
        return {
            "id": self.id,
            "title": self.title
        }

class Task(Base):
    """SQLAlchemy ORM model for tasks table"""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    status = Column(String, nullable=False, default="PENDING")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self):
        """Convert ORM object to dictionary for API response"""
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status
        }