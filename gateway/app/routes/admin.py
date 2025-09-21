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
from ..db import (
    create_organization as db_create_org,
    list_organizations as db_list_orgs,
    get_organization as db_get_org,
    update_organization as db_update_org,
    delete_organization as db_delete_org,
    create_team as db_create_team,
    list_teams as db_list_teams,
    get_team as db_get_team,
    update_team as db_update_team,
    delete_team as db_delete_team,
    add_membership as db_add_membership,
    list_memberships as db_list_memberships,
    remove_membership as db_remove_membership,
)
from ..types import UserCreate, KeyCreate, UserUpdate
from ..types import OrganizationCreate, OrganizationOut, OrganizationUpdate, TeamCreate, TeamOut, TeamUpdate, MembershipCreate, MembershipOut
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
            rec = db_update_user(db, user_id, name=payload.name, email=payload.email, status=payload.status)
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
    sort_by: str | None = Query(default="created_at", description="Sort field: name|user_id|role|status|created_at|expires_at"),
    sort_dir: str | None = Query(default="desc", description="Sort direction: asc|desc"),
    status: str | None = Query(default=None, description="Filter by status: active|revoked"),
    q: str | None = Query(default=None, description="Search keys by name, last4, role, or user_id"),
    expired: bool | None = Query(default=None, description="Filter by expiration status: true=expired, false=not expired (incl. unlimited)"),
    has_expiration: bool | None = Query(default=None, description="Filter to keys that have an expiration date or not"),
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
            expired=expired,
            has_expiration=has_expiration,
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
            name=payload.name,
            role=payload.role or "user",
            owner_type=payload.owner_type,
            owner_id=payload.owner_id,
            user_id=payload.user_id,
            monthly_quota_tokens=payload.monthly_quota_tokens,
            daily_request_quota=payload.daily_request_quota,
            expires_at=payload.expires_at,
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
        except ValueError as e:
            msg = str(e)
            if msg == "key not found":
                raise HTTPException(status_code=404, detail="Key not found")
            elif msg == "key not expired":
                raise HTTPException(status_code=400, detail="Key is not expired; rotation not allowed")
            else:
                raise HTTPException(status_code=400, detail=msg or "Rotation not allowed")


# -------------------------
# Organizations Endpoints
# -------------------------

@router.get("/organizations")
async def list_organizations(_: Principal = Depends(require_admin)):
    with get_session() as db:
        return {"items": db_list_orgs(db)}


@router.post("/organizations")
async def create_organization(payload: OrganizationCreate, principal: Principal = Depends(require_admin)) -> OrganizationOut:
    with get_session() as db:
        try:
            org = db_create_org(
                db,
                name=payload.name,
                status=payload.status or "active",
                monthly_token_quota=payload.monthly_token_quota,
            )
        except IntegrityError:
            raise HTTPException(status_code=409, detail="Organization already exists")
        db_audit(db, principal.key_id, "CREATE_ORG", org["id"], {"name": payload.name})
        return org


@router.get("/organizations/{org_id}")
async def get_organization(org_id: str, _: Principal = Depends(require_admin)) -> OrganizationOut:
    with get_session() as db:
        org = db_get_org(db, org_id)
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        return org


@router.patch("/organizations/{org_id}")
async def update_organization(org_id: str, payload: OrganizationUpdate, principal: Principal = Depends(require_admin)) -> OrganizationOut:
    with get_session() as db:
        org = db_update_org(db, org_id, name=payload.name, status=payload.status, monthly_token_quota=payload.monthly_token_quota)
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        db_audit(db, principal.key_id, "UPDATE_ORG", org_id, {k: v for k, v in payload.dict().items() if v is not None})
        return org


@router.delete("/organizations/{org_id}")
async def delete_organization(org_id: str, principal: Principal = Depends(require_admin)):
    with get_session() as db:
        ok = db_delete_org(db, org_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Organization not found")
        db_audit(db, principal.key_id, "DELETE_ORG", org_id, None)
        return {"ok": True}


# --------------
# Teams
# --------------

@router.get("/teams")
async def list_teams(organization_id: str | None = Query(default=None), _: Principal = Depends(require_admin)):
    with get_session() as db:
        return {"items": db_list_teams(db, organization_id=organization_id)}


@router.post("/teams")
async def create_team(payload: TeamCreate, principal: Principal = Depends(require_admin)) -> TeamOut:
    with get_session() as db:
        team = db_create_team(db, organization_id=payload.organization_id, name=payload.name, description=payload.description)
        db_audit(db, principal.key_id, "CREATE_TEAM", team["id"], {"name": payload.name})
        return team


@router.get("/teams/{team_id}")
async def get_team(team_id: str, _: Principal = Depends(require_admin)) -> TeamOut:
    with get_session() as db:
        t = db_get_team(db, team_id)
        if not t:
            raise HTTPException(status_code=404, detail="Team not found")
        return t


@router.patch("/teams/{team_id}")
async def update_team(team_id: str, payload: TeamUpdate, principal: Principal = Depends(require_admin)) -> TeamOut:
    with get_session() as db:
        t = db_update_team(db, team_id, name=payload.name, description=payload.description)
        if not t:
            raise HTTPException(status_code=404, detail="Team not found")
        db_audit(db, principal.key_id, "UPDATE_TEAM", team_id, {k: v for k, v in payload.dict().items() if v is not None})
        return t


@router.delete("/teams/{team_id}")
async def delete_team(team_id: str, principal: Principal = Depends(require_admin)):
    with get_session() as db:
        ok = db_delete_team(db, team_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Team not found")
        db_audit(db, principal.key_id, "DELETE_TEAM", team_id, None)
        return {"ok": True}


# -----------------
# Memberships
# -----------------

@router.get("/memberships")
async def list_memberships(team_id: str | None = Query(default=None), user_id: str | None = Query(default=None), _: Principal = Depends(require_admin)):
    with get_session() as db:
        return {"items": db_list_memberships(db, team_id=team_id, user_id=user_id)}


@router.post("/memberships")
async def add_membership(payload: MembershipCreate, principal: Principal = Depends(require_admin)) -> MembershipOut:
    with get_session() as db:
        m = db_add_membership(db, team_id=payload.team_id, user_id=payload.user_id, role=payload.role or "member")
        db_audit(db, principal.key_id, "ADD_MEMBERSHIP", m["id"], {"team_id": payload.team_id, "user_id": payload.user_id})
        return m


@router.delete("/memberships/{membership_id}")
async def remove_membership(membership_id: str, principal: Principal = Depends(require_admin)):
    with get_session() as db:
        ok = db_remove_membership(db, membership_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Membership not found")
        db_audit(db, principal.key_id, "REMOVE_MEMBERSHIP", membership_id, None)
        return {"ok": True}


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


@router.get("/organizations/{org_id}/usage")
async def organization_usage(
    org_id: str,
    _: Principal = Depends(require_admin),
    from_date: str | None = Query(default=None, alias="from"),
    to_date: str | None = Query(default=None, alias="to"),
):
    try:
        to_dt = date.fromisoformat(to_date) if to_date else date.today()
        from_dt = date.fromisoformat(from_date) if from_date else (to_dt - timedelta(days=30))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    with get_session() as db:
        # Totals at org level
        tot = db.execute(
            text(
                """
                SELECT COALESCE(SUM(request_count),0) AS request_count,
                       COALESCE(SUM(total_tokens),0) AS total_tokens
                FROM api_usage
                WHERE organization_id = :org_id AND day BETWEEN :from AND :to
                """
            ),
            {"org_id": org_id, "from": from_dt, "to": to_dt},
        ).fetchone()

        # Breakdown by owner_type/owner_id
        rows = db.execute(
            text(
                """
                SELECT owner_type, owner_id,
                       COALESCE(SUM(request_count),0) AS request_count,
                       COALESCE(SUM(total_tokens),0) AS total_tokens
                FROM api_usage
                WHERE organization_id = :org_id AND day BETWEEN :from AND :to
                GROUP BY owner_type, owner_id
                ORDER BY owner_type ASC, total_tokens DESC
                """
            ),
            {"org_id": org_id, "from": from_dt, "to": to_dt},
        ).fetchall()

        return {
            "totals": {"request_count": int(tot.request_count or 0), "total_tokens": int(tot.total_tokens or 0)},
            "breakdown": [
                {"owner_type": r.owner_type, "owner_id": str(r.owner_id), "request_count": int(r.request_count or 0), "total_tokens": int(r.total_tokens or 0)}
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
