from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .config import settings
from .models import User, APIKey, Audit
from .security import hash_key, verify_key
import secrets
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, date, time, timezone
from sqlalchemy import asc, desc, or_, cast, String
import uuid


engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


async def init_db() -> None:
    # Placeholder: migrations are run in container entrypoint via Alembic
    return None


@contextmanager
def get_session() -> Session:
    session: Session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# CRUD helpers (sync, called within endpoints)
def create_user(db: Session, name: str, email: Optional[str], status: str = "approved", password_hash: Optional[str] = None) -> Dict[str, Any]:
    user = User(name=name, email=email, status=status, password_hash=password_hash)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": str(user.id), "name": user.name, "email": user.email, "status": user.status}


def get_user(db: Session, user_id: str) -> Optional[Dict[str, Any]]:
    rec: Optional[User] = db.query(User).get(user_id)
    if not rec:
        return None
    return {
        "id": str(rec.id),
        "name": rec.name,
        "email": rec.email,
        "status": rec.status,
        "created_at": rec.created_at.isoformat() if hasattr(rec, "created_at") and rec.created_at else None,
    }


def update_user(db: Session, user_id: str, name: Optional[str] = None, email: Optional[str] = None, status: Optional[str] = None) -> Optional[Dict[str, Any]]:
    rec: Optional[User] = db.query(User).get(user_id)
    if not rec:
        return None
    if name is not None:
        rec.name = name
    if email is not None:
        rec.email = email
    if status is not None:
        rec.status = status
    db.commit()
    db.refresh(rec)
    return {
        "id": str(rec.id),
        "name": rec.name,
        "email": rec.email,
        "status": rec.status,
        "created_at": rec.created_at.isoformat() if hasattr(rec, "created_at") and rec.created_at else None,
    }


def get_user_by_email(db: Session, email: str) -> Optional[Dict[str, Any]]:
    rec: Optional[User] = db.query(User).filter(User.email == email).first()
    if not rec:
        return None
    return {
        "id": str(rec.id),
        "name": rec.name,
        "email": rec.email,
        "status": rec.status,
        "password_hash": rec.password_hash,
    }


def self_register_user(db: Session, name: str, email: str, password_plain: str) -> Dict[str, Any]:
    user = User(
        name=name,
        email=email,
        password_hash=hash_key(password_plain),
        status="pending",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": str(user.id), "name": user.name, "email": user.email, "status": user.status}


def verify_user_password(db: Session, email: str, password_plain: str) -> Optional[Dict[str, Any]]:
    rec: Optional[User] = db.query(User).filter(User.email == email).first()
    if not rec or not rec.password_hash:
        return None
    if not verify_key(password_plain, rec.password_hash):
        return None
    return {
        "id": str(rec.id),
        "name": rec.name,
        "email": rec.email,
        "status": rec.status,
    }


def list_users(
    db: Session,
    page: Optional[int] = None,
    page_size: Optional[int] = None,
    sort_by: Optional[str] = None,
    sort_dir: Optional[str] = None,
    q: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], int]:
    sort_fields = {
        "name": User.name,
        "email": User.email,
        "created_at": User.created_at,
    }
    sort_col = sort_fields.get((sort_by or "created_at").lower(), User.created_at)
    direction = desc if (sort_dir or "desc").lower() == "desc" else asc
    query = db.query(User)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(User.name.ilike(like), User.email.ilike(like)))
    query = query.order_by(direction(sort_col))
    total = query.count()

    if page and page_size:
        offset = max(page - 1, 0) * page_size
        query = query.offset(offset).limit(page_size)

    rows = query.all()
    return (
        [
            {
                "id": str(u.id),
                "name": u.name,
                "email": u.email,
                "status": getattr(u, "status", None),
                "created_at": u.created_at.isoformat()
                if hasattr(u, "created_at") and u.created_at
                else None,
            }
            for u in rows
        ],
        total,
    )


def create_api_key(
    db: Session,
    user_id: str,
    name: str,
    role: str = "user",
    monthly_quota_tokens: Optional[int] = None,
    daily_request_quota: Optional[int] = None,
    expires_at: Optional[str] = None,
) -> Dict[str, Any]:
    def _parse_expires(v: Optional[str]) -> Optional[datetime]:
        if not v:
            return None
        s = v.strip()
        try:
            # Accept full ISO datetime with or without timezone
            dt = datetime.fromisoformat(s)
            # If naive, assume UTC
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            # Try date-only (YYYY-MM-DD) → set to end of that day in UTC
            try:
                d = date.fromisoformat(s)
                return datetime.combine(d, time(23, 59, 59, 0, tzinfo=timezone.utc))
            except Exception:
                raise ValueError("Invalid expires_at format. Use YYYY-MM-DD or ISO datetime.")

    plaintext = secrets.token_urlsafe(32)
    key_hash = hash_key(plaintext)
    last4 = plaintext[-4:]
    rec = APIKey(
        user_id=user_id,
        name=name,
        key_hash=key_hash,
        key_last4=last4,
        role=role,
        status="active",
        monthly_token_quota=monthly_quota_tokens,
        daily_request_quota=daily_request_quota,
        expires_at=_parse_expires(expires_at),
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return {
        "id": str(rec.id),
        "user_id": str(rec.user_id),
        "name": rec.name,
        "role": rec.role,
        "status": rec.status,
        "last4": rec.key_last4,
        "expires_at": rec.expires_at.isoformat() if getattr(rec, "expires_at", None) else None,
        "plaintext_key": plaintext,
    }


def list_keys(
    db: Session,
    page: Optional[int] = None,
    page_size: Optional[int] = None,
    sort_by: Optional[str] = None,
    sort_dir: Optional[str] = None,
    status: Optional[str] = None,
    q: Optional[str] = None,
    expired: Optional[bool] = None,
    has_expiration: Optional[bool] = None,
) -> Tuple[List[Dict[str, Any]], int]:
    sort_fields = {
        "name": APIKey.name,
        "user_id": APIKey.user_id,
        "role": APIKey.role,
        "status": APIKey.status,
        "created_at": APIKey.created_at,
        "expires_at": APIKey.expires_at,
    }
    sort_col = sort_fields.get((sort_by or "created_at").lower(), APIKey.created_at)
    direction = desc if (sort_dir or "desc").lower() == "desc" else asc
    query = db.query(APIKey)
    if status and status.lower() in {"active", "revoked"}:
        query = query.filter(APIKey.status == status.lower())
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                APIKey.name.ilike(like),
                APIKey.key_last4.ilike(like),
                APIKey.role.ilike(like),
                cast(APIKey.user_id, String).ilike(like),
            )
        )
    # Expiration filters
    if has_expiration is True:
        query = query.filter(APIKey.expires_at.isnot(None))
    elif has_expiration is False:
        query = query.filter(APIKey.expires_at.is_(None))
    if expired is not None:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        if expired:
            query = query.filter(APIKey.expires_at.isnot(None), APIKey.expires_at < now)
        else:
            # Not expired includes unlimited (null) or in future
            query = query.filter(
                or_(APIKey.expires_at.is_(None), APIKey.expires_at >= now)
            )
    query = query.order_by(direction(sort_col))
    total = query.count()

    if page and page_size:
        offset = max(page - 1, 0) * page_size
        query = query.offset(offset).limit(page_size)

    rows = query.all()
    return (
        [
            {
                "id": str(k.id),
                "user_id": str(k.user_id),
                "name": k.name,
                "role": k.role,
                "status": k.status,
                "last4": k.key_last4,
                "monthly_quota_tokens": k.monthly_token_quota,
                "daily_request_quota": k.daily_request_quota,
                "expires_at": k.expires_at.isoformat() if getattr(k, "expires_at", None) else None,
                "created_at": k.created_at.isoformat()
                if hasattr(k, "created_at") and k.created_at
                else None,
            }
            for k in rows
        ],
        total,
    )


def list_keys_for_user(db: Session, user_id: str) -> List[Dict[str, Any]]:
    rows = db.query(APIKey).filter(APIKey.user_id == user_id).order_by(desc(APIKey.created_at)).all()
    return [
        {
            "id": str(k.id),
            "user_id": str(k.user_id),
            "name": k.name,
            "role": k.role,
            "status": k.status,
            "last4": k.key_last4,
            "monthly_quota_tokens": k.monthly_token_quota,
            "daily_request_quota": k.daily_request_quota,
            "expires_at": k.expires_at.isoformat() if getattr(k, "expires_at", None) else None,
            "created_at": k.created_at.isoformat() if hasattr(k, "created_at") and k.created_at else None,
        }
        for k in rows
    ]


def revoke_key(db: Session, key_id: str) -> Dict[str, Any]:
    rec: APIKey = db.query(APIKey).get(key_id)
    if not rec:
        raise ValueError("key not found")
    rec.status = "revoked"
    db.commit()
    db.refresh(rec)
    return {
        "id": str(rec.id),
        "user_id": str(rec.user_id),
        "name": rec.name,
        "role": rec.role,
        "status": rec.status,
        "last4": rec.key_last4,
        "monthly_quota_tokens": rec.monthly_token_quota,
        "daily_request_quota": rec.daily_request_quota,
        "created_at": rec.created_at.isoformat() if hasattr(rec, "created_at") and rec.created_at else None,
    }


def rotate_key(db: Session, key_id: str) -> Dict[str, Any]:
    rec: APIKey = db.query(APIKey).get(key_id)
    if not rec:
        raise ValueError("key not found")
    rec.status = "revoked"
    db.add(rec)
    plaintext = secrets.token_urlsafe(32)
    new = APIKey(
        user_id=rec.user_id,
        name=rec.name,
        key_hash=hash_key(plaintext),
        key_last4=plaintext[-4:],
        role=rec.role,
        status="active",
        monthly_token_quota=rec.monthly_token_quota,
        daily_request_quota=rec.daily_request_quota,
        expires_at=getattr(rec, "expires_at", None),
    )
    db.add(new)
    db.commit()
    db.refresh(new)
    return {"id": str(new.id), "last4": new.key_last4, "plaintext_key": plaintext}


def audit(db: Session, actor_key_id: Optional[str], action: str, target_id: Optional[str], meta: Optional[dict] = None) -> None:
    def _as_uuid(value: Optional[str]) -> Optional[uuid.UUID]:
        if not value:
            return None
        try:
            return uuid.UUID(str(value))
        except Exception:
            return None

    rec = Audit(
        actor_key_id=_as_uuid(actor_key_id),
        action=action,
        target_id=_as_uuid(target_id),
        meta=meta or {},
    )
    db.add(rec)
    db.commit()
