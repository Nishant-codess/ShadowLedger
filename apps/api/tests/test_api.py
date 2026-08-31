"""API integration tests for all FastAPI endpoints."""

from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient):
    """GET /health returns 200 and system metadata."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["engine"] == "deterministic_baseline"


def test_batch_process_endpoint(client: TestClient):
    """POST /api/batches/process ingests and processes a synthetic batch."""
    payload = {"seed": 42, "rows": 50, "batch_id": "test_api_batch"}
    res = client.post("/api/batches/process", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["batch_id"] == "test_api_batch"
    assert data["record_count"] == 50
    assert "match_rate" in data
    assert "throughput_records_per_sec" in data
    assert "reason_code_breakdown" in data


def test_list_batches_endpoint(client: TestClient):
    """GET /api/batches returns list of processed batches."""
    res = client.get("/api/batches")
    assert res.status_code == 200
    batches = res.json()
    assert isinstance(batches, list)
    assert len(batches) >= 1


def test_cases_endpoint(client: TestClient):
    """GET /api/cases returns discrepancy cases from processed batches."""
    res = client.get("/api/cases?batch_id=test_api_batch")
    assert res.status_code == 200
    cases = res.json()
    assert isinstance(cases, list)
    if cases:
        case_id = cases[0]["case_id"]
        res_single = client.get(f"/api/cases/{case_id}")
        assert res_single.status_code == 200
        case_detail = res_single.json()
        assert case_detail["case_id"] == case_id
        assert "observations" in case_detail


def test_metrics_endpoint(client: TestClient):
    """GET /api/metrics returns latest performance metrics."""
    res = client.get("/api/metrics")
    assert res.status_code == 200
    metrics = res.json()
    assert metrics["status"] == "ready"
    assert "match_rate" in metrics
    assert "total_volume_inr" in metrics
