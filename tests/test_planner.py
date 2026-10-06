from decimal import Decimal

from app.schemas import ConceptResponse
from app.services.planner import build_study_plan, get_eligible_concepts, get_next_concept

THRESHOLD = Decimal("0.70")


def concept(concept_id, slug, required=()):
    return ConceptResponse(id=concept_id, slug=slug, name=slug, description=slug, prerequisite_ids=list(required))


def test_root_is_available_and_unmet_prerequisites_are_locked():
    concepts = [concept(1, "variables"), concept(2, "loops", (1,))]
    plan = build_study_plan(concepts, {}, THRESHOLD)
    assert [c.slug for c in plan.available_now] == ["variables"]
    assert [c.slug for c in plan.locked] == ["loops"]
    assert plan.recommended_next.slug == "variables"
    assert not plan.completed


def test_all_prerequisites_must_reach_threshold():
    concepts = [concept(1, "a"), concept(2, "b"), concept(3, "c", (1, 2))]
    scores = {1: Decimal("0.70"), 2: Decimal("0.69")}
    assert [c.id for c in get_eligible_concepts(concepts, scores, THRESHOLD)] == [2]
    scores[2] = Decimal("0.70")
    assert [c.id for c in get_eligible_concepts(concepts, scores, THRESHOLD)] == [3]


def test_topological_ties_use_slug_and_input_order_does_not_matter():
    concepts = [concept(1, "z"), concept(2, "b"), concept(3, "a", (2,))]
    for order in (concepts, list(reversed(concepts))):
        assert [c.slug for c in get_eligible_concepts(order, {}, THRESHOLD)] == ["b", "z"]
        assert get_next_concept(order, {}, THRESHOLD).slug == "b"
        plan = build_study_plan(order, {2: THRESHOLD}, THRESHOLD)
        assert [c.slug for c in plan.available_now] == ["a", "z"]
        assert plan.recommended_next.slug == "a"


def test_mastered_roots_are_excluded_and_completion_has_no_recommendation():
    concepts = [concept(1, "variables"), concept(2, "loops", (1,))]
    assert get_next_concept(concepts, {1: THRESHOLD}, THRESHOLD).id == 2
    scores = {1: THRESHOLD, 2: THRESHOLD}
    plan = build_study_plan(concepts, scores, THRESHOLD)
    assert plan.completed
    assert plan.recommended_next is None
    assert plan.available_now == plan.locked == []
    assert get_next_concept(concepts, scores, THRESHOLD) is None


def test_recorded_attempts_give_alice_and_bob_different_recommendations(db, lesson):
    from app.models import Learner, Question
    from app.schemas import AttemptCreate
    from app.services.attempts import record_attempt
    from app.services.planner import load_learning_state

    bob = Learner(name="Bob")
    db.add(bob)
    # Two additional three-question practice sets are sufficient for this history.
    from app.models import Lesson
    additional_questions = []
    for _ in range(2):
        extra = Lesson(
            learner_id=lesson.learner_id, concept_id=lesson.concept_id,
            title=lesson.title, explanation=lesson.explanation, examples=lesson.examples,
            questions=[
                Question(position=index, prompt="What does x = 1 assign?", options=["1", "0", "None", "Error"],
                         correct_option_index=0, misconceptions={"1": "zero", "2": "none", "3": "error"})
                for index in range(3)
            ],
        )
        db.add(extra)
        db.flush()
        additional_questions.extend(extra.questions)
    db.commit()
    questions = lesson.questions + additional_questions
    for index, question in enumerate(questions):
        result, _ = record_attempt(db, AttemptCreate(
            learner_id=lesson.learner_id, question_id=question.id,
            selected_option_index=1 if index == 1 else 0,
        ))
    assert result.mastery_score == 0.75 and result.concept_attempts == 9
    concepts, alice_mastery = load_learning_state(db, lesson.learner_id)
    _, bob_mastery = load_learning_state(db, bob.id)
    alice = get_next_concept(concepts, {key: row.mastery_score for key, row in alice_mastery.items()}, THRESHOLD)
    bob_next = get_next_concept(concepts, {key: row.mastery_score for key, row in bob_mastery.items()}, THRESHOLD)
    assert alice.slug == "data-types"
    assert bob_next.slug == "variables"
