import os

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["JWT_SECRET"] = "test_secret_change_me"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import AuditLog, AuthIdentity, OAuthClient, Session, SSOCode, User
from app.models.mixins import utc_now

engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


def reset_db() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def client() -> TestClient:
    reset_db()
    return TestClient(app)


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_register_creates_user_identity_session_and_token():
    c = client()
    response = c.post("/auth/register", json={"email": "test@arvexo.ru", "password": "password12345", "name": "Alexey"})
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == "test@arvexo.ru"
    assert data["user"]["connected_providers"] == ["email"]
    assert data["access_token"]
    assert "arvexo_account_refresh" in c.cookies

    with TestingSessionLocal() as db:
        assert db.query(User).count() == 1
        assert db.query(AuthIdentity).count() == 1
        assert db.query(Session).count() == 1


def test_duplicate_email_rejected():
    c = client()
    payload = {"email": "test@arvexo.ru", "password": "password12345", "name": "Alexey"}
    assert c.post("/auth/register", json=payload).status_code == 200
    response = c.post("/auth/register", json=payload)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EMAIL_ALREADY_EXISTS"


def test_login_success_invalid_password_and_me():
    c = client()
    c.post("/auth/register", json={"email": "test@arvexo.ru", "password": "password12345", "name": "Alexey"})
    bad = c.post("/auth/login", json={"email": "test@arvexo.ru", "password": "wrong"})
    assert bad.status_code == 401
    assert bad.json()["error"]["code"] == "INVALID_CREDENTIALS"

    login = c.post("/auth/login", json={"email": "test@arvexo.ru", "password": "password12345"})
    assert login.status_code == 200
    token = login.json()["access_token"]
    me = c.get("/auth/me", headers=auth_headers(token))
    assert me.status_code == 200
    assert me.json()["email"] == "test@arvexo.ru"


def test_banned_user_cannot_login():
    c = client()
    c.post("/auth/register", json={"email": "test@arvexo.ru", "password": "password12345", "name": "Alexey"})
    with TestingSessionLocal() as db:
        user = db.query(User).filter(User.email == "test@arvexo.ru").one()
        user.is_banned = True
        db.commit()
    response = c.post("/auth/login", json={"email": "test@arvexo.ru", "password": "password12345"})
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "USER_BANNED"


def test_refresh_and_logout():
    c = client()
    c.post("/auth/register", json={"email": "test@arvexo.ru", "password": "password12345", "name": "Alexey"})
    refresh = c.post("/auth/refresh")
    assert refresh.status_code == 200
    assert refresh.json()["access_token"]

    logout = c.post("/auth/logout")
    assert logout.status_code == 200
    assert logout.json()["ok"] is True
    assert "arvexo_account_refresh" not in c.cookies

    expired = c.post("/auth/refresh")
    assert expired.status_code == 401
