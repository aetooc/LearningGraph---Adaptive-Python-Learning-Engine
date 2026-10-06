from decimal import Decimal

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic_settings")

from app.models import LearnerMastery
from app.services.planner import load_curriculum


def new_learner(client, name="Alice"):
    response = client.post("/learners", json={"name": name})
    assert response.status_code == 201
    return response.json()["id"]


def generate(client, learner_id):
    response = client.post(f"/learners/{learner_id}/lessons/generate")
    assert response.status_code == 201
    return response.json()


def answer(client, learner_id, question_id, option):
    return client.post("/attempts", json={
        "learner_id": learner_id, "question_id": question_id,
        "selected_option_index": option,
    })


def test_alice_and_bob_vertical_slice_and_answer_key_visibility(client, generator):
    alice, bob = new_learner(client), new_learner(client, "Bob")
    original = client.get(f"/learners/{alice}/study-plan").json()
    assert original["recommended_next"]["slug"] == "variables"
    assert client.get(f"/learners/{bob}/next-concept").json()["recommended_next"]["slug"] == "variables"
    lesson = generate(client, alice)
    assert len(lesson["questions"]) == 3
    for payload in (lesson, client.get(f"/lessons/{lesson['id']}").json()):
        for question in payload["questions"]:
            assert set(question) == {"id", "prompt", "code_snippet", "options"}
    first, second = lesson["questions"][:2]
    correct = answer(client, alice, first["id"], 0)
    assert correct.status_code == 201
    assert correct.json()["correct"] and correct.json()["mastery_score"] == 0.10
    generator.feedback.assert_not_called()
    incorrect = answer(client, alice, second["id"], 2)
    assert incorrect.status_code == 201
    assert incorrect.json()["mastery_score"] == 0.05
    assert incorrect.json()["misconception_tag"] == "assignment_is_none"
    assert incorrect.json()["feedback_source"] == "llm"
    generator.feedback.assert_called_once()
    for question in (first, second):
        assert answer(client, alice, question["id"], 0).status_code == 409
    assert generator.feedback.call_count == 1
    assert client.get(f"/learners/{alice}/study-plan").json()["recommended_next"]["slug"] == "variables"
    progress = client.get(f"/learners/{alice}/progress").json()
    variables = next(item for item in progress["concepts"] if item["concept"]["slug"] == "variables")
    assert variables["mastery_score"] == 0.05

    # Seven additional distinct correct questions: total 8 correct and 1 incorrect.
    seven = 0
    for _ in range(3):
        extra = generate(client, alice)
        assert extra["concept_slug"] == "variables"
        for question in extra["questions"]:
            if seven == 7:
                break
            assert answer(client, alice, question["id"], 0).status_code == 201
            seven += 1
    alice_plan = client.get(f"/learners/{alice}/study-plan").json()
    bob_plan = client.get(f"/learners/{bob}/study-plan").json()
    assert alice_plan["recommended_next"]["slug"] == "data-types"
    assert bob_plan["recommended_next"]["slug"] == "variables"
    progress = client.get(f"/learners/{alice}/progress").json()
    variables = next(item for item in progress["concepts"] if item["concept"]["slug"] == "variables")
    assert variables["mastery_score"] == 0.75 and variables["attempts"] == 9


def test_completed_curriculum_never_calls_generation(client, db, generator):
    learner_id = new_learner(client)
    for concept in load_curriculum(db):
        db.add(LearnerMastery(learner_id=learner_id, concept_id=concept.id, mastery_score=Decimal("0.70"), attempts=7))
    db.commit()
    assert client.get(f"/learners/{learner_id}/study-plan").json()["completed"]
    assert client.get(f"/learners/{learner_id}/next-concept").json() == {"completed": True, "recommended_next": None}
    assert client.post(f"/learners/{learner_id}/lessons/generate").status_code == 409
    generator.lesson.assert_not_called()


def test_feedback_failure_returns_saved_attempt_and_duplicate_does_not_retry(client, generator):
    learner_id = new_learner(client)
    question = generate(client, learner_id)["questions"][0]
    generator.feedback.side_effect = RuntimeError("provider failure")
    response = answer(client, learner_id, question["id"], 2)
    assert response.status_code == 201 and response.json()["feedback_source"] == "fallback"
    assert response.json()["concept_attempts"] == 1
    assert answer(client, learner_id, question["id"], 0).status_code == 409
    generator.feedback.assert_called_once()


def test_invalid_generation_does_not_persist_a_lesson(client, db, generator):
    from sqlalchemy import func, select
    from app.models import Lesson

    learner_id = new_learner(client)
    generator.lesson.side_effect = None
    generator.lesson.return_value = {"concept_slug": "wrong"}
    response = client.post(f"/learners/{learner_id}/lessons/generate")
    assert response.status_code == 502
    assert generator.lesson.call_count == 2
    assert db.scalar(select(func.count()).select_from(Lesson)) == 0


def test_api_errors_and_request_validation(client, generator):
    assert client.get("/learners/999").status_code == 404
    assert client.get("/learners/999/study-plan").status_code == 404
    assert client.post("/learners/999/lessons/generate").status_code == 404
    assert client.get("/concepts/999").status_code == 404
    assert client.get("/lessons/999").status_code == 404
    assert client.post("/learners", json={"name": " "}).status_code == 422
    assert client.post("/learners", json={"name": "Alice", "goal": "Other"}).status_code == 422
    assert client.post("/attempts", json={"learner_id": 1, "question_id": 1, "selected_option_index": 4}).status_code == 422
    generator.lesson.assert_not_called()


def test_learner_selector_lists_existing_learners(client):
    assert client.get("/learners").json() == []
    alice = new_learner(client)
    bob = new_learner(client, "Bob")
    response = client.get("/learners")
    assert response.status_code == 200
    assert [(item["id"], item["name"]) for item in response.json()] == [(alice, "Alice"), (bob, "Bob")]
