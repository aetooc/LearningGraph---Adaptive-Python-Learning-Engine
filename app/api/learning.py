from decimal import Decimal

from fastapi import APIRouter

from app.api.dependencies import Database
from app.config import get_settings
from app.schemas import NextConceptResponse, ProgressItem, ProgressResponse, StudyPlan
from app.services.planner import build_study_plan, load_learning_state

router = APIRouter(prefix="/learners", tags=["learning"])


# Show mastered, ready, and locked topics, plus what the learner should study next.
@router.get("/{learner_id}/study-plan", response_model=StudyPlan)
def study_plan(learner_id: int, db: Database):
    concepts, mastery = load_learning_state(db, learner_id)
    return build_study_plan(
        concepts, {key: row.mastery_score for key, row in mastery.items()},
        Decimal(str(get_settings().mastery_threshold)),
    )


# Show the next topic to study and whether the learner has mastered all topics.
@router.get("/{learner_id}/next-concept", response_model=NextConceptResponse)
def next_concept(learner_id: int, db: Database):
    plan = study_plan(learner_id, db)
    return NextConceptResponse(completed=plan.completed, recommended_next=plan.recommended_next)


# Show the learner's score, number of attempts, and last update for every topic.
@router.get("/{learner_id}/progress", response_model=ProgressResponse)
def progress(learner_id: int, db: Database):
    concepts, mastery = load_learning_state(db, learner_id)
    return ProgressResponse(
        learner_id=learner_id, mastery_threshold=get_settings().mastery_threshold,
        concepts=[
            ProgressItem(
                concept=concept,
                mastery_score=float(mastery[concept.id].mastery_score) if concept.id in mastery else 0.0,
                attempts=mastery[concept.id].attempts if concept.id in mastery else 0,
                updated_at=mastery[concept.id].updated_at if concept.id in mastery else None,
            )
            for concept in concepts
        ],
    )
