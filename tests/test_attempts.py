from decimal import Decimal
from unittest.mock import Mock

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.errors import ApplicationError
from app.models import Attempt, Learner, LearnerMastery
from app.schemas import AttemptCreate
from app.services.attempts import record_attempt
from app.services.feedback import feedback_for_mistake


def submission(lesson, position=0, option=0):
    return AttemptCreate(learner_id=lesson.learner_id, question_id=lesson.questions[position].id, selected_option_index=option)


def test_grading_and_misconception_mapping_are_deterministic(db, lesson):
    correct, mistake = record_attempt(db, submission(lesson))
    assert correct.correct and correct.mastery_score == 0.10
    assert correct.misconception_tag is None and mistake is None
    incorrect, mistake = record_attempt(db, submission(lesson, 1, 2))
    assert not incorrect.correct and incorrect.mastery_score == 0.05
    assert incorrect.misconception_tag == "assignment_is_none"
    assert mistake["selected_answer"] == "None"
    assert mistake["correct_answer"] == "1"
    assert mistake["misconception"] == "assignment_is_none"
    assert incorrect.concept_attempts == 2
    assert not db.in_transaction()


def test_duplicate_does_not_change_mastery_and_database_enforces_uniqueness(db, lesson):
    body = submission(lesson)
    record_attempt(db, body)
    with pytest.raises(ApplicationError) as error:
        record_attempt(db, body.model_copy(update={"selected_option_index": 1}))
    assert error.value.status_code == 409
    mastery = db.get(LearnerMastery, (lesson.learner_id, lesson.concept_id))
    assert mastery.mastery_score == Decimal("0.10") and mastery.attempts == 1
    db.add(Attempt(learner_id=body.learner_id, question_id=body.question_id, selected_option_index=0, correct=True))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
    assert db.scalar(select(func.count()).select_from(Attempt)) == 1


@pytest.mark.parametrize("result", [RuntimeError("provider offline"), {"explanation": " "}])
def test_feedback_failure_preserves_committed_progress(db, lesson, result):
    response, mistake = record_attempt(db, submission(lesson, option=1))
    mistake["code_snippet"] = " "
    assert not db.in_transaction()
    generator = Mock()
    if isinstance(result, Exception):
        generator.feedback.side_effect = result
    else:
        generator.feedback.return_value = result
    feedback, source = feedback_for_mistake(generator, mistake)
    assert feedback.explanation and source == "fallback"
    # Roll back a subsequent transaction to prove progress was already durable.
    db.rollback()
    stored = db.get(Attempt, response.id)
    mastery = db.get(LearnerMastery, (lesson.learner_id, lesson.concept_id))
    assert stored is not None and not stored.correct
    assert mastery.mastery_score == Decimal("0.00") and mastery.attempts == 1


def test_failed_commit_rolls_back_attempt_and_mastery_together(db, lesson, monkeypatch):
    def fail_commit():
        raise IntegrityError("COMMIT", {}, RuntimeError("simulated storage failure"))

    monkeypatch.setattr(db, "commit", fail_commit)
    with pytest.raises(IntegrityError):
        record_attempt(db, submission(lesson))
    assert db.scalar(select(func.count()).select_from(Attempt)) == 0
    assert db.get(LearnerMastery, (lesson.learner_id, lesson.concept_id)) is None


def test_another_learner_cannot_submit_this_lesson_question(db, lesson):
    bob = Learner(name="Bob")
    db.add(bob)
    db.commit()
    body = submission(lesson).model_copy(update={"learner_id": bob.id})
    with pytest.raises(ApplicationError) as error:
        record_attempt(db, body)
    assert error.value.status_code == 403
    assert db.scalar(select(func.count()).select_from(Attempt)) == 0
