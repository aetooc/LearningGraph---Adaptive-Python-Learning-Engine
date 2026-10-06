from fastapi import APIRouter

from app.api.dependencies import Database
from app.errors import ApplicationError
from app.schemas import ConceptResponse
from app.services.planner import load_curriculum

router = APIRouter(prefix="/concepts", tags=["curriculum"])


@router.get("", response_model=list[ConceptResponse])
def list_concepts(db: Database):
    return load_curriculum(db)


@router.get("/{concept_id}", response_model=ConceptResponse)
def get_concept(concept_id: int, db: Database):
    for concept in load_curriculum(db):
        if concept.id == concept_id:
            return concept
    raise ApplicationError(404, "Concept not found.")
