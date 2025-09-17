from pydantic import BaseModel
import os


class Settings(BaseModel):
    vllm_url: str = os.getenv("VLLM_URL", "http://localhost:8000")
    vllm_timeout_s: int = int(os.getenv("VLLM_TIMEOUT_S", "120"))
    vllm_max_concurrency: int = int(os.getenv("VLLM_MAX_CONCURRENCY", "8"))
    queue_max_size: int = int(os.getenv("QUEUE_MAX_SIZE", "2048"))
    batch_max_latency_ms: int = int(os.getenv("BATCH_MAX_LATENCY_MS", "10"))

    database_url: str = os.getenv("DATABASE_URL", "postgresql+psycopg://gateway:gateway_password@localhost:5432/gateway")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    admin_origin: str = os.getenv("ADMIN_ORIGIN", "http://localhost:8501")
    display_model_name: str = os.getenv("DISPLAY_MODEL_NAME", "")

    rate_limit_rps_default: int = int(os.getenv("RATE_LIMIT_RPS_DEFAULT", "10"))
    rate_limit_burst_default: int = int(os.getenv("RATE_LIMIT_BURST_DEFAULT", "20"))

    admin_bootstrap_key: str | None = os.getenv("ADMIN_BOOTSTRAP_KEY")


settings = Settings()

