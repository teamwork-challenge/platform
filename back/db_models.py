from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime


class Base(DeclarativeBase):
    pass


class AdminKeys(Base):
    __tablename__ = "admin_keys"

    api_key: Mapped[str] = mapped_column(primary_key=True, index=True)
    owner: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    api_key: Mapped[str] = mapped_column(primary_key=True, index=True)
    challenge_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(nullable=False)
    members: Mapped[str] = mapped_column(nullable=False)
    captain_contact: Mapped[str] = mapped_column(nullable=False)
    total_score: Mapped[int] = mapped_column(default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Round(Base):
    __tablename__ = "rounds"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    challenge_id: Mapped[int] = mapped_column(nullable=False, index=True)
    start_time: Mapped[str] = mapped_column(nullable=False)
    end_time: Mapped[str] = mapped_column(nullable=False)
    task_generator: Mapped[str] = mapped_column(nullable=True)
    task_settings: Mapped[str] = mapped_column(nullable=True)


class Challenge(Base):
    __tablename__ = "challenges"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=False)
    current_round_id: Mapped[int | None] = mapped_column(nullable=True)


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(nullable=False, default="PENDING")
