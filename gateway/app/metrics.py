from fastapi import APIRouter, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

metrics_router = APIRouter()

gateway_requests_total = Counter("gateway_requests_total", "Total requests", ["status", "endpoint"])
gateway_tokens_total = Counter("gateway_tokens_total", "Total tokens", ["key_id"])
gateway_queue_depth = Gauge("gateway_queue_depth", "Queue depth", ["endpoint"])
gateway_upstream_latency = Histogram("gateway_upstream_latency_seconds", "Upstream latency")
gateway_rl_exceeded = Counter("gateway_rate_limit_exceeded_total", "Rate limit exceeded")


@metrics_router.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

