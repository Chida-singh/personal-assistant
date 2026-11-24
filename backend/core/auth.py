import base64
import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session, select

from .database import get_session
from .models import User

JWT_SECRET = os.getenv("JWT_SECRET", "super_secret_key_change_in_production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30

security = HTTPBearer(auto_error=False)


# ── Password Hashing (PBKDF2-HMAC-SHA256 with salt) ──────────────────────────

def hash_password(password: str) -> str:
    salt = os.urandom(16).hex()
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return f"{salt}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        salt, stored_hash = hashed_password.split("$")
        key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100000)
        return hmac.compare_digest(key.hex(), stored_hash)
    except Exception:
        return False


# ── JWT Token Generation & Verification (HMAC-SHA256 Base64URL) ──────────────

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64url_decode(data_str: str) -> bytes:
    padding = 4 - (len(data_str) % 4)
    if padding and padding < 4:
        data_str += "=" * padding
    return base64.urlsafe_b64decode(data_str.encode("utf-8"))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = time.time() + expires_delta.total_seconds()
    else:
        expire = time.time() + (ACCESS_TOKEN_EXPIRE_DAYS * 86400)
    to_encode.update({"exp": int(expire), "iat": int(time.time())})

    header = {"alg": ALGORITHM, "typ": "JWT"}
    encoded_header = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    encoded_payload = _b64url_encode(json.dumps(to_encode, separators=(",", ":")).encode("utf-8"))

    signature_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    signature = hmac.new(JWT_SECRET.encode("utf-8"), signature_input, hashlib.sha256).digest()
    encoded_signature = _b64url_encode(signature)

    return f"{encoded_header}.{encoded_payload}.{encoded_signature}"


def verify_token(token: str) -> Optional[dict]:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, signature_b64 = parts

        expected_sig = hmac.new(
            JWT_SECRET.encode("utf-8"),
            f"{header_b64}.{payload_b64}".encode("utf-8"),
            hashlib.sha256
        ).digest()

        if not hmac.compare_digest(_b64url_encode(expected_sig), signature_b64):
            return None

        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


# ── Default User Initialization ──────────────────────────────────────────────

def ensure_default_user(session: Session):
    default_user = os.getenv("AUTH_USERNAME", "admin")
    default_pass = os.getenv("AUTH_PASSWORD", "password")

    user = session.exec(select(User).where(User.username == default_user)).first()
    if not user:
        # If user with old username exists, update to new .env username & password
        any_user = session.exec(select(User)).first()
        if any_user:
            any_user.username = default_user
            any_user.hashed_password = hash_password(default_pass)
            session.add(any_user)
            session.commit()
            print(f"[Auth] Updated user to '{default_user}' from .env.")
            return

        user = User(
            username=default_user,
            hashed_password=hash_password(default_pass),
            created_at=datetime.utcnow()
        )
        session.add(user)
        session.commit()
        print(f"[Auth] Default user '{default_user}' created.")
    else:
        # If password in .env changed, update the hash
        if not verify_password(default_pass, user.hashed_password):
            user.hashed_password = hash_password(default_pass)
            session.add(user)
            session.commit()
            print(f"[Auth] Updated password for '{default_user}' from .env.")



# ── FastAPI Dependencies ─────────────────────────────────────────────────────

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: Session = Depends(get_session)
) -> User:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username = payload.get("sub") or payload.get("user_id")
    user = session.exec(select(User).where(User.username == username)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
