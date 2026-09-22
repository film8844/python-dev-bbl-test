from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from core.config import AVAILABLE_SLOTS
from db import get_session
from deps import get_current_user, get_owned_booking, require_admin
from models import BOOKING_ACTIVE, BOOKING_CANCELLED, Booking, User
from schemas import BookingRequest, BookingResponse, BookingUpdateRequest, SlotResponse

router = APIRouter(prefix="/api/booking", tags=["Booking Management"])


def _to_response(booking: Booking, username: str) -> BookingResponse:
    return BookingResponse(
        id=booking.id,
        user_id=booking.user_id,
        username=username,
        slot=booking.slot,
        note=booking.note,
        status=booking.status,
        created_at=booking.created_at,
    )


def _username_of(session: Session, user_id: int) -> str:
    user = session.get(User, user_id)
    return user.username if user else ""


def _validate_slot(slot: str) -> None:
    if slot not in AVAILABLE_SLOTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid slot. Available slots: {', '.join(AVAILABLE_SLOTS)}",
        )


def _commit_or_conflict(session: Session) -> None:
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This time slot is already booked",
        )


@router.get("/slots", response_model=list[SlotResponse])
def list_slots(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[SlotResponse]:
    taken = set(
        session.exec(select(Booking.slot).where(Booking.status == BOOKING_ACTIVE)).all()
    )
    return [SlotResponse(slot=slot, available=slot not in taken) for slot in AVAILABLE_SLOTS]


@router.get("/", response_model=list[BookingResponse])
def list_bookings(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    username: str | None = Query(default=None),
) -> list[BookingResponse]:
    statement = select(Booking, User).join(User, User.id == Booking.user_id)

    if user.is_admin:
        if username:
            statement = statement.where(User.username == username)
    else:
        statement = statement.where(Booking.user_id == user.id)

    rows = session.exec(statement.order_by(Booking.id)).all()
    return [_to_response(booking, owner.username) for booking, owner in rows]


@router.get("/all", response_model=list[BookingResponse], dependencies=[Depends(require_admin)])
def list_all_bookings(session: Session = Depends(get_session)) -> list[BookingResponse]:
    rows = session.exec(
        select(Booking, User).join(User, User.id == Booking.user_id).order_by(Booking.id)
    ).all()
    return [_to_response(booking, owner.username) for booking, owner in rows]


@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def create_booking(
    request: BookingRequest,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> BookingResponse:
    _validate_slot(request.slot)

    booking = Booking(user_id=user.id, slot=request.slot, note=request.note)
    session.add(booking)
    _commit_or_conflict(session)
    session.refresh(booking)
    return _to_response(booking, user.username)


@router.get("/{booking_id}", response_model=BookingResponse)
def get_booking(
    booking: Booking = Depends(get_owned_booking),
    session: Session = Depends(get_session),
) -> BookingResponse:
    return _to_response(booking, _username_of(session, booking.user_id))


@router.patch("/{booking_id}", response_model=BookingResponse)
def update_booking(
    request: BookingUpdateRequest,
    booking: Booking = Depends(get_owned_booking),
    session: Session = Depends(get_session),
) -> BookingResponse:
    if booking.status != BOOKING_ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot update a cancelled booking",
        )

    if request.slot is not None:
        _validate_slot(request.slot)
        booking.slot = request.slot
    if request.note is not None:
        booking.note = request.note

    session.add(booking)
    _commit_or_conflict(session)
    session.refresh(booking)
    return _to_response(booking, _username_of(session, booking.user_id))


@router.delete("/{booking_id}", response_model=BookingResponse)
def cancel_booking(
    booking: Booking = Depends(get_owned_booking),
    session: Session = Depends(get_session),
) -> BookingResponse:
    booking.status = BOOKING_CANCELLED
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return _to_response(booking, _username_of(session, booking.user_id))
