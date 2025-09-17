from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .config import settings
from .models import User, APIKey, Audit
from .security import hash_key
import secrets
from typing import Optional, List, Dict, Any
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
def create_user(db: Session, name: str, email: Optional[str]) -> Dict[str, Any]:
    user = User(name=name, email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": str(user.id), "name": user.name, "email": user.email}


def list_users(db: Session) -> List[Dict[str, Any]]:
    rows = db.query(User).all()
    return [{"id": str(u.id), "name": u.name, "email": u.email} for u in rows]


def create_api_key(
    db: Session,
    user_id: str,
    name: str,
    role: str = "user",
    monthly_quota_tokens: Optional[int] = None,
    daily_request_quota: Optional[int] = None,
) -> Dict[str, Any]:
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
        "plaintext_key": plaintext,
    }


def list_keys(db: Session) -> List[Dict[str, Any]]:
    rows = db.query(APIKey).all()
    return [
        {
            "id": str(k.id),
            "user_id": str(k.user_id),
            "name": k.name,
            "role": k.role,
            "status": k.status,
            "last4": k.key_last4,
        }
        for k in rows
    ]


def revoke_key(db: Session, key_id: str) -> Dict[str, Any]:
    rec: APIKey = db.query(APIKey).get(key_id)
    if not rec:
        raise ValueError("key not found")
    rec.status = "revoked"
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return {"id": str(rec.id), "status": rec.status}


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
