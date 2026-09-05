"""API routers export."""

from app.api.routes.batches import router as batches_router
from app.api.routes.cases import router as cases_router
from app.api.routes.chat import router as chat_router
from app.api.routes.demo import router as demo_router
from app.api.routes.health import router as health_router
from app.api.routes.metrics import router as metrics_router
from app.api.routes.patterns import router as patterns_router

__all__ = [
    "health_router",
    "batches_router",
    "cases_router",
    "chat_router",
    "demo_router",
    "metrics_router",
    "patterns_router",
]
