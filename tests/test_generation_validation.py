from unittest.mock import Mock

import pytest

from app.errors import ApplicationError
from app.schemas import ConceptResponse
from app.services.generation import generate_lesson_draft
from app.services.validation import validate_lesson
from tests.drafts import valid_lesson


@pytest.mark.parametrize("case", [
    "malformed", "wrong_slug", "question_count", "option_count", "invalid_index",
    "missing_misconception", "correct_option_tagged", "duplicate_misconception",
    "empty_prompt", "empty_option", "empty_explanation",
])
def test_invalid_generated_content_is_rejected(case):
    draft = valid_lesson()
    question = draft["questions"][0]
    if case == "malformed":
        draft = "not JSON"
    elif case == "wrong_slug":
        draft["concept_slug"] = "loops"
    elif case == "question_count":
        draft["questions"].pop()
    elif case == "option_count":
        question["options"].pop()
    elif case == "invalid_index":
        question["correct_option_index"] = 4
    elif case == "missing_misconception":
        question["misconceptions"].pop()
    elif case == "correct_option_tagged":
        question["misconceptions"][0]["option_index"] = 0
    elif case == "duplicate_misconception":
        question["misconceptions"][0]["option_index"] = 2
    elif case == "empty_prompt":
        question["prompt"] = " "
    elif case == "empty_option":
        question["options"][0] = " "
    elif case == "empty_explanation":
        draft["explanation"] = " "
    with pytest.raises(ValueError):
        validate_lesson(draft, "variables")


def test_valid_generated_lesson_succeeds():
    draft = validate_lesson(valid_lesson(), "variables")
    assert draft.concept_slug == "variables"
    assert len(draft.questions) == 3


def test_generation_retries_once_then_succeeds_or_returns_clean_error():
    concept = ConceptResponse(id=1, slug="variables", name="Variables", description="Assignment", prerequisite_ids=[])
    generator = Mock()
    generator.lesson.side_effect = ["invalid", valid_lesson()]
    assert generate_lesson_draft(generator, concept, []).concept_slug == "variables"
    assert generator.lesson.call_count == 2
    generator.reset_mock(side_effect=True)
    generator.lesson.return_value = "invalid"
    with pytest.raises(ApplicationError, match="after two attempts") as error:
        generate_lesson_draft(generator, concept, [])
    assert error.value.status_code == 502
    assert generator.lesson.call_count == 2
