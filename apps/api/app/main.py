import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure repository root is on sys.path regardless of execution working directory
repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from app.api.routes import (  # noqa: E402
    batches_router,
    cases_router,
    demo_router,
    health_router,
    metrics_router,
    patterns_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown hooks."""
    # Ensure startup initialization
    yield


app = FastAPI(
    title="ShadowLedger API",
    version="0.1.0",
    description="Value-flow reconstruction engine for financial operations (Razorpay Track 04)",
    lifespan=lifespan,
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount endpoints
app.include_router(health_router)
app.include_router(batches_router)
app.include_router(cases_router)
app.include_router(demo_router)
app.include_router(metrics_router)
app.include_router(patterns_router)


@app.get("/")
def root():
    return {
        "project": "ShadowLedger",
        "description": "Value-flow reconstruction engine for finance operations",
        "version": "0.1.0",
        "docs_url": "/docs",
    }
