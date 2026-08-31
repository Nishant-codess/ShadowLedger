"""ShadowLedger API Service."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    batches_router,
    cases_router,
    health_router,
    metrics_router,
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
app.include_router(metrics_router)


@app.get("/")
def root():
    return {
        "project": "ShadowLedger",
        "description": "Value-flow reconstruction engine for finance operations",
        "version": "0.1.0",
        "docs_url": "/docs",
    }
