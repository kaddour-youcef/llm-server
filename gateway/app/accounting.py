from typing import Any, Dict, Optional
from datetime import datetime, timezone
from sqlalchemy import text
from .db import get_session
from fastapi import HTTPException, status
from datetime import date as _date


def _extract_usage(resp: Dict[str, Any]) -> Dict[str, int]:
    usage = resp.get("usage") or {}
    return {
        "prompt_tokens": int(usage.get("prompt_tokens") or 0),
        "completion_tokens": int(usage.get("completion_tokens") or 0),
        "total_tokens": int(usage.get("total_tokens") or 0),
    }


async def enforce_org_quota(organization_id: str) -> None:
    """Ensure the organization's monthly token quota has not been exceeded."""
    with get_session() as db:
        # Load quota
        row = db.execute(
            text("SELECT monthly_token_quota FROM organizations WHERE id = :org_id"),
            {"org_id": organization_id},
        ).fetchone()
        if not row or not row.monthly_token_quota:
            return  # No quota set

        # Sum usage for current month
        today = _date.today()
        start = today.replace(day=1)
        total = db.execute(
            text(
                """
                SELECT COALESCE(SUM(total_tokens),0) AS total
                FROM api_usage
                WHERE organization_id = :org_id
                  AND day BETWEEN :start AND :end
                """
            ),
            {"org_id": organization_id, "start": start, "end": today},
        ).fetchone()
        used = int(total.total or 0)
        if used >= int(row.monthly_token_quota):
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Organization token quota exceeded")


async def record_request(
    *,
    key_id: str,
    organization_id: str,
    owner_type: str,
    owner_id: str,
    user_id: Optional[str],
    endpoint: str,
    model: Optional[str],
    request_body: Dict[str, Any],
    response_body: Optional[Dict[str, Any]],
    status_code: Optional[int],
    error_message: Optional[str],
    latency_ms: Optional[int],
) -> None:
    usage = _extract_usage(response_body or {})
    now = datetime.now(timezone.utc)
    day = now.date()
    with get_session() as db:
        db.execute(
            text(
                """
                INSERT INTO requests (
                    key_id, user_id, organization_id, owner_type, owner_id,
                    endpoint, model, request_body, response_body, status_code, error_message,
                    prompt_tokens, completion_tokens, total_tokens, latency_ms, created_at
                ) VALUES (
                    :key_id, :user_id, :organization_id, :owner_type, :owner_id,
                    :endpoint, :model, :request_body, :response_body, :status_code, :error_message,
                    :prompt_tokens, :completion_tokens, :total_tokens, :latency_ms, now()
                )
                """
            ),
            {
                "key_id": key_id,
                "user_id": user_id,
                "organization_id": organization_id,
                "owner_type": owner_type,
                "owner_id": owner_id,
                "endpoint": endpoint,
                "model": model,
                "request_body": request_body,
                "response_body": response_body,
                "status_code": status_code,
                "error_message": error_message,
                "prompt_tokens": usage["prompt_tokens"],
                "completion_tokens": usage["completion_tokens"],
                "total_tokens": usage["total_tokens"],
                "latency_ms": latency_ms,
            },
        )

        # Back-compat rollup keyed by key/day
        db.execute(
            text(
                """
                INSERT INTO usage_rollups (
                    key_id, user_id, day, request_count, prompt_tokens, completion_tokens, total_tokens
                ) VALUES (
                    :key_id, :user_id, :day, 1, :prompt_tokens, :completion_tokens, :total_tokens
                )
                ON CONFLICT (key_id, day) DO UPDATE SET
                    request_count = usage_rollups.request_count + EXCLUDED.request_count,
                    prompt_tokens = usage_rollups.prompt_tokens + EXCLUDED.prompt_tokens,
                    completion_tokens = usage_rollups.completion_tokens + EXCLUDED.completion_tokens,
                    total_tokens = usage_rollups.total_tokens + EXCLUDED.total_tokens
                """
            ),
            {
                "key_id": key_id,
                "user_id": user_id,
                "day": day,
                "prompt_tokens": usage["prompt_tokens"],
                "completion_tokens": usage["completion_tokens"],
                "total_tokens": usage["total_tokens"],
            },
        )

        # New analytics table with full ownership + org breakdown
        db.execute(
            text(
                """
                INSERT INTO api_usage (
                    organization_id, owner_type, owner_id, key_id, day, request_count, prompt_tokens, completion_tokens, total_tokens
                ) VALUES (
                    :organization_id, :owner_type, :owner_id, :key_id, :day, 1, :prompt_tokens, :completion_tokens, :total_tokens
                )
                ON CONFLICT (organization_id, owner_type, owner_id, key_id, day) DO UPDATE SET
                    request_count = api_usage.request_count + EXCLUDED.request_count,
                    prompt_tokens = api_usage.prompt_tokens + EXCLUDED.prompt_tokens,
                    completion_tokens = api_usage.completion_tokens + EXCLUDED.completion_tokens,
                    total_tokens = api_usage.total_tokens + EXCLUDED.total_tokens
                """
            ),
            {
                "organization_id": organization_id,
                "owner_type": owner_type,
                "owner_id": owner_id,
                "key_id": key_id,
                "day": day,
                "prompt_tokens": usage["prompt_tokens"],
                "completion_tokens": usage["completion_tokens"],
                "total_tokens": usage["total_tokens"],
            },
        )

        db.commit()
