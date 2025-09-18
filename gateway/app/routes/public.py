from fastapi import APIRouter, Depends, HTTPException
from starlette.responses import StreamingResponse, JSONResponse
from ..auth import require_key, Principal
from ..schemas import ChatCompletionRequest
from ..ratelimit import check_rate_limit
from ..queue import enqueue_job
from ..accounting import record_request
import asyncio
import time

router = APIRouter()

@router.get("/v1/models")
async def list_models():
    # Closer to OpenAI spec (optional, but nice)
    return {"object": "list", "data": [{"id": "default", "object": "model"}]}

@router.post("/v1/chat/completions")
async def chat_completions(body: ChatCompletionRequest, principal: Principal = Depends(require_key)):
    await check_rate_limit(principal.key_id)

    started = time.time()
    job = await enqueue_job(
        endpoint="/v1/chat/completions",
        body=body.model_dump(),
        principal=principal,
        stream=bool(body.stream),
    )

    # STREAMING
    if body.stream:
        async def _gen():
            try:
                async for chunk in job.stream():
                    # Pass-through SSE from vLLM (already framed)
                    yield chunk
            finally:
                # best effort accounting for streamed requests (latency only)
                try:
                    latency_ms = int((time.time() - started) * 1000)
                    await record_request(
                        key_id=principal.key_id,
                        user_id=principal.user_id,
                        endpoint="/v1/chat/completions",
                        model=(body.model or None),
                        request_body=body.model_dump(),
                        response_body=None,
                        status_code=200,
                        error_message=None,
                        latency_ms=latency_ms,
                    )
                except Exception:
                    pass

        # Disable proxy buffering (nginx) and keep SSE semantics explicit
        headers = {
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
        return StreamingResponse(_gen(), media_type="text/event-stream", headers=headers)

    # NON-STREAMING
    try:
        # Optional: put a sensible ceiling to avoid hanging forever
        result = await asyncio.wait_for(job.result(), timeout=body.timeout_s if hasattr(body, "timeout_s") else 300)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Upstream timeout")

    latency_ms = int((time.time() - started) * 1000)
    status_code = 200
    error_message = None

    # If dispatcher surfaced an error, translate to HTTP error
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
        response_body=result,
        status_code=status_code,
        error_message=error_message,
        latency_ms=latency_ms,
    )
    return JSONResponse(result, status_code=status_code)
