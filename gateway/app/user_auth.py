import base64
import json
import hmac
import hashlib
import time
from typing import Any, Dict, Optional
from fastapi import Header, HTTPException, status, Request
from .config import settings


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = '=' * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _sign(msg: bytes, secret: str) -> str:
    sig = hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).digest()
    return _b64url_encode(sig)


def jwt_encode(payload: Dict[str, Any], ttl_s: int) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    body = {
        **payload,
        "iat": now,
        "exp": now + ttl_s,
    }
    h = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    b = _b64url_encode(json.dumps(body, separators=(",", ":")).encode("utf-8"))
    msg = f"{h}.{b}".encode("utf-8")
    sig = _sign(msg, settings.auth_secret)
    return f"{h}.{b}.{sig}"


def jwt_decode(token: str) -> Dict[str, Any]:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid token")
        h, b, s = parts
        msg = f"{h}.{b}".encode("utf-8")
        expected = _sign(msg, settings.auth_secret)
        if not hmac.compare_digest(s, expected):
            raise ValueError("Bad signature")
        payload = json.loads(_b64url_decode(b))
        if int(payload.get("exp", 0)) < int(time.time()):
            raise ValueError("Expired")
        return payload
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def extract_bearer(auth_header: Optional[str]) -> Optional[str]:
    if not auth_header:
        return None
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()
    return None


async def require_user(
    request: Request,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> Dict[str, Any]:
    token = extract_bearer(authorization)
    if not token:
        # fallback to cookie
        token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing access token")
    payload = jwt_decode(token)
    if payload.get("typ") != "access" or not payload.get("sub"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")
    return payload  # contains sub=user_id, name, email, role

