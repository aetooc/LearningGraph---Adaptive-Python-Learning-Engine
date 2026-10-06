from functools import lru_cache
from typing import Iterator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session

class Base(DeclarativeBase):
    pass


@lru_cache
def get_engine() -> Engine:
    from app.config import get_settings

    return create_engine(get_settings().database_url, pool_pre_ping=True)


def get_db() -> Iterator[Session]:
    with Session(get_engine()) as session:
        yield session
