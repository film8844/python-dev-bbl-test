from fastapi import Depends, HTTPException, Path, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from core.security import decode_access_token
from db import get_session
from models import Booking, User

bearer_scheme = HTTPBearer(auto_error=False)

_UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid or expired access token",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: Session = Depends(get_session),
) -> User:
    if credentials is None:
        raise _UNAUTHORIZED

    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise _UNAUTHORIZED

    user = session.get(User, user_id)
    if user is None:
        raise _UNAUTHORIZED
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return user


def get_owned_booking(
    booking_id: int = Path(..., ge=1),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Booking:
    booking = session.get(Booking, booking_id)
    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )
    if not user.is_admin and booking.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only manage your own bookings",
        )
    return booking
