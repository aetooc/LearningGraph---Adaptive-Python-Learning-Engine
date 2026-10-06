from decimal import Decimal

from fastapi import APIRouter

from app.api.dependencies import Database, Generator
from app.config import get_settings
from app.errors import ApplicationError
from app.models import Concept, Lesson, Question
from app.schemas import LessonResponse, QuestionResponse
from app.services.generation import generate_lesson_draft
from app.services.planner import get_next_concept, load_learning_state

router = APIRouter(tags=["lessons"])


def lesson_response(lesson: Lesson, concept_slug: str) -> LessonResponse:
    return LessonResponse(
        id=lesson.id, learner_id=lesson.learner_id, concept_slug=concept_slug,
        title=lesson.title, explanation=lesson.explanation, examples=lesson.examples,
        questions=[QuestionResponse.model_validate(question) for question in lesson.questions],
        created_at=lesson.created_at,
    )


@router.post("/learners/{learner_id}/lessons/generate", response_model=LessonResponse, status_code=201)
def generate_lesson(learner_id: int, db: Database, generator: Generator):
    concepts, mastery = load_learning_state(db, learner_id)
    concept = get_next_concept(
        concepts, {key: row.mastery_score for key, row in mastery.items()},
        Decimal(str(get_settings().mastery_threshold)),
    )
    if concept is None:
        raise ApplicationError(409, "Curriculum is complete; no lesson remains to generate.")
    # End the read transaction before waiting for external generation.
    db.rollback()
    required = [item for item in concepts if item.id in concept.prerequisite_ids]
    draft = generate_lesson_draft(generator, concept, required)
    lesson = Lesson(
        learner_id=learner_id, concept_id=concept.id, title=draft.title,
        explanation=draft.explanation, examples=draft.examples,
        questions=[
            Question(
                position=position, prompt=question.prompt, code_snippet=question.code_snippet,
                options=question.options, correct_option_index=question.correct_option_index,
                misconceptions={str(item.option_index): item.tag for item in question.misconceptions},
            )
            for position, question in enumerate(draft.questions)
        ],
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson_response(lesson, concept.slug)


@router.get("/lessons/{lesson_id}", response_model=LessonResponse)
def get_lesson(lesson_id: int, db: Database):
    lesson = db.get(Lesson, lesson_id)
    if lesson is None:
        raise ApplicationError(404, "Lesson not found.")
    concept = db.get(Concept, lesson.concept_id)
    return lesson_response(lesson, concept.slug)
