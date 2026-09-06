import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

curr = Path(__file__).resolve()
repo_root = next((p for p in curr.parents if (p / "scripts").is_dir()), curr.parent.parent.parent.parent)
api_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
if str(api_root) not in sys.path:
    sys.path.insert(0, str(api_root))

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from app.api.routes import (  # noqa: E402
    batches_router,
    cases_router,
    chat_router,
    demo_router,
    health_router,
    metrics_router,
    patterns_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown hooks."""
    # Ensure startup pre-seeding so cases, patterns, and metrics are ready immediately
    from app.api.routes.batches import get_case_repo, get_obs_repo
    from app.api.routes.demo import run_hero_demo

    obs_repo = get_obs_repo()
    case_repo = get_case_repo()
    try:
        run_hero_demo("hero_c", obs_repo, case_repo)
        run_hero_demo("hero_b", obs_repo, case_repo)
        run_hero_demo("hero_a", obs_repo, case_repo)
    except Exception as e:
        print(f"Startup demo pre-seed warning: {e}")
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
app.include_router(chat_router)
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
