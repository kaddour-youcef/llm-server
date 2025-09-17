import asyncio
from typing import Any, Dict
from .config import settings


_queue: asyncio.Queue = asyncio.Queue(maxsize=settings.queue_max_size)
_sem: asyncio.Semaphore = asyncio.Semaphore(settings.vllm_max_concurrency)


class Job:
    def __init__(self, payload: Dict[str, Any], stream: bool = False):
        self.payload = payload
        self._stream = stream
        self._event = asyncio.Event()
        self._result: Dict[str, Any] | None = None

    async def set_result(self, result: Dict[str, Any]):
        self._result = result
        self._event.set()

    async def result(self) -> Dict[str, Any]:
        await self._event.wait()
        return self._result or {}

    async def stream(self):
        # Placeholder streaming generator
        yield b"data: [streaming not implemented in skeleton]\n\n"


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
            # In the skeleton, echo back a minimal OpenAI-compatible shape
            await asyncio.sleep(0.01)
            await job.set_result({
                "id": "chatcmpl-skeleton",
                "object": "chat.completion",
                "choices": [
                    {"index": 0, "message": {"role": "assistant", "content": "[skeleton response]"}, "finish_reason": "stop"}
                ],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            })
        _queue.task_done()

