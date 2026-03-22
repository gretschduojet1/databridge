from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from core.config import settings

# The engine manages the connection pool to Postgres.
# pool_pre_ping=True checks if a connection is alive before using it —
# important in Docker where the DB container might restart independently.
engine = create_engine(settings.database_url, pool_pre_ping=True)

# SessionLocal is a factory — calling SessionLocal() gives you a new session.
# A session is a unit of work: it tracks all queries and changes for one request,
# then either commits them all or rolls them all back.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """
    All ORM models inherit from this single Base.
    SQLAlchemy uses it to track which classes map to which tables.
    """
    pass


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a DB session scoped to one HTTP request.

    The `yield` makes this a generator — FastAPI runs the setup, injects the
    session into the route function, then runs the `finally` block after the
    response is sent. The session is always closed, even if an exception occurs.

    Swap this function out in tests to use a test database instead.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
