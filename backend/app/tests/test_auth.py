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


def register_and_login(c: TestClient, email: str = "test@arvexo.ru", password: str = "password12345") -> str:
    c.post("/auth/register", json={"email": email, "password": password, "name": "Alexey"})
    resp = c.post("/auth/login", json={"email": email, "password": password})
    return resp.json()["access_token"]


# ── Auth ────────────────────────────────────────


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


# ── Account / identities ────────────────────────


def test_list_identities():
    c = client()
    token = register_and_login(c)
    resp = c.get("/account/identities", headers=auth_headers(token))
    assert resp.status_code == 200
    identities = resp.json()
    assert len(identities) == 1
    assert identities[0]["provider"] == "email"


def test_cannot_disconnect_last_identity():
    c = client()
    token = register_and_login(c)
    resp = c.delete("/account/identities/email", headers=auth_headers(token))
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "LAST_IDENTITY"


def test_disconnect_nonexistent_identity():
    c = client()
    token = register_and_login(c)
    resp = c.delete("/account/identities/telegram", headers=auth_headers(token))
    assert resp.status_code == 404


def test_update_profile():
    c = client()
    token = register_and_login(c)
    resp = c.patch(
        "/account/profile",
        json={"name": "Новое имя", "last_name": "Фамилия"},
        headers=auth_headers(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Новое имя"
    assert data["last_name"] == "Фамилия"


def test_change_password():
    c = client()
    token = register_and_login(c)
    resp = c.post(
        "/account/password",
        json={"current_password": "password12345", "new_password": "newpassword99"},
        headers=auth_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    # old password no longer works
    bad = c.post("/auth/login", json={"email": "test@arvexo.ru", "password": "password12345"})
    assert bad.status_code == 401
    # new password works
    good = c.post("/auth/login", json={"email": "test@arvexo.ru", "password": "newpassword99"})
    assert good.status_code == 200


def test_change_password_wrong_current():
    c = client()
    token = register_and_login(c)
    resp = c.post(
        "/account/password",
        json={"current_password": "wrongpassword", "new_password": "newpassword99"},
        headers=auth_headers(token),
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "INVALID_CURRENT_PASSWORD"


# ── Sessions ────────────────────────────────────


def test_list_sessions():
    c = client()
    token = register_and_login(c)
    resp = c.get("/sessions", headers=auth_headers(token))
    assert resp.status_code == 200
    sessions = resp.json()
    assert len(sessions) >= 1


def test_revoke_session():
    c = client()
    token = register_and_login(c)
    sessions = c.get("/sessions", headers=auth_headers(token)).json()
    # find non-current session (login created a 2nd session, register created 1st)
    non_current = [s for s in sessions if not s["current"]]
    if non_current:
        session_id = non_current[0]["id"]
        resp = c.delete(f"/sessions/{session_id}", headers=auth_headers(token))
        assert resp.status_code == 200
        assert resp.json()["ok"] is True


def test_revoke_nonexistent_session():
    c = client()
    token = register_and_login(c)
    resp = c.delete("/sessions/00000000-0000-0000-0000-000000000000", headers=auth_headers(token))
    assert resp.status_code == 404


# ── Delete account ──────────────────────────────


def test_delete_account():
    c = client()
    token = register_and_login(c)
    resp = c.delete("/auth/me", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    with TestingSessionLocal() as db:
        assert db.query(User).count() == 0
        assert db.query(AuthIdentity).count() == 0
        assert db.query(Session).count() == 0
