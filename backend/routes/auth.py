from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from fastapi.openapi.models import Example
from slowapi import Limiter
from slowapi.util import get_remote_address

from core.container import get_user_repo
from core.security import create_access_token, verify_password
from repositories.interfaces.user import UserRepositoryProtocol
from schemas.user import LoginRequest, TokenResponse

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

_LOGIN_EXAMPLES: dict[str, Example] = {
    "admin": Example(summary="Admin — full access", value={"email": "admin@databridge.io", "password": "admin"}),
    "viewer": Example(summary="Viewer — read-only", value={"email": "demo@databridge.io", "password": "demo"}),
}


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(
    request: Request,
    body: LoginRequest = Body(openapi_examples=_LOGIN_EXAMPLES),
    repo: UserRepositoryProtocol = Depends(get_user_repo),
) -> TokenResponse:
    user = repo.get_by_email(body.email)

    # Deliberately vague error — don't reveal whether the email exists
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    token = create_access_token(subject=user.email, role=user.role)
    return TokenResponse(access_token=token)
