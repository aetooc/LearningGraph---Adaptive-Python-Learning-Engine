import logging
from typing import Literal

from pydantic import BaseModel

from app.schemas import Feedback
from app.services.llm import OpenAIGenerator

logger = logging.getLogger(__name__)


def feedback_for_mistake(
    generator: OpenAIGenerator, mistake: dict
) -> tuple[Feedback, Literal["llm", "fallback"]]:
    try:
        raw = generator.feedback(mistake)
        if isinstance(raw, BaseModel):
            raw = raw.model_dump()
        feedback = Feedback.model_validate_json(raw) if isinstance(raw, str) else Feedback.model_validate(raw)
        return feedback, "llm"
    except Exception:
        # The attempt is already committed; any provider/parsing failure must
        # leave the learner with a usable response, without asking for resubmission.
        logger.warning("Feedback generation failed; returning fallback feedback.")
        return Feedback(
            explanation=f"The stored correct answer is: {mistake['correct_answer']}"[:1200],
            what_you_misunderstood=f"Your choice was associated with: {mistake['misconception'].replace('_', ' ')}"[:800],
            how_to_improve="Review the lesson examples, compare each option, and try a new question.",
            short_example=((mistake.get("code_snippet") or "").strip() or mistake["correct_answer"])[:800],
        ), "fallback"
