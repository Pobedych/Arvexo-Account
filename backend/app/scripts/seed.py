from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.auth_identity import AuthIdentity
from app.models.oauth_client import OAuthClient
from app.models.user import User


def seed(db: Session) -> None:
    user = db.query(User).filter(User.email == "test@arvexo.ru").one_or_none()
    if not user:
        user = User(email="test@arvexo.ru", password_hash=hash_password("password12345"), name="Test", role="user")
        db.add(user)
        db.flush()
        db.add(AuthIdentity(user_id=user.id, provider="email", provider_user_id="test@arvexo.ru", provider_email="test@arvexo.ru"))

    if settings.seed_arvexo_study_client:
        client = db.query(OAuthClient).filter(OAuthClient.client_id == settings.arvexo_study_client_id).one_or_none()
        if not client:
            db.add(
                OAuthClient(
                    client_id=settings.arvexo_study_client_id,
                    client_secret_hash=hash_password(settings.arvexo_study_client_secret),
                    name="Arvexo Study",
                    allowed_redirect_uris=[settings.arvexo_study_redirect_uri],
                    allowed_origins=["http://localhost:3001"],
                    is_active=True,
                )
            )
    db.commit()


def main() -> None:
    with SessionLocal() as db:
        seed(db)


if __name__ == "__main__":
    main()
