from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.database import Base
from app.db.seed import seed_curriculum
from app.models import Learner, Lesson, Question
from app.services.validation import validate_lesson
from tests.drafts import valid_lesson


@pytest.fixture
def db():
    # SQLite keeps fast tests independent of Docker; PostgreSQL checks are separate.
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    with Session(engine) as session:
        seed_curriculum(session)
        session.commit()
        yield session
    engine.dispose()


@pytest.fixture
def lesson(db):
    learner = Learner(name="Alice")
    db.add(learner)
    db.flush()
    draft = validate_lesson(valid_lesson(), "variables")
    lesson = Lesson(
        learner_id=learner.id, concept_id=1, title=draft.title,
        explanation=draft.explanation, examples=draft.examples,
        questions=[
            Question(
                position=index, prompt=question.prompt, code_snippet=question.code_snippet,
                options=question.options, correct_option_index=question.correct_option_index,
                misconceptions={str(item.option_index): item.tag for item in question.misconceptions},
            )
            for index, question in enumerate(draft.questions)
        ],
    )
    db.add(lesson)
    db.commit()
    return lesson


@pytest.fixture
def generator():
    from app.services.llm import OpenAIGenerator

    provider = Mock(spec=OpenAIGenerator)
    provider.lesson.side_effect = lambda context: valid_lesson(context["concept_slug"])
    provider.feedback.return_value = {
        "explanation": "Assignment binds x to 1.",
        "what_you_misunderstood": "Assignment does not initialize x to None.",
        "how_to_improve": "Read the expression on the right of the assignment.",
        "short_example": "x = 1\nprint(x)  # 1",
    }
    return provider


@pytest.fixture
def client(db, generator, monkeypatch):
    from fastapi.testclient import TestClient

    from app.config import get_settings
    from app.db.database import get_db
    from app.api.dependencies import get_generator
    from app.main import app

    monkeypatch.setenv("MASTERY_THRESHOLD", "0.70")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("OPENAI_MODEL", "")
    get_settings.cache_clear()

    def test_db():
        yield db

    app.dependency_overrides[get_db] = test_db
    app.dependency_overrides[get_generator] = lambda: generator
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    get_settings.cache_clear()
