from fastapi import Header, HTTPException, status, Depends
from pydantic import BaseModel
import os
from .db import get_session
from .models import APIKey, User, Team
from .security import verify_key
from datetime import datetime, timezone


class Principal(BaseModel):
    key_id: str
    # Ownership context
    organization_id: str
    owner_type: str  # 'user' | 'team'
    owner_id: str
    # Back-compat for places still expecting a user_id
    user_id: str | None = None
    role: str = "user"


async def require_key(x_api_key: str | None = Header(default=None)) -> Principal:
    if not x_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing x-api-key")

    # Bootstrap admin key bypass for initial setup
    bootstrap = os.getenv("ADMIN_BOOTSTRAP_KEY")
    if bootstrap and x_api_key == bootstrap:
        # Bootstrap is super-admin without org context; fabricate a stub
        return Principal(
            key_id="bootstrap",
            organization_id="bootstrap",
            owner_type="user",
            owner_id="bootstrap",
            user_id="bootstrap",
            role="admin",
        )

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
                # Resolve ownership → organization
                if getattr(k, "owner_type", None) == "team":
                    t = db.query(Team).get(k.owner_id)
                    if not t:
                        continue
                    return Principal(
                        key_id=str(k.id),
                        organization_id=str(t.organization_id),
                        owner_type="team",
                        owner_id=str(t.id),
                        user_id=None,
                        role=k.role,
                    )
                else:
                    # default to user
                    u = db.query(User).get(k.owner_id or k.user_id)
                    if not u:
                        continue
                    return Principal(
                        key_id=str(k.id),
                        organization_id=str(u.organization_id),
                        owner_type="user",
                        owner_id=str(u.id),
                        user_id=str(u.id),
                        role=k.role,
                    )

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


async def require_admin(principal: Principal = Depends(require_key)) -> Principal:
    if principal.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin required")
    return principal
