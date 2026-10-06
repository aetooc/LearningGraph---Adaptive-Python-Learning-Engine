from app.errors import ApplicationError
from app.schemas import ConceptResponse, LessonDraft
from app.services.llm import OpenAIGenerator
from app.services.validation import validate_lesson


def generate_lesson_draft(
    generator: OpenAIGenerator, concept: ConceptResponse,
    prerequisites: list[ConceptResponse],
) -> LessonDraft:
    context = {
        "concept_slug": concept.slug,
        "concept": concept.name,
        "description": concept.description,
        "learner_level": "beginner",
        "desired_difficulty": "introductory",
        "prerequisites": [item.name for item in prerequisites],
    }
    for attempt in range(2):
        try:
            raw = generator.lesson(context)
            return validate_lesson(raw, concept.slug)
        except ValueError:
            if attempt == 0:
                context["validation_hint"] = "Previous output was invalid; check schema, concept slug, and misconception indices."
    raise ApplicationError(502, "Generated lesson failed validation after two attempts.")
