from datetime import datetime

from pydantic import BaseModel, Field

from core.security import MAX_PASSWORD_BYTES


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=MAX_PASSWORD_BYTES)


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=MAX_PASSWORD_BYTES)


class BookingRequest(BaseModel):
    slot: str = Field(min_length=1, max_length=50)
    note: str | None = Field(default=None, max_length=500)


class BookingUpdateRequest(BaseModel):
    slot: str | None = Field(default=None, min_length=1, max_length=50)
    note: str | None = Field(default=None, max_length=500)


class UserResponse(BaseModel):
    id: int
    username: str
    is_admin: bool


class RegisterResponse(UserResponse):
    pass


class LoginResponse(UserResponse):
    access_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    message: str


class BookingResponse(BaseModel):
    id: int
    user_id: int
    username: str
    slot: str
    note: str | None
    status: str
    created_at: datetime


class SlotResponse(BaseModel):
    slot: str
    available: bool
