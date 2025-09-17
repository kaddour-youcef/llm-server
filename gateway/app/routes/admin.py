from fastapi import APIRouter, Depends, HTTPException
from ..auth import require_admin, Principal
from ..db import get_session, create_user as db_create_user, list_users as db_list_users
from ..db import create_api_key as db_create_key, list_keys as db_list_keys, revoke_key as db_revoke_key, rotate_key as db_rotate_key, audit as db_audit
from ..schemas import UserCreate, KeyCreate


router = APIRouter()


@router.get("/users")
async def list_users(_: Principal = Depends(require_admin)):
    with get_session() as db:
        return db_list_users(db)


@router.post("/users")
async def create_user(payload: UserCreate, principal: Principal = Depends(require_admin)):
    with get_session() as db:
        rec = db_create_user(db, name=payload.name, email=payload.email)
        db_audit(db, principal.key_id, "CREATE_USER", rec["id"], {"name": payload.name})
        return rec


@router.get("/keys")
async def list_keys(_: Principal = Depends(require_admin)):
    with get_session() as db:
        return db_list_keys(db)


@router.post("/keys")
async def create_key(payload: KeyCreate, principal: Principal = Depends(require_admin)):
    with get_session() as db:
        rec = db_create_key(
            db,
            user_id=payload.user_id,
            name=payload.name,
            role=payload.role or "user",
            monthly_quota_tokens=payload.monthly_quota_tokens,
            daily_request_quota=payload.daily_request_quota,
        )
        db_audit(db, principal.key_id, "CREATE_KEY", rec["id"], {"name": payload.name})
        return rec


@router.post("/keys/{key_id}/revoke")
async def revoke_key(key_id: str, principal: Principal = Depends(require_admin)):
    with get_session() as db:
        try:
            rec = db_revoke_key(db, key_id)
            db_audit(db, principal.key_id, "REVOKE_KEY", key_id, None)
            return rec
        except ValueError:
            raise HTTPException(status_code=404, detail="Key not found")


@router.post("/keys/{key_id}/rotate")
async def rotate_key(key_id: str, principal: Principal = Depends(require_admin)):
    with get_session() as db:
        try:
            rec = db_rotate_key(db, key_id)
            db_audit(db, principal.key_id, "ROTATE_KEY", key_id, None)
            return rec
        except ValueError:
            raise HTTPException(status_code=404, detail="Key not found")


@router.get("/usage")
async def usage(_: Principal = Depends(require_admin)):
    return {"totals": {"request_count": 0, "total_tokens": 0}, "timeseries": []}


@router.get("/requests")
async def requests(_: Principal = Depends(require_admin)):
    return []
