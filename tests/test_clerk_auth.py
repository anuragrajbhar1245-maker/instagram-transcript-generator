import pytest
from unittest.mock import patch, MagicMock
from fastapi.security import HTTPAuthorizationCredentials
from database import SessionLocal, init_db
from models import User
from auth import (
    get_current_user,
    get_optional_user,
    create_access_token,
    verify_token
)

@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    db = SessionLocal()
    db.query(User).filter(User.email.like("%@clerktest.com")).delete(synchronize_session=False)
    db.commit()
    db.close()

def test_clerk_user_model_fields():
    db = SessionLocal()
    user = User(
        clerk_id="user_2mock_clerk_id_123",
        email="john.doe@clerktest.com",
        password_hash=None,
        full_name="John Doe",
        avatar_url="https://img.clerk.com/avatar1.png",
        tier="free",
        credits=10
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    assert user.id is not None
    assert user.clerk_id == "user_2mock_clerk_id_123"
    assert user.password_hash is None
    assert user.avatar_url == "https://img.clerk.com/avatar1.png"
    assert user.credits == 10

    db.delete(user)
    db.commit()
    db.close()

def test_jit_user_provisioning_from_clerk_token():
    db = SessionLocal()
    
    mock_clerk_payload = {
        "sub": "user_2mock_clerk_id_999",
        "email": "auto_created@clerktest.com",
        "name": "Auto Created User",
        "picture": "https://img.clerk.com/profile.png"
    }

    with patch("auth.verify_token", return_value=mock_clerk_payload):
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="mock_clerk_jwt")
        user = get_current_user(auth=credentials, db=db)

        assert user.id is not None
        assert user.clerk_id == "user_2mock_clerk_id_999"
        assert user.email == "auto_created@clerktest.com"
        assert user.full_name == "Auto Created User"
        assert user.avatar_url == "https://img.clerk.com/profile.png"
        assert user.credits == 10  # 10 free credits initialized

    db.delete(user)
    db.commit()
    db.close()

def test_link_existing_user_by_email_on_clerk_login():
    db = SessionLocal()
    # 1. Create legacy user without clerk_id
    legacy_user = User(
        email="existing@clerktest.com",
        password_hash="legacy_hashed_pass",
        full_name="Existing User",
        tier="pro",
        credits=50
    )
    db.add(legacy_user)
    db.commit()
    db.refresh(legacy_user)

    # 2. User signs in with Clerk using same email
    mock_clerk_payload = {
        "sub": "user_2clerk_linked_id_777",
        "email": "existing@clerktest.com",
        "picture": "https://img.clerk.com/avatar2.png"
    }

    with patch("auth.verify_token", return_value=mock_clerk_payload):
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="mock_clerk_jwt")
        user = get_current_user(auth=credentials, db=db)

        assert user.id == legacy_user.id
        assert user.clerk_id == "user_2clerk_linked_id_777"
        assert user.tier == "pro"
        assert user.credits == 50  # preserved credits
        assert user.avatar_url == "https://img.clerk.com/avatar2.png"

    db.delete(user)
    db.commit()
    db.close()

def test_legacy_jwt_verification():
    db = SessionLocal()
    user = User(
        email="legacy_login@clerktest.com",
        password_hash="hash",
        full_name="Legacy Login",
        credits=10
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.email, "uid": user.id})
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    current_user = get_current_user(auth=credentials, db=db)

    assert current_user.id == user.id
    assert current_user.email == user.email

    db.delete(user)
    db.commit()
    db.close()

def test_google_oauth_login_endpoint():
    from fastapi.testclient import TestClient
    from app import app

    client = TestClient(app)
    
    mock_google_info = {
        "sub": "109876543210987654321",
        "email": "google_user@clerktest.com",
        "email_verified": True,
        "name": "Google Verified User",
        "picture": "https://lh3.googleusercontent.com/a/mock_avatar"
    }

    with patch("app.verify_google_id_token", return_value=mock_google_info):
        resp = client.post("/api/auth/google", json={"credential": "valid_google_id_token_jwt"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "access_token" in data
        assert data["user"]["email"] == "google_user@clerktest.com"
        assert data["user"]["full_name"] == "Google Verified User"
        assert data["user"]["avatar_url"] == "https://lh3.googleusercontent.com/a/mock_avatar"
        assert data["user"]["credits"] == 10

        # Clean up
        db = SessionLocal()
        u = db.query(User).filter(User.email == "google_user@clerktest.com").first()
        if u:
            db.delete(u)
            db.commit()
        db.close()

def test_google_oauth_invalid_token():
    from fastapi.testclient import TestClient
    from app import app

    client = TestClient(app)
    with patch("app.verify_google_id_token", return_value=None):
        resp = client.post("/api/auth/google", json={"credential": "invalid_fake_token"})
        assert resp.status_code == 401


