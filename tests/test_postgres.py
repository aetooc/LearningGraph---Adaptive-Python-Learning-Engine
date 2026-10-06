"""Opt-in checks for real migrations and row locking in an isolated schema."""
import os
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import Session

from app.db.seed import seed_curriculum
from app.errors import ApplicationError
from app.models import Attempt, Learner, LearnerMastery, Lesson, Question
from app.schemas import AttemptCreate
from app.services.attempts import record_attempt

pytestmark = pytest.mark.postgres


@pytest.fixture
def postgres_engine(monkeypatch):
    database_url = os.environ.get("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Set TEST_DATABASE_URL for real PostgreSQL checks.")
    from alembic import command
    from alembic.config import Config
    from app.config import get_settings
    from app.db.database import get_engine

    schema = "test_" + uuid4().hex
    admin = create_engine(database_url)
    with admin.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    scoped = create_engine(database_url, connect_args={"options": f"-csearch_path={schema}"})
    get_engine.cache_clear()
    get_settings.cache_clear()
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("PGOPTIONS", f"-csearch_path={schema}")
    try:
        command.upgrade(Config(str(Path(__file__).parents[1] / "alembic.ini")), "head")
        yield scoped
    finally:
        scoped.dispose()
        get_engine().dispose()
        get_engine.cache_clear()
        get_settings.cache_clear()
        with admin.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin.dispose()


def test_postgres_migrations_and_concurrent_attempts(postgres_engine):
    with Session(postgres_engine) as db:
        seed_curriculum(db)
        learner = Learner(name="Alice")
        db.add(learner)
        db.flush()
        lesson = Lesson(
            learner_id=learner.id, concept_id=1, title="Variables", explanation="Assignment",
            examples=["x = 1"], questions=[
                Question(position=index, prompt="What is x?", options=["1", "0", "None", "Error"],
                         correct_option_index=0, misconceptions={"1": "zero", "2": "none", "3": "error"})
                for index in range(3)
            ],
        )
        db.add(lesson)
        db.commit()
        learner_id, concept_id = learner.id, lesson.concept_id
        question_ids = [question.id for question in lesson.questions]

    def submit(question_id):
        with Session(postgres_engine) as session:
            try:
                record_attempt(session, AttemptCreate(learner_id=learner_id, question_id=question_id, selected_option_index=0))
                return 201
            except ApplicationError as error:
                return error.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(submit, [question_ids[0], question_ids[0]])) == [201, 409]
        assert list(pool.map(submit, question_ids[1:])) == [201, 201]
    with Session(postgres_engine) as db:
        mastery = db.get(LearnerMastery, (learner_id, concept_id))
        assert mastery.mastery_score == Decimal("0.30") and mastery.attempts == 3
        assert db.scalar(select(func.count()).select_from(Attempt)) == 3
