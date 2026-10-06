from fastapi import APIRouter
from sqlalchemy import select

from app.api.dependencies import Database
from app.errors import ApplicationError
from app.models import Learner
from app.schemas import LearnerCreate, LearnerResponse

router = APIRouter(prefix="/learners", tags=["learners"])


@router.get("", response_model=list[LearnerResponse])
def list_learners(db: Database):
    return list(db.scalars(select(Learner).order_by(Learner.id)))


@router.post("", response_model=LearnerResponse, status_code=201)
def create_learner(body: LearnerCreate, db: Database):
    learner = Learner(name=body.name, goal=body.goal)
    db.add(learner)
    db.commit()
    db.refresh(learner)
    return learner


@router.get("/{learner_id}", response_model=LearnerResponse)
def get_learner(learner_id: int, db: Database):
    learner = db.get(Learner, learner_id)
    if learner is None:
        raise ApplicationError(404, "Learner not found.")
    return learner
