from __future__ import annotations

import base64
import hashlib
import hmac
import os
import time

import jwt
from cryptography.fernet import Fernet

from .config import settings


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return f"scrypt${base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, s, h = stored.split("$")
        dk = hashlib.scrypt(password.encode(), salt=base64.b64decode(s), n=2**14, r=8, p=1, dklen=32)
        return hmac.compare_digest(dk, base64.b64decode(h))
    except Exception:
        return False


def create_token(user_id: str, ttl: int = 60 * 60 * 12) -> str:
    return jwt.encode({"sub": user_id, "exp": int(time.time()) + ttl}, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> str | None:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])["sub"]
    except jwt.PyJWTError:
        return None


def _fernet() -> Fernet:
    secret = settings.encryption_key
    if not secret:
        if settings.env == "production":
            raise RuntimeError("ENCRYPTION_KEY is required in production")
        secret = "dev-" + settings.jwt_secret
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest()))   # any long random string works


def encrypt_secret(plain: str) -> str:
    return _fernet().encrypt(plain.encode()).decode()


def decrypt_secret(token: str) -> str:
    return _fernet().decrypt(token.encode()).decode()


def verify_github_signature(body: bytes, signature_header: str | None, secret: str) -> bool:
    if not secret or not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)


def verify_razorpay_signature(body: bytes, signature: str | None, secret: str) -> bool:
    if not secret or not signature:
        return False
    return hmac.compare_digest(hmac.new(secret.encode(), body, hashlib.sha256).hexdigest(), signature)
