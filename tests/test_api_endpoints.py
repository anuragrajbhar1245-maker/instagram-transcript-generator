import pytest
import uuid
import json
from fastapi.testclient import TestClient
from app import app
from database import SessionLocal, init_db
from models import User, TranscriptRecord
from auth import hash_password, create_access_token

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_test_data():
    init_db()
    db = SessionLocal()
    # Clean up test users & their records
    test_users = db.query(User).filter(User.email.like("%@testclient.com")).all()
    for u in test_users:
        db.delete(u)
    db.commit()
    db.close()
    yield
    # Teardown
    db = SessionLocal()
    test_users = db.query(User).filter(User.email.like("%@testclient.com")).all()
    for u in test_users:
        db.delete(u)
    db.commit()
    db.close()

def test_health_check_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "Instagram Transcript Generator" in data["service"]
    assert data["supported_languages_count"] >= 30

def test_supported_languages_endpoint():
    res = client.get("/api/languages")
    assert res.status_code == 200
    languages = res.json()
    assert isinstance(languages, list)
    codes = [item["code"] for item in languages]
    assert "en" in codes
    assert "hi" in codes
    assert "es" in codes
    assert "auto" in codes

def test_user_registration_and_login_flow():
    email = f"user_{uuid.uuid4().hex[:8]}@testclient.com"
    password = "StrongPassword123"
    name = "Test Automation User"

    # 1. Register new user
    reg_res = client.post("/api/auth/register", json={
        "email": email,
        "password": password,
        "full_name": name
    })
    assert reg_res.status_code == 200
    reg_data = reg_res.json()
    assert reg_data["status"] == "success"
    assert "access_token" in reg_data
    assert reg_data["user"]["email"] == email
    assert reg_data["user"]["credits"] == 10
    assert reg_data["user"]["tier"] == "free"

    # 2. Duplicate registration should fail
    dup_res = client.post("/api/auth/register", json={
        "email": email,
        "password": password,
        "full_name": name
    })
    assert dup_res.status_code == 400
    assert "already exists" in dup_res.json()["detail"]

    # 3. Successful Login
    login_res = client.post("/api/auth/login", json={
        "email": email,
        "password": password
    })
    assert login_res.status_code == 200
    login_data = login_res.json()
    token = login_data["access_token"]
    assert token is not None

    # 4. Wrong password login
    bad_login = client.post("/api/auth/login", json={
        "email": email,
        "password": "WrongPassword!"
    })
    assert bad_login.status_code == 401

    # 5. Fetch /api/auth/me with Bearer token
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == email
    assert me_data["credits"] == 10

    # 6. Fetch /api/auth/me without token should fail
    unauth_res = client.get("/api/auth/me")
    assert unauth_res.status_code == 401

def test_user_history_isolation_and_deletion():
    db = SessionLocal()
    # Create User A
    user_a = User(
        email=f"user_a_{uuid.uuid4().hex[:6]}@testclient.com",
        password_hash=hash_password("pass123"),
        full_name="User A",
        credits=10
    )
    # Create User B
    user_b = User(
        email=f"user_b_{uuid.uuid4().hex[:6]}@testclient.com",
        password_hash=hash_password("pass123"),
        credits=10
    )
    db.add(user_a)
    db.add(user_b)
    db.commit()
    db.refresh(user_a)
    db.refresh(user_b)

    task_id_a = str(uuid.uuid4())
    record_a = TranscriptRecord(
        id=task_id_a,
        user_id=user_a.id,
        instagram_url="https://www.instagram.com/reel/C_TestA/",
        title="Reel A Title",
        uploader="creator_a",
        detected_language="en",
        language_name="English",
        full_text="Transcript for Reel A",
        summary="Summary A",
        key_points_json="[]",
        segments_json="[]"
    )
    email_a = user_a.email
    uid_a = user_a.id
    email_b = user_b.email
    uid_b = user_b.id

    db.add(record_a)
    db.commit()
    db.close()

    token_a = create_access_token({"sub": email_a, "uid": uid_a})
    token_b = create_access_token({"sub": email_b, "uid": uid_b})

    # User A sees 1 record
    hist_a = client.get("/api/user/history", headers={"Authorization": f"Bearer {token_a}"})
    assert hist_a.status_code == 200
    assert hist_a.json()["count"] == 1
    assert hist_a.json()["items"][0]["task_id"] == task_id_a

    # User B sees 0 records (Isolation)
    hist_b = client.get("/api/user/history", headers={"Authorization": f"Bearer {token_b}"})
    assert hist_b.status_code == 200
    assert hist_b.json()["count"] == 0

    # User B cannot delete User A's record
    del_b = client.delete(f"/api/user/history/{task_id_a}", headers={"Authorization": f"Bearer {token_b}"})
    assert del_b.status_code == 404

    # User A deletes their own record
    del_a = client.delete(f"/api/user/history/{task_id_a}", headers={"Authorization": f"Bearer {token_a}"})
    assert del_a.status_code == 200
    assert del_a.json()["status"] == "deleted"

    # Now User A history is empty
    hist_a_empty = client.get("/api/user/history", headers={"Authorization": f"Bearer {token_a}"})
    assert hist_a_empty.json()["count"] == 0

def test_transcribe_credit_limit_validation():
    db = SessionLocal()
    # Create zero credit user
    zero_credit_user = User(
        email=f"zero_credit_{uuid.uuid4().hex[:6]}@testclient.com",
        password_hash=hash_password("pass123"),
        tier="free",
        credits=0
    )
    db.add(zero_credit_user)
    db.commit()
    db.refresh(zero_credit_user)
    token = create_access_token({"sub": zero_credit_user.email, "uid": zero_credit_user.id})
    db.close()

    # Attempt to transcribe with 0 credits
    res = client.post(
        "/api/transcribe",
        json={"url": "https://www.instagram.com/reel/C8XYZ123/"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 402
    assert "used all your free transcription credits" in res.json()["detail"]

def test_invalid_instagram_url_rejection():
    res = client.post(
        "/api/transcribe",
        json={"url": "https://youtube.com/watch?v=12345"}
    )
    assert res.status_code == 400
    assert "Invalid Instagram URL" in res.json()["detail"]
