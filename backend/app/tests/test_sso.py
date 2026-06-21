import os

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["JWT_SECRET"] = "test_secret_change_me"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.oauth_client import OAuthClient
from app.models.sso_code import SSOCode

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


def setup_client(db) -> None:
    db.add(
        OAuthClient(
            client_id="arvexo-study",
            client_secret_hash=hash_password("dev_secret"),
            name="Arvexo Study",
            allowed_redirect_uris=["http://localhost:3001/auth/callback"],
            allowed_origins=["http://localhost:3001"],
            is_active=True,
        )
    )
    db.commit()


def make_client() -> TestClient:
    reset_db()
    with TestingSessionLocal() as db:
        setup_client(db)
    return TestClient(app, follow_redirects=False)


def register_and_get_token(c: TestClient) -> str:
    c.post("/auth/register", json={"email": "test@arvexo.ru", "password": "password12345", "name": "Alexey"})
    resp = c.post("/auth/login", json={"email": "test@arvexo.ru", "password": "password12345"})
    return resp.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


REDIRECT_URI = "http://localhost:3001/auth/callback"


def test_sso_start_unauthenticated_redirects_to_login():
    c = make_client()
    resp = c.get(f"/sso/start?client_id=arvexo-study&redirect_uri={REDIRECT_URI}&state=xyz")
    assert resp.status_code == 302
    assert "/login" in resp.headers["location"]


def test_sso_start_authenticated_redirects_to_continue():
    c = make_client()
    register_and_get_token(c)
    resp = c.get(f"/sso/start?client_id=arvexo-study&redirect_uri={REDIRECT_URI}&state=xyz")
    assert resp.status_code == 302
    assert "/sso/continue" in resp.headers["location"]


def test_sso_start_invalid_client():
    c = make_client()
    resp = c.get(f"/sso/start?client_id=unknown&redirect_uri={REDIRECT_URI}")
    assert resp.status_code == 404


def test_sso_start_invalid_redirect_uri():
    c = make_client()
    register_and_get_token(c)
    resp = c.get("/sso/start?client_id=arvexo-study&redirect_uri=http://evil.com/callback")
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "INVALID_REDIRECT_URI"


def test_sso_client_info():
    c = make_client()
    resp = c.get("/sso/client?client_id=arvexo-study")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Arvexo Study"


def test_sso_full_flow():
    c = make_client()
    token = register_and_get_token(c)

    # Confirm → get redirect_url with code
    confirm = c.post(
        "/sso/confirm",
        json={"client_id": "arvexo-study", "redirect_uri": REDIRECT_URI, "state": "xyz"},
        headers=auth_headers(token),
    )
    assert confirm.status_code == 200
    redirect_url = confirm.json()["redirect_url"]
    assert "code=" in redirect_url
    assert "state=xyz" in redirect_url

    # Extract code from redirect_url
    from urllib.parse import parse_qs, urlparse
    parsed = urlparse(redirect_url)
    code = parse_qs(parsed.query)["code"][0]

    # Exchange code
    exchange = c.post(
        "/sso/exchange",
        json={
            "client_id": "arvexo-study",
            "client_secret": "dev_secret",
            "code": code,
            "redirect_uri": REDIRECT_URI,
        },
    )
    assert exchange.status_code == 200
    data = exchange.json()
    assert data["account_user"]["email"] == "test@arvexo.ru"
    assert data["expires_in"] > 0


def test_sso_code_cannot_be_reused():
    c = make_client()
    token = register_and_get_token(c)

    confirm = c.post(
        "/sso/confirm",
        json={"client_id": "arvexo-study", "redirect_uri": REDIRECT_URI},
        headers=auth_headers(token),
    )
    from urllib.parse import parse_qs, urlparse
    parsed = urlparse(confirm.json()["redirect_url"])
    code = parse_qs(parsed.query)["code"][0]

    payload = {"client_id": "arvexo-study", "client_secret": "dev_secret", "code": code, "redirect_uri": REDIRECT_URI}
    assert c.post("/sso/exchange", json=payload).status_code == 200
    assert c.post("/sso/exchange", json=payload).json()["error"]["code"] == "CODE_ALREADY_USED"


def test_sso_wrong_redirect_uri_rejected():
    c = make_client()
    token = register_and_get_token(c)

    confirm = c.post(
        "/sso/confirm",
        json={"client_id": "arvexo-study", "redirect_uri": REDIRECT_URI},
        headers=auth_headers(token),
    )
    from urllib.parse import parse_qs, urlparse
    code = parse_qs(urlparse(confirm.json()["redirect_url"]).query)["code"][0]

    resp = c.post(
        "/sso/exchange",
        json={"client_id": "arvexo-study", "client_secret": "dev_secret", "code": code, "redirect_uri": "http://evil.com/cb"},
    )
    assert resp.json()["error"]["code"] == "REDIRECT_URI_MISMATCH"


def test_sso_wrong_client_secret_rejected():
    c = make_client()
    token = register_and_get_token(c)

    confirm = c.post(
        "/sso/confirm",
        json={"client_id": "arvexo-study", "redirect_uri": REDIRECT_URI},
        headers=auth_headers(token),
    )
    from urllib.parse import parse_qs, urlparse
    code = parse_qs(urlparse(confirm.json()["redirect_url"]).query)["code"][0]

    resp = c.post(
        "/sso/exchange",
        json={"client_id": "arvexo-study", "client_secret": "wrong_secret", "code": code, "redirect_uri": REDIRECT_URI},
    )
    assert resp.json()["error"]["code"] == "INVALID_CLIENT"
