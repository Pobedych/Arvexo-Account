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


class UpdateProfileRequest(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    last_name: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=40)
    avatar_url: str | None = Field(default=None, max_length=2048)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class IdentityRead(BaseModel):
    provider: str
    provider_email: str | None
    created_at: datetime


class SessionRead(BaseModel):
    id: UUID
    user_agent: str | None
    ip_address: str | None
    created_at: datetime
    expires_at: datetime
    current: bool


# ── SSO ──────────────────────────────────────────

class SSOClientInfo(BaseModel):
    client_id: str
    name: str


class SSOConfirmRequest(BaseModel):
    client_id: str
    redirect_uri: str
    state: str | None = None
    scope: str | None = None


class SSOConfirmResponse(BaseModel):
    redirect_url: str


class SSOExchangeRequest(BaseModel):
    client_id: str
    client_secret: str
    code: str
    redirect_uri: str


class SSOUserPublic(BaseModel):
    id: UUID
    email: str | None
    name: str | None
    avatar_url: str | None


class SSOExchangeResponse(BaseModel):
    account_user: SSOUserPublic
    expires_in: int
