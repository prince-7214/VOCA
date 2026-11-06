"""
Authentication service — password hashing and JWT tokens.
"""

import hashlib
import hmac
import os
import json
import base64
import time
import logging

logger = logging.getLogger(__name__)

SECRET_KEY = os.environ.get("JWT_SECRET", "voca-default-secret-change-in-production")
ACCESS_TOKEN_EXPIRE_SECONDS = 24 * 60 * 60  # 24 hours


# ---------------------------------------------------------------------------
# Password hashing (SHA-256 + salt — simple, no extra dependencies)
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    """Hash a password with a random salt using SHA-256."""
    salt = os.urandom(16).hex()
    hashed = hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()
    return f"{salt}${hashed}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a salted SHA-256 hash."""
    try:
        salt, stored_hash = hashed_password.split("$", 1)
        check_hash = hashlib.sha256(f"{salt}:{plain_password}".encode()).hexdigest()
        return hmac.compare_digest(check_hash, stored_hash)
    except (ValueError, AttributeError):
        return False


# ---------------------------------------------------------------------------
# JWT tokens (minimal implementation — no extra dependencies)
# ---------------------------------------------------------------------------

def _b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64_decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def create_token(user_id: int) -> str:
    """Create a simple JWT access token."""
    header = _b64_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload_data = {
        "sub": str(user_id),
        "exp": int(time.time()) + ACCESS_TOKEN_EXPIRE_SECONDS,
    }
    payload = _b64_encode(json.dumps(payload_data).encode())
    signature = hmac.new(
        SECRET_KEY.encode(), f"{header}.{payload}".encode(), hashlib.sha256
    ).digest()
    sig_str = _b64_encode(signature)
    return f"{header}.{payload}.{sig_str}"


def decode_token(token: str) -> int:
    """Decode a JWT token and return the user_id. Raises ValueError on failure."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid token format")

        header_part, payload_part, sig_part = parts

        # Verify signature
        expected_sig = hmac.new(
            SECRET_KEY.encode(),
            f"{header_part}.{payload_part}".encode(),
            hashlib.sha256,
        ).digest()
        actual_sig = _b64_decode(sig_part)
        if not hmac.compare_digest(expected_sig, actual_sig):
            raise ValueError("Invalid signature")

        # Decode payload
        payload_data = json.loads(_b64_decode(payload_part))

        # Check expiration
        if payload_data.get("exp", 0) < time.time():
            raise ValueError("Token expired")

        return int(payload_data["sub"])
    except (KeyError, json.JSONDecodeError, Exception) as exc:
        raise ValueError(f"Invalid token: {exc}")

