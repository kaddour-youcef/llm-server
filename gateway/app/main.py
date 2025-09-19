from fastapi import FastAPI
from .routes import public, admin
from .metrics import metrics_router
from .db import init_db
from .queue import start_dispatcher, stop_dispatcher
from .logging import setup_logging
from fastapi.middleware.cors import CORSMiddleware
import os

setup_logging()
app = FastAPI(title="LLM Gateway")


# Build CORS origins from env (supports comma-separated list) with sensible defaults
_default_admin_origin = "http://llm-server-admin:8181"
origins_set: set[str] = {"http://localhost:8181"}

# Backward-compat: single origin or comma-separated list in ADMIN_ORIGIN
_single_or_many = os.getenv("ADMIN_ORIGIN")
if _single_or_many:
    for item in _single_or_many.split(","):
        if item and item.strip():
            origins_set.add(item.strip())

# Preferred: comma-separated list in ADMIN_ORIGINS
_many = os.getenv("ADMIN_ORIGINS")
if _many:
    for item in _many.split(","):
        if item and item.strip():
            origins_set.add(item.strip())

# Fallback to in-cluster hostname to preserve previous behavior
if not _single_or_many and not _many:
    origins_set.add(_default_admin_origin)

allow_origin_regex = os.getenv("ALLOW_ORIGIN_REGEX")  # e.g. ^https?://(localhost|192\.168\.1\.[0-9]+):\d+$
origins = sorted(origins_set)



# Allow your Next.js frontend to talk to the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],  # or ["GET", "POST", "OPTIONS"] if you want to restrict
    allow_headers=["*"],  # allows x-api-key, authorization, etc.
)


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
