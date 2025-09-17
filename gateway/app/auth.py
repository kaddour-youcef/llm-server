from fastapi import Header, HTTPException, status, Depends
from pydantic import BaseModel


class Principal(BaseModel):
    key_id: str
    user_id: str
    role: str = "user"


async def require_key(x_api_key: str | None = Header(default=None)) -> Principal:
    if not x_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing x-api-key")
    # TODO: look up hashed key in DB; for now, accept any non-empty key as a placeholder
    # Derive pseudo IDs for skeleton usage
    return Principal(key_id="00000000-0000-0000-0000-000000000000", user_id="00000000-0000-0000-0000-000000000000")


async def require_admin(principal: Principal = Depends(require_key)) -> Principal:
    if principal.role != "admin":
        # In the skeleton, allow bootstrap via ADMIN_BOOTSTRAP_KEY later
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin required")
    return principal

