import pytest
from auth import hash_password, verify_password, create_access_token, decode_access_token
from database import SessionLocal, init_db, engine, Base
from models import User, TranscriptRecord

@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    db = SessionLocal()
    # Clean up test users
    db.query(User).filter(User.email.like("%@test.com")).delete(synchronize_session=False)
    db.commit()
    db.close()

def test_password_hashing():
    raw = "MySecretPass123"
    hashed = hash_password(raw)
    assert hashed != raw
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPass", hashed) is False

def test_jwt_token_flow():
    payload = {"sub": "user@test.com", "uid": 42}
    token = create_access_token(payload)
    assert isinstance(token, str)
    
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "user@test.com"
    assert decoded["uid"] == 42

def test_user_creation_and_credits():
    db = SessionLocal()
    user = User(
        email="test_credits@test.com",
        password_hash=hash_password("password123"),
        full_name="Test User",
        tier="free",
        credits=10
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    assert user.id is not None
    assert user.credits == 10
    
    # Deduct 1 credit
    user.credits -= 1
    db.commit()
    db.refresh(user)
    assert user.credits == 9

    db.close()
