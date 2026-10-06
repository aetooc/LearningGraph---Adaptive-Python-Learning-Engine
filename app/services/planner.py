from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import ApplicationError
from app.graph import topological_order
from app.models import Concept, Learner, LearnerMastery, Prerequisite
from app.schemas import ConceptResponse, StudyPlan


def load_curriculum(db: Session) -> list[ConceptResponse]:
    required: dict[int, list[int]] = {}
    for edge in db.scalars(select(Prerequisite)):
        required.setdefault(edge.concept_id, []).append(edge.prerequisite_id)
    return [
        ConceptResponse(
            id=concept.id, slug=concept.slug, name=concept.name,
            description=concept.description,
            prerequisite_ids=sorted(required.get(concept.id, [])),
        )
        for concept in db.scalars(select(Concept).order_by(Concept.slug))
    ]


def load_learning_state(
    db: Session, learner_id: int
) -> tuple[list[ConceptResponse], dict[int, LearnerMastery]]:
    if db.get(Learner, learner_id) is None:
        raise ApplicationError(404, "Learner not found.")
    concepts = load_curriculum(db)
    if not concepts:
        raise ApplicationError(503, "Curriculum is empty. Run the seed script first.")
    mastery = {
        row.concept_id: row
        for row in db.scalars(select(LearnerMastery).where(LearnerMastery.learner_id == learner_id))
    }
    return concepts, mastery


def ordered_concepts(concepts: list[ConceptResponse]) -> list[ConceptResponse]:
    by_id = {concept.id: concept for concept in concepts}
    ordered_ids = topological_order(
        {concept.id: concept.slug for concept in concepts},
        {concept.id: set(concept.prerequisite_ids) for concept in concepts},
    )
    return [by_id[concept_id] for concept_id in ordered_ids]


def get_eligible_concepts(
    concepts: list[ConceptResponse], scores: dict[int, Decimal], threshold: Decimal
) -> list[ConceptResponse]:
    return [
        concept for concept in ordered_concepts(concepts)
        if scores.get(concept.id, Decimal("0")) < threshold
        and all(scores.get(required, Decimal("0")) >= threshold for required in concept.prerequisite_ids)
    ]


def get_next_concept(
    concepts: list[ConceptResponse], scores: dict[int, Decimal], threshold: Decimal
) -> ConceptResponse | None:
    eligible = get_eligible_concepts(concepts, scores, threshold)
    return eligible[0] if eligible else None


def build_study_plan(
    concepts: list[ConceptResponse], scores: dict[int, Decimal], threshold: Decimal
) -> StudyPlan:
    ordered = ordered_concepts(concepts)
    mastered = [concept for concept in ordered if scores.get(concept.id, Decimal("0")) >= threshold]
    available = get_eligible_concepts(concepts, scores, threshold)
    included = {concept.id for concept in mastered + available}
    return StudyPlan(
        completed=len(mastered) == len(ordered),
        mastered=mastered,
        available_now=available,
        locked=[concept for concept in ordered if concept.id not in included],
        recommended_next=available[0] if available else None,
    )
