"""Local developer demonstration; reads private answer keys to choose test answers."""
import argparse

import httpx
from sqlalchemy.orm import Session

from app.db.database import get_engine
from app.models import Question


def run_demo(base_url: str) -> None:
    with httpx.Client(base_url=base_url, timeout=90) as client:
        def request(method: str, path: str, body: dict | None = None, expected: int = 200):
            response = client.request(method, path, json=body)
            if response.status_code != expected:
                raise RuntimeError(f"{method} {path}: {response.status_code} {response.text}")
            print(f"{method} {path} -> {response.status_code}")
            return response.json()

        def plan(learner_id: int):
            return request("GET", f"/learners/{learner_id}/study-plan")

        def lesson(learner_id: int):
            result = request("POST", f"/learners/{learner_id}/lessons/generate", expected=201)
            assert result["concept_slug"] == "variables"
            return result

        def submit(learner_id: int, question_id: int, correct: bool, expected=201):
            # Developer-only DB inspection. Learner-facing endpoints never reveal
            # these keys until after submission. No generated code is executed.
            with Session(get_engine()) as db:
                stored = db.get(Question, question_id)
                if stored is None:
                    raise RuntimeError("Demo DATABASE_URL must point to the API's database.")
                index = stored.correct_option_index
            selected = index if correct else (index + 1) % 4
            result = request("POST", "/attempts", {
                "learner_id": learner_id, "question_id": question_id,
                "selected_option_index": selected,
            }, expected=expected)
            if expected == 201:
                assert result["correct"] is correct
                print(f"  correct={result['correct']}, mastery={result['mastery_score']:.2f}")
            return result

        alice = request("POST", "/learners", {"name": "Alice"}, 201)["id"]
        bob = request("POST", "/learners", {"name": "Bob"}, 201)["id"]
        assert plan(alice)["recommended_next"]["slug"] == "variables"
        assert plan(bob)["recommended_next"]["slug"] == "variables"
        first_lesson = lesson(alice)
        first, second, third = first_lesson["questions"]
        assert submit(alice, first["id"], True)["mastery_score"] == 0.10
        incorrect = submit(alice, second["id"], False)
        assert incorrect["mastery_score"] == 0.05
        assert incorrect["misconception_tag"] and incorrect["feedback"]
        print(f"  feedback ({incorrect['feedback_source']}): {incorrect['feedback']['explanation']}")
        submit(alice, first["id"], True, 409)
        submit(alice, second["id"], False, 409)
        assert plan(alice)["recommended_next"]["slug"] == "variables"
        pending = [third]
        for _ in range(7):
            if not pending:
                pending = lesson(alice)["questions"]
            result = submit(alice, pending.pop(0)["id"], True)
        assert result["mastery_score"] == 0.75
        assert result["concept_attempts"] == 9
        assert plan(alice)["recommended_next"]["slug"] == "data-types"
        assert plan(bob)["recommended_next"]["slug"] == "variables"
        print("Alice: 0.75 -> data-types. Bob: 0.00 -> variables.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://localhost:8000")
    run_demo(parser.parse_args().base_url)
