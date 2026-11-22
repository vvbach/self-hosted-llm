
import time
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Request
from prometheus_client import (
    Counter,
    Histogram,
    make_asgi_app,
)

from app.classifier import (
    Classifier,
    InvalidLLMResponse,
    LLMTimeout,
    LLMUnavailable,
)
from app.config import settings
from app.schema import (
    ClassificationRequest,
    ClassificationResponse,
)


REQUESTS = Counter(
    "classification_requests_total",
    "Total classification requests",
    ["status"],
)

LATENCY = Histogram(
    "classification_latency_seconds",
    "Classification request latency",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with httpx.AsyncClient() as client:
        app.state.client = client
        app.state.classifier = Classifier(client)
        yield


app = FastAPI(
    title="Self-hosted LLM Error Classifier",
    version="1.0.0",
    lifespan=lifespan,
)

app.mount("/metrics", make_asgi_app())


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/ready")
async def ready(request: Request):
    health_url = settings.LLM_URL.replace("/v1/chat/completions", "/health")

    try:
        response = await request.app.state.client.get(
            health_url,
            timeout=5,
        )
        response.raise_for_status()

        if response.json().get("status") != "ok":
            raise ValueError("Model is not ready")

        return {"status": "ready"}

    except (httpx.HTTPError, ValueError):
        raise HTTPException(
            status_code=503,
            detail="LLM not ready",
        )


@app.post("/api/v1/classify", response_model=ClassificationResponse)
async def classify(
    payload: ClassificationRequest,
    request: Request,
):
    start = time.perf_counter()
    status = "success"

    try:
        return await request.app.state.classifier.classify(payload.error)

    except LLMTimeout:
        status = "timeout"
        raise HTTPException(
            status_code=504,
            detail="LLM timeout",
        )

    except (LLMUnavailable, InvalidLLMResponse):
        status = "error"
        raise HTTPException(
            status_code=502,
            detail="LLM inference failed",
        )

    finally:
        REQUESTS.labels(status=status).inc()
        LATENCY.observe(time.perf_counter() - start)
