from fastapi import APIRouter, Depends, HTTPException
from starlette.responses import StreamingResponse, JSONResponse
from ..auth import require_key, Principal
from ..schemas import ChatCompletionRequest
from ..ratelimit import check_rate_limit
from ..queue import enqueue_job

router = APIRouter()


@router.get("/v1/models")
async def list_models():
    return {"data": [{"id": "default", "object": "model"}]}


@router.post("/v1/chat/completions")
async def chat_completions(body: ChatCompletionRequest, principal: Principal = Depends(require_key)):
    await check_rate_limit(principal.key_id)
    job = await enqueue_job(endpoint="/v1/chat/completions", body=body.model_dump(), principal=principal, stream=body.stream or False)
    if body.stream:
        return StreamingResponse(job.stream(), media_type="text/event-stream")
    result = await job.result()
    return JSONResponse(result)

