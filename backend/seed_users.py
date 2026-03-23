"""
Creates the two demo user accounts needed to log in to the app.

Run this after `docker compose up` before anything else:
    docker compose exec backend python seed_users.py

Credentials:
    admin@databridge.io  /  admin   (admin role)
    demo@databridge.io   /  demo    (viewer role)
"""

from datetime import UTC, datetime

from core.database import SessionLocal
from core.security import hash_password
from models.user import User
from schemas.enums import Role

db = SessionLocal()

for email, password, role in [
    ("admin@databridge.io", "admin", Role.ADMIN),
    ("demo@databridge.io", "demo", Role.VIEWER),
]:
    if not db.query(User).filter_by(email=email).first():
        db.add(
            User(
                email=email,
                hashed_password=hash_password(password),
                role=role,
                created_at=datetime.now(UTC),
            )
        )

db.commit()
db.close()
print("Users seeded: admin@databridge.io / demo@databridge.io")
