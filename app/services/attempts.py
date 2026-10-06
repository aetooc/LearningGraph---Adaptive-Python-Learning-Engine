from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import ApplicationError
from app.models import Attempt, Concept, Learner, LearnerMastery, Lesson, Question
from app.schemas import AttemptCreate, AttemptResponse
from app.services.mastery import calculate_mastery


def record_attempt(db: Session, body: AttemptCreate) -> tuple[AttemptResponse, dict | None]:
    """Persist grading and progress atomically; return plain data after commit."""
    # Lock the learner even when no mastery row exists yet. This serializes their
    # submissions and prevents lost updates on both first and subsequent attempts.
    learner = db.scalar(select(Learner).where(Learner.id == body.learner_id).with_for_update())
    if learner is None:
        raise ApplicationError(404, "Learner not found.")
    question = db.get(Question, body.question_id)
    if question is None:
        raise ApplicationError(404, "Question not found.")
    lesson = db.get(Lesson, question.lesson_id)
    if lesson.learner_id != body.learner_id:
        raise ApplicationError(403, "This question belongs to another learner's lesson.")
    previous = select(Attempt).where(
        Attempt.learner_id == body.learner_id, Attempt.question_id == body.question_id
    )
    if db.scalar(previous) is not None:
        raise ApplicationError(409, "This question has already been answered by this learner.")

    correct = body.selected_option_index == question.correct_option_index
    misconception = None if correct else question.misconceptions[str(body.selected_option_index)]
    attempt = Attempt(
        learner_id=body.learner_id, question_id=body.question_id,
        selected_option_index=body.selected_option_index,
        correct=correct, misconception_tag=misconception,
    )
    mastery = db.get(LearnerMastery, (body.learner_id, lesson.concept_id))
    if mastery is None:
        mastery = LearnerMastery(
            learner_id=body.learner_id, concept_id=lesson.concept_id,
            mastery_score=Decimal("0.00"), attempts=0,
        )
        db.add(mastery)
    mastery.mastery_score = calculate_mastery(mastery.mastery_score, correct)
    mastery.attempts += 1
    db.add(attempt)
    concept = db.get(Concept, lesson.concept_id)
    mistake = None if correct else {
        "concept": concept.slug, "question": question.prompt,
        "code_snippet": question.code_snippet,
        "selected_answer": question.options[body.selected_option_index],
        "correct_answer": question.options[question.correct_option_index],
        "misconception": misconception,
    }
    try:
        db.flush()
        response = AttemptResponse(
            id=attempt.id, learner_id=body.learner_id, question_id=body.question_id,
            selected_option_index=body.selected_option_index, correct=correct,
            correct_option_index=question.correct_option_index,
            correct_answer=question.options[question.correct_option_index],
            misconception_tag=misconception,
            mastery_score=float(mastery.mastery_score), concept_attempts=mastery.attempts,
            created_at=attempt.created_at,
        )
        db.commit()
    except IntegrityError as error:
        db.rollback()
        if db.scalar(previous) is not None:
            raise ApplicationError(409, "This question has already been answered by this learner.") from error
        raise
    return response, mistake
