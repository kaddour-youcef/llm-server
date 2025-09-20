from fastapi import Header, HTTPException, status, Depends
from pydantic import BaseModel
import os
from .db import get_session
from .models import APIKey
from .security import verify_key
from datetime import datetime, timezone


class Principal(BaseModel):
    key_id: str
    user_id: str
    role: str = "user"


async def require_key(x_api_key: str | None = Header(default=None)) -> Principal:
    if not x_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing x-api-key")

    # Bootstrap admin key bypass for initial setup
    bootstrap = os.getenv("ADMIN_BOOTSTRAP_KEY")
    if bootstrap and x_api_key == bootstrap:
        return Principal(key_id="bootstrap", user_id="bootstrap", role="admin")

    last4 = x_api_key[-4:]
    # Look up keys with matching last4 and verify hash
    with get_session() as db:
        candidates = db.query(APIKey).filter(APIKey.key_last4 == last4).all()
        for k in candidates:
            if k.status != "active":
                continue
            # Enforce key expiration: null = unlimited
            if getattr(k, "expires_at", None):
                now = datetime.now(timezone.utc)
                # if stored expires_at is naive, treat as UTC
                exp = k.expires_at if k.expires_at.tzinfo else k.expires_at.replace(tzinfo=timezone.utc)
                if now > exp:
                    continue
            if verify_key(x_api_key, k.key_hash):
                return Principal(key_id=str(k.id), user_id=str(k.user_id), role=k.role)

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


async def require_admin(principal: Principal = Depends(require_key)) -> Principal:
    if principal.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin required")
    return principal
