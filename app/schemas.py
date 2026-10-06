from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

NonEmpty = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class LearnerCreate(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
    goal: Literal["Python Fundamentals"] = "Python Fundamentals"


class LearnerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    goal: str
    created_at: datetime


class ConceptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    description: str
    prerequisite_ids: list[int]


class ProgressItem(BaseModel):
    concept: ConceptResponse
    mastery_score: float
    attempts: int
    updated_at: datetime | None


class ProgressResponse(BaseModel):
    learner_id: int
    mastery_threshold: float
    concepts: list[ProgressItem]


class StudyPlan(BaseModel):
    goal: str = "Python Fundamentals"
    completed: bool
    mastered: list[ConceptResponse]
    available_now: list[ConceptResponse]
    locked: list[ConceptResponse]
    recommended_next: ConceptResponse | None


class NextConceptResponse(BaseModel):
    completed: bool
    recommended_next: ConceptResponse | None


class MisconceptionDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    option_index: int = Field(ge=0, le=3, strict=True)
    tag: Annotated[NonEmpty, Field(max_length=200)]


class QuestionDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt: NonEmpty
    code_snippet: str | None
    options: list[NonEmpty] = Field(min_length=4, max_length=4)
    correct_option_index: int = Field(ge=0, le=3, strict=True)
    misconceptions: list[MisconceptionDraft] = Field(min_length=3, max_length=3)


class LessonDraft(BaseModel):
    """Internal generation format: never used as an API response."""
    model_config = ConfigDict(extra="forbid")

    title: Annotated[NonEmpty, Field(max_length=300)]
    concept_slug: NonEmpty
    explanation: Annotated[NonEmpty, Field(max_length=2500)]
    examples: list[NonEmpty] = Field(min_length=1, max_length=3)
    questions: list[QuestionDraft] = Field(min_length=3, max_length=3)


class QuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    prompt: str
    code_snippet: str | None
    options: list[str]


class LessonResponse(BaseModel):
    id: int
    learner_id: int
    concept_slug: str
    title: str
    explanation: str
    examples: list[str]
    questions: list[QuestionResponse]
    created_at: datetime


class AttemptCreate(BaseModel):
    learner_id: int = Field(gt=0, strict=True)
    question_id: int = Field(gt=0, strict=True)
    selected_option_index: int = Field(ge=0, le=3, strict=True)


class Feedback(BaseModel):
    model_config = ConfigDict(extra="forbid")

    explanation: Annotated[NonEmpty, Field(max_length=1200)]
    what_you_misunderstood: Annotated[NonEmpty, Field(max_length=800)]
    how_to_improve: Annotated[NonEmpty, Field(max_length=800)]
    short_example: Annotated[NonEmpty, Field(max_length=800)]


class AttemptResponse(BaseModel):
    id: int
    learner_id: int
    question_id: int
    selected_option_index: int
    correct: bool
    correct_option_index: int
    correct_answer: str
    misconception_tag: str | None
    mastery_score: float
    concept_attempts: int
    created_at: datetime
    feedback: Feedback | None = None
    feedback_source: Literal["llm", "fallback"] | None = None
