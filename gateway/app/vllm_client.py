from typing import Any, Dict, AsyncGenerator
import httpx
from .config import settings


async def chat_completions(payload: Dict[str, Any]) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=settings.vllm_timeout_s) as client:
        r = await client.post(f"{settings.vllm_url}/v1/chat/completions", json=payload)
        r.raise_for_status()
        return r.json()


async def stream_chat_completions(payload: Dict[str, Any]) -> AsyncGenerator[bytes, None]:
    # Ensure stream flag is set for upstream
    payload = dict(payload)
    payload["stream"] = True
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", f"{settings.vllm_url}/v1/chat/completions", json=payload) as r:
            r.raise_for_status()
            async for chunk in r.aiter_raw():
                if not chunk:
                    continue
                yield chunk
