from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.config import get_settings
from app.services.llm import OpenAIGenerator

Database = Annotated[Session, Depends(get_db)]


def get_generator() -> OpenAIGenerator:
    return OpenAIGenerator(get_settings())


Generator = Annotated[OpenAIGenerator, Depends(get_generator)]
