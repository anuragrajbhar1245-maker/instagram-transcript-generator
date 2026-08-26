import os
import time
import datetime
from typing import Optional, Dict, Any, List
import bcrypt
import jwt
from jwt.algorithms import RSAAlgorithm
import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from database import get_db
from models import User
import config

SECRET_KEY = getattr(config, "JWT_SECRET_KEY", os.getenv("JWT_SECRET_KEY", "instatranscript-super-secret-production-key-2026"))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30

security = HTTPBearer(auto_error=False)

# In-memory cache for Clerk JWKS keys
_jwks_cache: Dict[str, Any] = {"keys": [], "expires_at": 0}

def get_clerk_jwks() -> List[dict]:
    """Fetches and caches Clerk JWKS public keys from configured endpoint."""
    now = time.time()
    if _jwks_cache["keys"] and now < _jwks_cache["expires_at"]:
        return _jwks_cache["keys"]

    jwks_url = getattr(config, "CLERK_JWKS_URL", "") or os.getenv("CLERK_JWKS_URL", "")
    issuer = getattr(config, "CLERK_ISSUER", "") or os.getenv("CLERK_ISSUER", "")

    if not jwks_url and issuer:
        jwks_url = f"{issuer.rstrip('/')}/.well-known/jwks.json"

    if not jwks_url:
        return []

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(jwks_url)
            if resp.status_code == 200:
                jwks = resp.json().get("keys", [])
                _jwks_cache["keys"] = jwks
                _jwks_cache["expires_at"] = now + 3600  # Cache for 1 hour
                return jwks
    except Exception as e:
        print(f"Warning: Failed to fetch Clerk JWKS from {jwks_url}: {e}")

    return _jwks_cache.get("keys", [])

def verify_token(token: str) -> Optional[dict]:
    """
    Decodes and validates JWT token supporting both Clerk RS256 and legacy HS256 tokens.
    """
    try:
        unverified_header = jwt.get_unverified_header(token)
        alg = unverified_header.get("alg", "RS256")
        kid = unverified_header.get("kid")

        # 1. Handle Legacy HS256 Tokens
        if alg == "HS256":
            return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

        # 2. Handle Clerk RS256 Tokens
        jwks = get_clerk_jwks()
        key_dict = next((k for k in jwks if k.get("kid") == kid), None) if kid else None

        # Refresh cache once if key not found
        if not key_dict and jwks:
            _jwks_cache["expires_at"] = 0
            jwks = get_clerk_jwks()
            key_dict = next((k for k in jwks if k.get("kid") == kid), None) if kid else None

        if key_dict:
            public_key = RSAAlgorithm.from_jwk(key_dict)
            return jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                options={"verify_aud": False}
            )

        # Fallback decode attempt for custom Clerk configurations
        return None
    except Exception:
        return None

def verify_google_id_token(id_token: str) -> Optional[dict]:
    """
    Verifies genuine Google OAuth ID Token via Google's tokeninfo API.
    Returns payload containing 'sub', 'email', 'name', 'picture' if valid.
    """
    if not id_token:
        return None
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}")
            if resp.status_code == 200:
                data = resp.json()
                if data.get("email_verified") in [True, "true", "True"]:
                    return data
    except Exception as e:
        print(f"Google token verification error: {e}")
    return None

def hash_password(password: str) -> str:
    """Hashes password using bcrypt with salt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies plain password against hashed password."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    """Creates signed legacy JWT token."""
    to_encode = data.copy()
    now = datetime.datetime.now(datetime.timezone.utc)
    expire = now + (expires_delta or datetime.timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire, "iat": now})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> Optional[dict]:
    """Unified token decoder for legacy and Clerk tokens."""
    return verify_token(token)

def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Requires authentication, raising 401 if invalid.
    Supports JIT (Just-In-Time) user creation and linking for Clerk authenticated users.
    """
    if not auth or not auth.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided."
        )

    payload = verify_token(auth.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token."
        )

    sub = payload["sub"]

    # Check if sub is an email (legacy) or Clerk user ID (e.g. user_xxx)
    if "@" in sub:
        # Legacy user lookup
        user = db.query(User).filter(User.email == sub).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found."
            )
        return user

    # Clerk user ID lookup
    clerk_id = sub
    user = db.query(User).filter(User.clerk_id == clerk_id).first()

    if not user:
        # Check if email is in payload to link existing account
        email = payload.get("email") or payload.get("primary_email_address")
        if email:
            user = db.query(User).filter(User.email == email.lower().strip()).first()
            if user:
                user.clerk_id = clerk_id
                if not user.avatar_url and payload.get("picture"):
                    user.avatar_url = payload.get("picture")
                db.commit()
                db.refresh(user)
                return user

        # JIT Provision new user with 10 free credits
        effective_email = email or f"{clerk_id}@clerk.user"
        user = User(
            clerk_id=clerk_id,
            email=effective_email.lower().strip(),
            full_name=payload.get("name") or payload.get("first_name") or effective_email.split("@")[0],
            avatar_url=payload.get("picture"),
            tier="free",
            credits=10
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return user

def get_optional_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Optional authentication for guest-friendly routes."""
    if not auth or not auth.credentials:
        return None
    try:
        return get_current_user(auth, db)
    except HTTPException:
        return None

