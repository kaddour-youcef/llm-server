from typing import Any, Dict, AsyncGenerator
import httpx
from .config import settings

class UpstreamHTTPError(Exception):
    def __init__(self, status_code: int, message: str, body: Any = None):
        super().__init__(f"{status_code}: {message}")
        self.status_code = status_code
        self.message = message
        self.body = body

async def chat_completions(payload: Dict[str, Any]) -> Dict[str, Any]:
    # Ensure we don't accidentally stream in non-stream path
    payload = dict(payload)
    payload.pop("stream", None)
    async with httpx.AsyncClient(timeout=settings.vllm_timeout_s) as client:
        r = await client.post(f"{settings.vllm_url}/v1/chat/completions", json=payload)
        if r.status_code >= 400:
            # propagate error details so the route can return a proper HTTP error
            body = None
            try:
                body = r.json()
                message = body.get("error", {}).get("message") or body
            except Exception:
                message = r.text
            raise UpstreamHTTPError(r.status_code, str(message), body=body)
        return r.json()

async def stream_chat_completions(payload: Dict[str, Any]) -> AsyncGenerator[bytes, None]:
    payload = dict(payload)
    payload["stream"] = True
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", f"{settings.vllm_url}/v1/chat/completions", json=payload) as r:
            if r.status_code >= 400:
                # Create a single SSE error frame then stop
                text = await r.aread()
                msg = text.decode("utf-8", errors="replace")
                err = f"event: error\ndata: {{\"status\": {r.status_code}, \"message\": {msg!r}}}\n\n"
                yield err.encode("utf-8")
                return
            async for chunk in r.aiter_raw():
                if not chunk:
                    continue
                # Pass through vLLM's SSE bytes
                yield chunk
