from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from core.database import Base, get_db
from core.dependencies import get_current_user
from main import app
from models.user import User
from schemas.enums import Role

# Postgres schema names the models declare in __table_args__
SCHEMAS = ["customers", "inventory", "sales", "auth", "workers"]

# StaticPool means a single connection is reused for the entire session.
# That way ATTACH DATABASE (below) and CREATE TABLE both run on the same
# connection and are visible to every subsequent query.
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

_FAKE_USER = User(id=1, email="test@example.com", hashed_password="x", role=Role.ADMIN, is_active=True)  # noqa: S106


@event.listens_for(engine, "connect")
def attach_schemas(dbapi_connection: Any, connection_record: Any) -> None:
    """Create a separate in-memory SQLite DB for each Postgres schema."""
    for schema in SCHEMAS:
        dbapi_connection.execute(f"ATTACH DATABASE ':memory:' AS \"{schema}\"")


@pytest.fixture(scope="session", autouse=True)
def setup_database() -> Generator[None, None, None]:
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db() -> Generator[Session, None, None]:
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client(db: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: _FAKE_USER
    yield TestClient(app)
    app.dependency_overrides.clear()
