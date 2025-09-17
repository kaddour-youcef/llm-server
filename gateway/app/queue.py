import asyncio
from typing import Any, Dict, Optional
from .config import settings
from . import vllm_client


_queue: asyncio.Queue = asyncio.Queue(maxsize=settings.queue_max_size)
_sem: asyncio.Semaphore = asyncio.Semaphore(settings.vllm_max_concurrency)


class Job:
    def __init__(self, payload: Dict[str, Any], stream: bool = False):
        self.payload = payload
        self._stream = stream
        self._event = asyncio.Event()
        self._result: Optional[Dict[str, Any]] = None
        self._stream_q: Optional[asyncio.Queue] = asyncio.Queue() if stream else None

    async def set_result(self, result: Dict[str, Any]):
        self._result = result
        self._event.set()

    async def result(self) -> Dict[str, Any]:
        await self._event.wait()
        return self._result or {}

    async def stream(self):
        if not self._stream_q:
            # Not a streaming job
            return
        while True:
            chunk = await self._stream_q.get()
            if chunk is None:
                self._stream_q.task_done()
                break
            yield chunk
            self._stream_q.task_done()


async def enqueue_job(endpoint: str, body: Dict[str, Any], principal: Any, stream: bool = False) -> Job:
    job = Job({"endpoint": endpoint, "body": body, "principal": principal.model_dump()}, stream=stream)
    await _queue.put(job)
    return job


def start_dispatcher() -> None:
    loop = asyncio.get_event_loop()
    loop.create_task(_dispatcher())


async def _dispatcher():
    while True:
        job: Job = await _queue.get()
        async with _sem:
            endpoint = job.payload.get("endpoint")
            body = job.payload.get("body")
            if endpoint == "/v1/chat/completions":
                if job._stream_q is not None:
                    # stream mode
                    try:
                        async for chunk in vllm_client.stream_chat_completions(body):
                            await job._stream_q.put(chunk)
                    finally:
                        await job._stream_q.put(None)
                else:
                    result = await vllm_client.chat_completions(body)
                    await job.set_result(result)
            else:
                # Unknown endpoint; return error-shaped result
                await job.set_result({"error": {"message": "unsupported endpoint"}})
        _queue.task_done()
