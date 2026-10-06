from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Concept(Base):
    __tablename__ = "concepts"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)


class Prerequisite(Base):
    __tablename__ = "prerequisites"
    __table_args__ = (CheckConstraint("concept_id != prerequisite_id", name="no_self_edge"),)

    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id"), primary_key=True)
    prerequisite_id: Mapped[int] = mapped_column(ForeignKey("concepts.id"), primary_key=True)


class Learner(Base):
    __tablename__ = "learners"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    goal: Mapped[str] = mapped_column(String(100), default="Python Fundamentals")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LearnerMastery(Base):
    __tablename__ = "learner_mastery"
    __table_args__ = (
        CheckConstraint("mastery_score >= 0 AND mastery_score <= 1", name="mastery_range"),
        CheckConstraint("attempts >= 0", name="nonnegative_attempts"),
    )

    learner_id: Mapped[int] = mapped_column(ForeignKey("learners.id"), primary_key=True)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id"), primary_key=True)
    mastery_score: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("0.00"))
    attempts: Mapped[int] = mapped_column(default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(primary_key=True)
    learner_id: Mapped[int] = mapped_column(ForeignKey("learners.id"), index=True)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id"))
    title: Mapped[str] = mapped_column(String(300))
    explanation: Mapped[str] = mapped_column(Text)
    examples: Mapped[list[str]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    questions: Mapped[list[Question]] = relationship(order_by="Question.position", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"
    __table_args__ = (
        UniqueConstraint("lesson_id", "position", name="unique_lesson_question_position"),
        CheckConstraint("correct_option_index >= 0 AND correct_option_index <= 3", name="answer_index_range"),
        CheckConstraint("position >= 0 AND position <= 2", name="question_position_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id"))
    position: Mapped[int]
    prompt: Mapped[str] = mapped_column(Text)
    code_snippet: Mapped[str | None] = mapped_column(Text)
    options: Mapped[list[str]] = mapped_column(JSON)
    correct_option_index: Mapped[int]
    misconceptions: Mapped[dict[str, str]] = mapped_column(JSON)


class Attempt(Base):
    __tablename__ = "attempts"
    __table_args__ = (
        UniqueConstraint("learner_id", "question_id", name="unique_learner_question_attempt"),
        CheckConstraint("selected_option_index >= 0 AND selected_option_index <= 3", name="selected_index_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    learner_id: Mapped[int] = mapped_column(ForeignKey("learners.id"))
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    selected_option_index: Mapped[int]
    correct: Mapped[bool]
    misconception_tag: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
