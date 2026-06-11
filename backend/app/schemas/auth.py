from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str | None = Field(default=None, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserRead(BaseModel):
    id: UUID
    email: str | None
    name: str | None
    last_name: str | None = None
    phone: str | None = None
    avatar_url: str | None = None
    role: str
    connected_providers: list[str] = []
    created_at: datetime


class AuthResponse(BaseModel):
    user: UserRead
    access_token: str


class RefreshResponse(BaseModel):
    access_token: str


class OAuthStatusResponse(BaseModel):
    google: bool
    yandex: bool
    telegram: bool
