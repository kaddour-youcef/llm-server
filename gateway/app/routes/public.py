from fastapi import APIRouter, Depends
from starlette.responses import StreamingResponse, JSONResponse
from ..auth import require_key, Principal
from ..schemas import ChatCompletionRequest
from ..ratelimit import check_rate_limit
from ..queue import enqueue_job
from ..accounting import record_request
import time

router = APIRouter()


@router.get("/v1/models")
async def list_models():
    return {"data": [{"id": "default", "object": "model"}]}


@router.post("/v1/chat/completions")
async def chat_completions(body: ChatCompletionRequest, principal: Principal = Depends(require_key)):
    await check_rate_limit(principal.key_id)
    started = time.time()
    job = await enqueue_job(endpoint="/v1/chat/completions", body=body.model_dump(), principal=principal, stream=body.stream or False)
    if body.stream:
        # TODO: accounting for streaming once final usage is known
        return StreamingResponse(job.stream(), media_type="text/event-stream")
    result = await job.result()
    latency_ms = int((time.time() - started) * 1000)
    # Fire-and-forget accounting; no await needed, but keep simple for now
    await record_request(
        key_id=principal.key_id,
        user_id=principal.user_id,
        endpoint="/v1/chat/completions",
        model=(body.model or None),
        request_body=body.model_dump(),
        response_body=result,
        status_code=200,
        error_message=None,
        latency_ms=latency_ms,
    )
    return JSONResponse(result)
