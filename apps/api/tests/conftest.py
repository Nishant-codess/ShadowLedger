"""Pytest fixtures and test configuration."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

repo_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "apps" / "api"))

from app.engine.reconciler import DeterministicReconciler  # noqa: E402
from app.main import app  # noqa: E402
from app.persistence.case_repo import CaseRepository  # noqa: E402
from app.persistence.database import DatabaseManager  # noqa: E402
from app.persistence.observation_repo import ObservationRepository  # noqa: E402


@pytest.fixture
def test_db():
    """In-memory DuckDB instance for isolated unit tests."""
    db = DatabaseManager(db_path=":memory:")
    yield db
    db.close()


@pytest.fixture
def obs_repo(test_db):
    return ObservationRepository(test_db)


@pytest.fixture
def case_repo(test_db):
    return CaseRepository(test_db)


@pytest.fixture
def reconciler():
    return DeterministicReconciler()


@pytest.fixture
def client():
    """FastAPI TestClient instance."""
    with TestClient(app) as c:
        yield c
