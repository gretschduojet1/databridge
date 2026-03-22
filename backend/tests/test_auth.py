from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from core.security import hash_password
from models.user import User
from schemas.enums import Role


def _seed_user(db: Session, email: str, password: str, is_active: bool = True) -> User:
    user = User(
        email=email,
        hashed_password=hash_password(password),
        role=Role.VIEWER,
        is_active=is_active,
        created_at=datetime.now(UTC),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_login_success(client: TestClient, db: Session) -> None:
    _seed_user(db, "login@example.com", "correctpassword")
    response = client.post("/auth/login", json={"email": "login@example.com", "password": "correctpassword"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient, db: Session) -> None:
    _seed_user(db, "wrong@example.com", "realpassword")
    response = client.post("/auth/login", json={"email": "wrong@example.com", "password": "wrongpassword"})
    assert response.status_code == 401


def test_login_unknown_email(client: TestClient) -> None:
    response = client.post("/auth/login", json={"email": "nobody@example.com", "password": "anything"})
    assert response.status_code == 401


def test_login_disabled_account(client: TestClient, db: Session) -> None:
    _seed_user(db, "disabled@example.com", "password", is_active=False)
    response = client.post("/auth/login", json={"email": "disabled@example.com", "password": "password"})
    assert response.status_code == 403
