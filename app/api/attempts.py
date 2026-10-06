from fastapi import APIRouter

from app.api.dependencies import Database, Generator
from app.schemas import AttemptCreate, AttemptResponse
from app.services.attempts import record_attempt
from app.services.feedback import feedback_for_mistake

router = APIRouter(prefix="/attempts", tags=["attempts"])


@router.post("", response_model=AttemptResponse, status_code=201)
def submit_attempt(body: AttemptCreate, db: Database, generator: Generator):
    response, mistake = record_attempt(db, body)
    if mistake is not None:
        response.feedback, response.feedback_source = feedback_for_mistake(generator, mistake)
    return response
