from datetime import UTC, datetime

from sqlalchemy import Index, text
from sqlmodel import Field, SQLModel

BOOKING_ACTIVE = "booked"
BOOKING_CANCELLED = "cancelled"


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    password_hash: str
    is_admin: bool = False


class Booking(SQLModel, table=True):
    __table_args__ = (
        Index(
            "uq_active_slot",
            "slot",
            unique=True,
            sqlite_where=text(f"status = '{BOOKING_ACTIVE}'"),
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    slot: str
    note: str | None = None
    status: str = Field(default=BOOKING_ACTIVE)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
