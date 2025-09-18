from fastapi import FastAPI
from .routes import public, admin
from .metrics import metrics_router
from .db import init_db
from .queue import start_dispatcher, stop_dispatcher
from .logging import setup_logging

setup_logging()
app = FastAPI(title="LLM Gateway")

app.include_router(public.router, prefix="")
app.include_router(admin.router, prefix="/admin")
app.include_router(metrics_router)

# Prefer lifespan to deprecated on_event hooks so background tasks are managed cleanly
from contextlib import asynccontextmanager
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    await init_db()
    dispatcher_task = start_dispatcher()  # returns asyncio.Task
    try:
        yield
    finally:
        # shutdown
        await stop_dispatcher(dispatcher_task)

app.router.lifespan_context = lifespan
