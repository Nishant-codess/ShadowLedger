"""Health check endpoint."""

from fastapi import APIRouter

from app.api.schemas.api_models import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """Service health and engine status probe."""
    return HealthResponse()
