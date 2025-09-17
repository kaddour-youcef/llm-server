from fastapi import FastAPI
from .routes import public, admin
from .metrics import metrics_router
from .db import init_db
from .queue import start_dispatcher
from .logging import setup_logging


setup_logging()
app = FastAPI(title="LLM Gateway")

app.include_router(public.router, prefix="")
app.include_router(admin.router, prefix="/admin")
app.include_router(metrics_router)


@app.on_event("startup")
async def on_startup():
    await init_db()
    start_dispatcher()

