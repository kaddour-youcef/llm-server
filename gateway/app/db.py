from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .config import settings


engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


async def init_db() -> None:
    # Placeholder: migrations are run in container entrypoint via Alembic
    return None


@contextmanager
def get_session() -> Session:
    session: Session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

