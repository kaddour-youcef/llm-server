# app/routes/public.py

import logging
import json
import time
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from starlette.responses import StreamingResponse, JSONResponse

from ..auth import require_key, Principal
from ..types import ChatCompletionRequest
from ..ratelimit import check_rate_limit
from ..queue import enqueue_job
from ..accounting import record_request

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/v1/models")
async def list_models():
    logger.debug("GET /v1/models called")
    return {"object": "list", "data": [{"id": "default", "object": "model"}]}


@router.post("/v1/chat/completions")
async def chat_completions(
    body: ChatCompletionRequest, principal: Principal = Depends(require_key)
):
    logger.info(
        "POST /v1/chat/completions called for key_id=%s user_id=%s stream=%s",
        principal.key_id,
        principal.user_id,
        body.stream,
    )

    await check_rate_limit(principal.key_id)

    started = time.time()
    job = await enqueue_job(
        endpoint="/v1/chat/completions",
        body=body.model_dump(),
        principal=principal,
        stream=bool(body.stream),
    )

    # STREAMING MODE
    if body.stream:
        logger.info("Streaming mode enabled")

        async def _gen():
            last_with_usage = None
            try:
                async for chunk in job.stream():
                    # Forward raw SSE chunk to client
                    yield chunk

                    # Try to parse JSON from SSE "data:" lines
                    try:
                        text_chunk = chunk.decode("utf-8").strip()
                        if text_chunk.startswith("data: "):
                            payload = text_chunk[len("data: "):].strip()
                            if payload != "[DONE]":
                                parsed = json.loads(payload)
                                if "usage" in parsed:
                                    last_with_usage = parsed
                    except Exception:
                        # Ignore parse errors — keep streaming
                        pass
            finally:
                try:
                    latency_ms = int((time.time() - started) * 1000)
                    logger.info(
                        "Finalizing streamed request with latency_ms=%d", latency_ms
                    )
                    await record_request(
                        key_id=principal.key_id,
                        user_id=principal.user_id,
                        endpoint="/v1/chat/completions",
                        model=(body.model or None),
                        request_body=body.model_dump(),
                        response_body=last_with_usage,  # ✅ usage if present
                        status_code=200,
                        error_message=None,
                        latency_ms=latency_ms,
                    )
                except Exception as e:
                    logger.exception("Error recording streamed request: %s", e)

        headers = {
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
        return StreamingResponse(
            _gen(), media_type="text/event-stream", headers=headers
        )

    # NON-STREAMING MODE
    try:
        logger.debug("Waiting for job result...")
        result = await asyncio.wait_for(
            job.result(),
            timeout=body.timeout_s if hasattr(body, "timeout_s") else 300,
        )
        logger.debug("Job result received: %s", result)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Upstream timeout")

    latency_ms = int((time.time() - started) * 1000)
    status_code = 200
    error_message = None

    if isinstance(result, dict) and result.get("__error__"):
        status_code = int(result.get("status_code", 502))
        error_message = result.get("message", "Upstream error")
        await record_request(
            key_id=principal.key_id,
            user_id=principal.user_id,
            endpoint="/v1/chat/completions",
            model=(body.model or None),
            request_body=body.model_dump(),
            response_body=result,
            status_code=status_code,
            error_message=error_message,
            latency_ms=latency_ms,
        )
        raise HTTPException(status_code=status_code, detail=error_message)

    await record_request(
        key_id=principal.key_id,
        user_id=principal.user_id,
        endpoint="/v1/chat/completions",
        model=(body.model or None),
        request_body=body.model_dump(),
        response_body=result,  # ✅ includes usage if backend provides it
        status_code=status_code,
        error_message=error_message,
        latency_ms=latency_ms,
    )
    return JSONResponse(result, status_code=status_code)
