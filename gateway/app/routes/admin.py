from fastapi import APIRouter, Depends, HTTPException
from ..auth import require_admin, Principal


router = APIRouter()


@router.get("/users")
async def list_users(_: Principal = Depends(require_admin)):
    # TODO: query DB
    return []


@router.post("/users")
async def create_user(_: Principal = Depends(require_admin)):
    # TODO: insert user
    return {"id": "todo"}


@router.get("/keys")
async def list_keys(_: Principal = Depends(require_admin)):
    return []


@router.post("/keys")
async def create_key(_: Principal = Depends(require_admin)):
    # TODO: generate, hash, store
    return {"id": "todo", "plaintext_key": "copy_me_now", "last4": "XXXX"}


@router.post("/keys/{key_id}/revoke")
async def revoke_key(key_id: str, _: Principal = Depends(require_admin)):
    return {"id": key_id, "status": "revoked"}


@router.post("/keys/{key_id}/rotate")
async def rotate_key(key_id: str, _: Principal = Depends(require_admin)):
    return {"id": key_id, "plaintext_key": "new_key", "last4": "YYYY"}


@router.get("/usage")
async def usage(_: Principal = Depends(require_admin)):
    return {"totals": {"request_count": 0, "total_tokens": 0}, "timeseries": []}


@router.get("/requests")
async def requests(_: Principal = Depends(require_admin)):
    return []

