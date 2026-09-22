from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from core.security import create_access_token, hash_password, verify_password
from db import get_session
from deps import get_current_user
from models import User
from schemas import (
    LoginRequest,
    LoginResponse,
    MessageResponse,
    RegisterRequest,
    RegisterResponse,
    UserResponse,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

INVALID_CREDENTIALS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid username or password",
    headers={"WWW-Authenticate": "Bearer"},
)

_DUMMY_HASH = hash_password("dummy-password-for-constant-time-login")


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, session: Session = Depends(get_session)) -> LoginResponse:
    user = session.exec(select(User).where(User.username == request.username)).first()

    if user is None:
        verify_password(request.password, _DUMMY_HASH)
        raise INVALID_CREDENTIALS

    if not verify_password(request.password, user.password_hash):
        raise INVALID_CREDENTIALS

    return LoginResponse(
        id=user.id,
        username=user.username,
        is_admin=user.is_admin,
        access_token=create_access_token(user.id),
    )


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, session: Session = Depends(get_session)) -> User:
    user = User(
        username=request.username,
        password_hash=hash_password(request.password),
        is_admin=False,
    )
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )
    session.refresh(user)
    return user


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.post("/logout", response_model=MessageResponse)
def logout(user: User = Depends(get_current_user)) -> MessageResponse:
    return MessageResponse(message="Logged out, please discard the access token")
