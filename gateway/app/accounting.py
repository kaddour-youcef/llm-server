from typing import Any, Dict, Optional
from datetime import datetime, timezone
from sqlalchemy import text
from .db import get_session


def _extract_usage(resp: Dict[str, Any]) -> Dict[str, int]:
    usage = resp.get("usage") or {}
    return {
        "prompt_tokens": int(usage.get("prompt_tokens") or 0),
        "completion_tokens": int(usage.get("completion_tokens") or 0),
        "total_tokens": int(usage.get("total_tokens") or 0),
    }


async def record_request(
    key_id: str,
    user_id: str,
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
                    key_id, user_id, endpoint, model, request_body, response_body, status_code, error_message,
                    prompt_tokens, completion_tokens, total_tokens, latency_ms, created_at
                ) VALUES (
                    :key_id, :user_id, :endpoint, :model, :request_body, :response_body, :status_code, :error_message,
                    :prompt_tokens, :completion_tokens, :total_tokens, :latency_ms, now()
                )
                """
            ),
            {
                "key_id": key_id,
                "user_id": user_id,
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

        db.commit()

