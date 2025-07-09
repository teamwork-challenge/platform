from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship
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
    api_key: Mapped[str] = mapped_column(unique=True, index=True)
    challenge_id: Mapped[int] = mapped_column(ForeignKey("challenges.id"), index=True)
    name: Mapped[str] = mapped_column(nullable=False)
    members: Mapped[str] = mapped_column(nullable=False)
    captain_contact: Mapped[str] = mapped_column(nullable=False)
    total_score: Mapped[int] = mapped_column(default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    challenge = relationship("Challenge", back_populates="teams")


class Round(Base):
    __tablename__ = "rounds"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    challenge_id: Mapped[int] = mapped_column(ForeignKey("challenges.id"), nullable=False, index=True)
    index: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(default="draft", nullable=False)
    start_time: Mapped[str] = mapped_column(nullable=False)
    end_time: Mapped[str] = mapped_column(nullable=False)
    claim_by_type: Mapped[bool] = mapped_column(default=False, nullable=False)
    allow_resubmit: Mapped[bool] = mapped_column(default=False, nullable=False)
    score_decay: Mapped[str] = mapped_column(default="no", nullable=False)

    challenge = relationship("Challenge", back_populates="rounds")
    task_types = relationship("RoundTaskType", back_populates="round", cascade="all, delete-orphan")


class Challenge(Base):
    __tablename__ = "challenges"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=False)
    current_round_id: Mapped[int | None] = mapped_column(nullable=True)

    teams = relationship("Team", back_populates="challenge", cascade="all, delete-orphan")
    rounds = relationship("Round", back_populates="challenge", cascade="all, delete-orphan")


class RoundTaskType(Base):
    __tablename__ = "round_task_types"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    round_id: Mapped[int] = mapped_column(ForeignKey("rounds.id"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(nullable=False)
    generator_url: Mapped[str] = mapped_column(nullable=False)
    generator_settings: Mapped[str] = mapped_column(nullable=True)
    generator_secret: Mapped[str] = mapped_column(nullable=False)

    round = relationship("Round", back_populates="task_types")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(nullable=False, default="PENDING")
