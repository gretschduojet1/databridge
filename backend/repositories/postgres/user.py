from sqlalchemy.orm import Session

from models.user import User


class PostgresUserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email).first()

    def get_by_id(self, id: int) -> User | None:
        return self.db.query(User).filter(User.id == id).first()
