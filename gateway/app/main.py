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


origins = [
    "http://localhost:3000",
    os.getenv("ADMIN_ORIGIN", "http://llm-server-admin:3000"),
]


# Allow your Next.js frontend to talk to the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
