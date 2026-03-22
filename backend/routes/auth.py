from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from core.database import get_db
from core.security import verify_password, create_access_token
from repositories.postgres.user import PostgresUserRepository
from schemas.user import LoginRequest, TokenResponse

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(request: Request, body: LoginRequest, db: Session = Depends(get_db)):
    repo = PostgresUserRepository(db)
    user = repo.get_by_email(body.email)

    # Deliberately vague error — don't reveal whether the email exists
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    token = create_access_token(subject=user.email, role=user.role)
    return TokenResponse(access_token=token)
