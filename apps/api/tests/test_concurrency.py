"""Concurrency regression tests for DuckDB thread safety and API resilience."""

import concurrent.futures
from decimal import Decimal

from fastapi.testclient import TestClient

from app.domain.models import BatchMetadata, Case
from app.persistence.case_repo import CaseRepository
from app.persistence.database import DatabaseManager
from app.persistence.observation_repo import ObservationRepository


def test_concurrent_metrics_requests(client: TestClient) -> None:
    """Requirement 1: Multiple concurrent GET /api/metrics calls must succeed without 500s."""
    # Ensure at least one batch exists
    client.post("/api/batches/process", json={"seed": 42, "rows": 20, "batch_id": "batch_conc_1"})

    def make_request() -> int:
        res = client.get("/api/metrics")
        return res.status_code

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(make_request) for _ in range(16)]
        results = [f.result() for f in futures]

    assert all(status == 200 for status in results)


def test_repeated_concurrent_cases_requests(client: TestClient) -> None:
    """Requirement 2: Repeated concurrent GET /api/cases calls must return consistent results."""
    client.post("/api/batches/process", json={"seed": 42, "rows": 30, "batch_id": "batch_conc_cases"})

    def fetch_cases() -> tuple[int, int]:
        res = client.get("/api/cases?batch_id=batch_conc_cases")
        return res.status_code, len(res.json())

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(fetch_cases) for _ in range(12)]
        results = [f.result() for f in futures]

    assert all(status == 200 for status, _ in results)
    case_counts = [count for _, count in results]
    assert len(set(case_counts)) == 1, "All concurrent reads must return identical case counts"


def test_repeated_concurrent_patterns_requests(client: TestClient) -> None:
    """Requirement 3: Repeated concurrent GET /api/patterns calls must return cleanly."""
    client.post("/api/batches/process", json={"seed": 42, "rows": 30, "batch_id": "batch_conc_patterns"})

    def fetch_patterns() -> int:
        res = client.get("/api/patterns?batch_id=batch_conc_patterns")
        return res.status_code

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(fetch_patterns) for _ in range(12)]
        results = [f.result() for f in futures]

    assert all(status == 200 for status in results)


def test_simultaneous_benchmark_requests_identical_parameters(client: TestClient) -> None:
    """Requirement 4: Two simultaneous benchmark requests with identical rows/seed execute safely."""
    def run_bm() -> tuple[int, str]:
        res = client.get("/api/metrics/benchmark?rows=10000&seed=42&force_refresh=false")
        return res.status_code, res.json().get("batch_id", "")

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        f1 = executor.submit(run_bm)
        f2 = executor.submit(run_bm)
        f3 = executor.submit(run_bm)
        res1, res2, res3 = f1.result(), f2.result(), f3.result()

    assert res1[0] == 200 and res2[0] == 200 and res3[0] == 200
    assert res1[1] == res2[1] == res3[1] == "benchmark_s42_r10000"


def test_metrics_while_benchmark_active(client: TestClient) -> None:
    """Requirement 5: Metrics requests during active benchmark execution must not fail or hang."""
    client.post("/api/batches/process", json={"seed": 42, "rows": 20, "batch_id": "batch_interleave"})

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        # Start benchmark in background thread
        bm_future = executor.submit(lambda: client.get("/api/metrics/benchmark?rows=10000&seed=42").status_code)
        # Simultaneously fire rapid metrics requests
        metrics_futures = [executor.submit(lambda: client.get("/api/metrics").status_code) for _ in range(10)]

        assert bm_future.result() == 200
        assert all(f.result() == 200 for f in metrics_futures)


def test_cases_request_while_batch_processing(client: TestClient) -> None:
    """Requirement 6: Cases/metrics requests during batch processing must succeed cleanly."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        # Launch batch processing
        batch_fut = executor.submit(
            lambda: client.post(
                "/api/batches/process",
                json={"seed": 99, "rows": 50, "batch_id": "batch_race_test"},
            ).status_code
        )
        # Simultaneously read cases and metrics
        read_futs = [
            executor.submit(lambda: client.get("/api/cases").status_code),
            executor.submit(lambda: client.get("/api/metrics").status_code),
            executor.submit(lambda: client.get("/api/patterns").status_code),
            executor.submit(lambda: client.get("/api/batches").status_code),
        ]

        assert batch_fut.result() == 200
        assert all(f.result() == 200 for f in read_futs)


def test_repository_concurrent_multithreaded_reads_and_writes() -> None:
    """Requirement 7: Repository direct concurrency stress test under high thread count."""
    db = DatabaseManager(":memory:")
    case_repo = CaseRepository(db)
    obs_repo = ObservationRepository(db)

    # Pre-populate batch metadata
    for i in range(10):
        case_repo.save_batch_metadata(
            BatchMetadata(
                batch_id=f"stress_batch_{i}",
                seed=i,
                record_count=100,
                matched_count=25,
                exception_count=75,
                resolved_count=25,
                review_count=50,
                unresolved_count=0,
                total_volume_inr=Decimal("10000.00"),
                explained_volume_inr=Decimal("10000.00"),
                unexplained_volume_inr=Decimal("0.00"),
                processing_time_ms=10.0,
            )
        )

    def reader_task(idx: int) -> int:
        batches = case_repo.list_all_batches()
        meta = case_repo.get_batch_metadata(f"stress_batch_{idx % 10}")
        obs = obs_repo.get_by_batch(f"stress_batch_{idx % 10}")
        return len(batches) + (1 if meta else 0) + len(obs)

    def writer_task(idx: int) -> None:
        case_repo.save_cases([
            Case(
                case_id=f"c_stress_{idx}",
                batch_id=f"stress_batch_{idx % 10}",
                observation_ids=[f"obs_{idx}"],
                residual_amount=Decimal("10.00"),
                financial_impact=Decimal("10.00"),
            )
        ])

    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        read_futures = [executor.submit(reader_task, i) for i in range(40)]
        write_futures = [executor.submit(writer_task, i) for i in range(40)]

        # All read and write tasks must complete without any DuckDB InvalidInputException
        for wf in write_futures:
            wf.result()
        for rf in read_futures:
            read_count = rf.result()
            assert read_count >= 10

    db.close()


def test_sequential_baseline_behavior(client: TestClient) -> None:
    """Requirement 8: Existing sequential behavior remains 100% intact."""
    res_post = client.post("/api/batches/process", json={"seed": 42, "rows": 25, "batch_id": "seq_batch"})
    assert res_post.status_code == 200

    res_cases = client.get("/api/cases?batch_id=seq_batch")
    assert res_cases.status_code == 200
    cases = res_cases.json()
    assert len(cases) > 0

    first_case_id = cases[0]["case_id"]
    res_single = client.get(f"/api/cases/{first_case_id}")
    assert res_single.status_code == 200
    assert res_single.json()["case_id"] == first_case_id
