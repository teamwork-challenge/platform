from sqlalchemy import DateTime, ForeignKey, Enum
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from api_models import RoundStatus, TaskStatus, SubmissionStatus


class Base(DeclarativeBase):
    pass


class AdminKeys(Base):
    __tablename__ = "admin_keys"

    api_key: Mapped[str] = mapped_column(primary_key=True)
    owner: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    api_key: Mapped[str] = mapped_column(unique=True, index=True)
    challenge_id: Mapped[int] = mapped_column(ForeignKey("challenges.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(nullable=False)
    members: Mapped[str] = mapped_column(nullable=False)
    captain_contact: Mapped[str] = mapped_column(nullable=False)
    total_score: Mapped[int] = mapped_column(default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    challenge = relationship("Challenge", back_populates="teams")


class Round(Base):
    __tablename__ = "rounds"

    id: Mapped[int] = mapped_column(primary_key=True)
    challenge_id: Mapped[int] = mapped_column(ForeignKey("challenges.id", ondelete="CASCADE", name='fk_rounds_challenge_id'), nullable=False, index=True)
    index: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[RoundStatus] = mapped_column(Enum(RoundStatus), default=RoundStatus.DRAFT, nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    claim_by_type: Mapped[bool] = mapped_column(default=False, nullable=False)
    allow_resubmit: Mapped[bool] = mapped_column(default=False, nullable=False)
    score_decay: Mapped[str] = mapped_column(default="no", nullable=False)

    # Tell SQLAlchemy which foreign key to use (Challenge <-> Round reference each other)
    challenge = relationship("Challenge", back_populates="rounds", foreign_keys="[Round.challenge_id]")
    task_types = relationship("RoundTaskType", back_populates="round", cascade="all, delete-orphan", passive_deletes=True)


class Challenge(Base):
    __tablename__ = "challenges"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=False)
    current_round_id: Mapped[int | None] = mapped_column( ForeignKey("rounds.id", ondelete="SET NULL", name='fk_challenges_current_round_id'), nullable=True)
    deleted: Mapped[bool] = mapped_column(default=False, nullable=False)

    teams = relationship("Team", back_populates="challenge", cascade="all, delete-orphan", passive_deletes=True)
    # Tell SQLAlchemy which foreign key to use (Challenge <-> Round reference each other)
    rounds = relationship("Round", back_populates="challenge", cascade="all, delete-orphan", passive_deletes=True, foreign_keys="[Round.challenge_id]")


class RoundTaskType(Base):
    __tablename__ = "round_task_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    round_id: Mapped[int] = mapped_column(ForeignKey("rounds.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(nullable=False)
    max_tasks_per_team: Mapped[int] = mapped_column(nullable=True)
    generator_url: Mapped[str] = mapped_column(nullable=False)
    generator_settings: Mapped[str] = mapped_column(nullable=True)
    generator_secret: Mapped[str] = mapped_column(nullable=False)

    round = relationship("Round", back_populates="task_types")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), nullable=False, default=TaskStatus.PENDING)
    challenge_id: Mapped[int] = mapped_column(ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False, index=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    round_id: Mapped[int] = mapped_column(ForeignKey("rounds.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(nullable=False)
    statement_version: Mapped[str] = mapped_column(nullable=True)
    score: Mapped[int] = mapped_column(nullable=True)
    input: Mapped[str] = mapped_column(nullable=True)
    checker_hint: Mapped[str] = mapped_column(nullable=True)
    statement: Mapped[str] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    challenge = relationship("Challenge")
    team = relationship("Team")
    round = relationship("Round")
    submissions = relationship("Submission", back_populates="task", cascade="all, delete-orphan", passive_deletes=True)


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[SubmissionStatus] = mapped_column(Enum(SubmissionStatus), nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    answer: Mapped[str] = mapped_column(nullable=True)
    explanation: Mapped[str] = mapped_column(nullable=True)
    score: Mapped[int] = mapped_column(nullable=True)
    
    task = relationship("Task", back_populates="submissions")
