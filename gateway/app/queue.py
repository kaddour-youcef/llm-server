import asyncio
from typing import Any, Dict, Optional, AsyncGenerator
from .config import settings
from . import vllm_client

_queue: asyncio.Queue = asyncio.Queue(maxsize=settings.queue_max_size)
_sem: asyncio.Semaphore = asyncio.Semaphore(settings.vllm_max_concurrency)
_shutdown_event = asyncio.Event()

class Job:
    def __init__(self, payload: Dict[str, Any], stream: bool = False):
        self.payload = payload
        self._stream = stream
        self._event = asyncio.Event()
        self._result: Optional[Dict[str, Any]] = None
        self._stream_q: Optional[asyncio.Queue] = asyncio.Queue() if stream else None

    def set_result(self, result: Dict[str, Any]) -> None:
        self._result = result
        self._event.set()

    async def result(self) -> Dict[str, Any]:
        await self._event.wait()
        return self._result or {}

    async def stream(self) -> AsyncGenerator[bytes, None]:
        if not self._stream_q:
            return
        while True:
            chunk = await self._stream_q.get()
            try:
                if chunk is None:
                    break
                yield chunk
            finally:
                self._stream_q.task_done()

async def enqueue_job(endpoint: str, body: Dict[str, Any], principal: Any, stream: bool = False) -> Job:
    job = Job({"endpoint": endpoint, "body": body, "principal": principal.model_dump()}, stream=stream)
    await _queue.put(job)
    return job

# --- Dispatcher lifecycle

_dispatcher_task: Optional[asyncio.Task] = None

def start_dispatcher() -> asyncio.Task:
    # Use the currently running loop; don't construct a new one
    task = asyncio.create_task(_dispatcher(), name="vllm-dispatcher")
    global _dispatcher_task
    _dispatcher_task = task
    return task

async def stop_dispatcher(task: Optional[asyncio.Task]) -> None:
    _shutdown_event.set()
    # Let the dispatcher exit gracefully
    if task:
        try:
            await asyncio.wait_for(task, timeout=5)
        except asyncio.TimeoutError:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

async def _dispatcher():
    while not _shutdown_event.is_set():
        try:
            job: Job = await asyncio.wait_for(_queue.get(), timeout=0.2)
        except asyncio.TimeoutError:
            continue

        try:
            async with _sem:
                endpoint = job.payload.get("endpoint")
                body = job.payload.get("body")

                if endpoint == "/v1/chat/completions":
                    if job._stream_q is not None:
                        # stream mode
                        try:
                            async for chunk in vllm_client.stream_chat_completions(body):
                                await job._stream_q.put(chunk)
                        except Exception as e:
                            # Surface streaming error as a terminal SSE error frame
                            err = f"event: error\ndata: {{" \
                                  f"\"message\": \"{type(e).__name__}: {str(e)}\"}}\n\n"
                            await job._stream_q.put(err.encode("utf-8"))
                        finally:
                            # Signal end of stream
                            await job._stream_q.put(None)
                    else:
                        try:
                            result = await vllm_client.chat_completions(body)
                        except vllm_client.UpstreamHTTPError as e:
                            job.set_result({
                                "__error__": True,
                                "message": e.message,
                                "status_code": e.status_code,
                                "body": e.body,
                            })
                        except Exception as e:
                            job.set_result({
                                "__error__": True,
                                "message": f"{type(e).__name__}: {str(e)}",
                                "status_code": 502,
                            })
                        else:
                            job.set_result(result)
                else:
                    job.set_result({"__error__": True, "message": "unsupported endpoint", "status_code": 404})
        finally:
            _queue.task_done()
