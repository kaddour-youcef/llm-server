from fastapi import APIRouter, Depends, HTTPException, Query
from ..auth import require_admin, Principal
from ..db import (
    get_session,
    create_user as db_create_user,
    list_users as db_list_users,
)
from ..db import (
    create_api_key as db_create_key,
    list_keys as db_list_keys,
    revoke_key as db_revoke_key,
    rotate_key as db_rotate_key,
    audit as db_audit,
)
from ..db import get_user as db_get_user, update_user as db_update_user, list_keys_for_user as db_list_keys_for_user
from ..schemas import UserCreate, KeyCreate, UserUpdate
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from datetime import date, timedelta
import json


router = APIRouter()


@router.get("/users")
async def list_users(
    _: Principal = Depends(require_admin),
    page: int | None = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int | None = Query(default=25, ge=1, le=200, description="Items per page"),
    sort_by: str | None = Query(default="created_at", description="Sort field: name|email|created_at"),
    sort_dir: str | None = Query(default="desc", description="Sort direction: asc|desc"),
    q: str | None = Query(default=None, description="Search users by name or email"),
):
    with get_session() as db:
        items, total = db_list_users(db, page=page, page_size=page_size, sort_by=sort_by, sort_dir=sort_dir, q=q)
        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
        }


@router.post("/users")
async def create_user(payload: UserCreate, principal: Principal = Depends(require_admin)):
    with get_session() as db:
        try:
            rec = db_create_user(db, name=payload.name, email=payload.email)
        except IntegrityError:
            # duplicate email or other constraint
            raise HTTPException(status_code=409, detail="Email already exists")
        db_audit(db, principal.key_id, "CREATE_USER", rec["id"], {"name": payload.name})
        return rec


@router.get("/users/{user_id}")
async def get_user_detail(user_id: str, _: Principal = Depends(require_admin)):
    with get_session() as db:
        user = db_get_user(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        keys = db_list_keys_for_user(db, user_id)
        return {**user, "keys": keys}


@router.patch("/users/{user_id}")
async def update_user(user_id: str, payload: UserUpdate, principal: Principal = Depends(require_admin)):
    with get_session() as db:
        try:
            rec = db_update_user(db, user_id, name=payload.name, email=payload.email)
        except IntegrityError:
            raise HTTPException(status_code=409, detail="Email already exists")
        if not rec:
            raise HTTPException(status_code=404, detail="User not found")
        db_audit(db, principal.key_id, "UPDATE_USER", user_id, {k: v for k, v in payload.dict().items() if v is not None})
        return rec


@router.get("/keys")
async def list_keys(
    _: Principal = Depends(require_admin),
    page: int | None = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int | None = Query(default=25, ge=1, le=200, description="Items per page"),
    sort_by: str | None = Query(default="created_at", description="Sort field: name|user_id|role|status|created_at"),
    sort_dir: str | None = Query(default="desc", description="Sort direction: asc|desc"),
    status: str | None = Query(default=None, description="Filter by status: active|revoked"),
    q: str | None = Query(default=None, description="Search keys by name, last4, role, or user_id"),
):
    with get_session() as db:
        items, total = db_list_keys(
            db,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_dir=sort_dir,
            status=status,
            q=q,
        )
        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
        }


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
async def usage(
    _: Principal = Depends(require_admin),
    from_date: str | None = Query(default=None, alias="from", description="Start date YYYY-MM-DD (inclusive)"),
    to_date: str | None = Query(default=None, alias="to", description="End date YYYY-MM-DD (inclusive)"),
    key_id: str | None = Query(default=None, description="Filter by API key ID"),
):
    # Defaults to last 30 days if not provided
    try:
        to_dt = date.fromisoformat(to_date) if to_date else date.today()
        from_dt = date.fromisoformat(from_date) if from_date else (to_dt - timedelta(days=30))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    params = {"from": from_dt, "to": to_dt}
    where_extra = ""
    if key_id:
        where_extra = " AND key_id = :key_id"
        params["key_id"] = key_id

    with get_session() as db:
        # Totals across the range
        totals_row = db.execute(
            text(
                f"""
                SELECT 
                    COALESCE(SUM(request_count), 0) AS request_count,
                    COALESCE(SUM(total_tokens), 0) AS total_tokens
                FROM usage_rollups
                WHERE day BETWEEN :from AND :to
                {where_extra}
                """
            ),
            params,
        ).fetchone()

        # Per-day series
        rows = db.execute(
            text(
                f"""
                SELECT day, 
                       COALESCE(SUM(request_count), 0) AS request_count,
                       COALESCE(SUM(total_tokens), 0) AS total_tokens
                FROM usage_rollups
                WHERE day BETWEEN :from AND :to
                {where_extra}
                GROUP BY day
                ORDER BY day ASC
                """
            ),
            params,
        ).fetchall()

        return {
            "totals": {
                "request_count": int(totals_row.request_count if totals_row and totals_row.request_count is not None else 0),
                "total_tokens": int(totals_row.total_tokens if totals_row and totals_row.total_tokens is not None else 0),
            },
            "timeseries": [
                {
                    "day": r.day.isoformat(),
                    "request_count": int(r.request_count or 0),
                    "total_tokens": int(r.total_tokens or 0),
                }
                for r in rows
            ],
        }


@router.get("/requests")
async def requests(_: Principal = Depends(require_admin)):
    with get_session() as db:
        rows = db.execute(
            text(
                """
                SELECT id, created_at, endpoint, status_code, latency_ms, user_id, key_id,
                       total_tokens, error_message, request_body, response_body
                FROM requests
                ORDER BY created_at DESC
                LIMIT 100
                """
            )
        ).fetchall()

        def _to_str(val):
            return str(val) if val is not None else None

        results = []
        for r in rows:
            results.append(
                {
                    "id": _to_str(r.id),
                    "timestamp": r.created_at.isoformat() if getattr(r, "created_at", None) else None,
                    "method": "POST",  # Current endpoints are POST; default for log display
                    "endpoint": r.endpoint,
                    "status_code": r.status_code,
                    "response_time_ms": r.latency_ms,
                    "user_id": _to_str(r.user_id),
                    "key_id": _to_str(r.key_id),
                    "tokens_used": r.total_tokens,
                    "error_message": r.error_message,
                    # The admin UI expects stringified JSON it can JSON.parse safely
                    "request_body": json.dumps(r.request_body) if r.request_body is not None else None,
                    "response_body": json.dumps(r.response_body) if r.response_body is not None else None,
                }
            )

        return results
