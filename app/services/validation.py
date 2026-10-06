from pydantic import BaseModel

from app.schemas import LessonDraft


def validate_lesson(raw: dict | str | BaseModel, expected_slug: str) -> LessonDraft:
    if isinstance(raw, BaseModel):
        raw = raw.model_dump()
    draft = LessonDraft.model_validate_json(raw) if isinstance(raw, str) else LessonDraft.model_validate(raw)
    if draft.concept_slug != expected_slug:
        raise ValueError("Generated lesson does not match the requested concept.")
    for question in draft.questions:
        indices = [item.option_index for item in question.misconceptions]
        expected = set(range(4)) - {question.correct_option_index}
        if len(set(indices)) != len(indices) or set(indices) != expected:
            raise ValueError("Exactly the three incorrect options need misconception tags.")
        if len(set(question.options)) != 4:
            raise ValueError("Question options must be distinct.")
    return draft
