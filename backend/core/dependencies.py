from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import decode_access_token
from models.user import User
from repositories.postgres.user import PostgresUserRepository
from schemas.enums import Role

bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_access_token(credentials.credentials)
        email = payload.get("sub")
        if not isinstance(email, str) or not email:
            raise ValueError
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from None

    user = PostgresUserRepository(db).get_by_email(email)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != Role.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user
