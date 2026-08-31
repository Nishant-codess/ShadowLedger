"""Unit tests for DuckDB persistence layer and repositories."""

from datetime import UTC, datetime
from decimal import Decimal

from app.domain.enums import DecisionType, EventType, ValuationBasis
from app.domain.models import BatchMetadata, Case, Decision, InventoryMove, Observation
from app.persistence.case_repo import CaseRepository
from app.persistence.database import DatabaseManager
from app.persistence.observation_repo import ObservationRepository


def test_observation_and_inventory_roundtrip(test_db: DatabaseManager, obs_repo: ObservationRepository):
    """Verify storing and retrieving observations and inventory moves in DuckDB."""
    t0 = datetime(2026, 8, 31, 10, 0, 0, tzinfo=UTC)
    obs = Observation(
        observation_id="obs_test_1",
        source_system="pos",
        source_record_id="pos_rec_1",
        event_type=EventType.PAYMENT,
        amount=Decimal("999.50"),
        timestamp=t0,
        entity_ids={"order_id": "ORD-DB-1"},
        batch_id="batch_db_test",
    )
    inv = InventoryMove(
        move_id="inv_test_1",
        observation_id="obs_test_1",
        sku="SKU-TEST",
        item_description="Test Item",
        quantity=Decimal("2.0"),
        unit_cost=Decimal("50.00"),
        retail_value=Decimal("100.00"),
        valuation_basis=ValuationBasis.RETAIL,
        linked_order_id="ORD-DB-1",
        timestamp=t0,
    )

    obs_repo.save_observations([obs])
    obs_repo.save_inventory_moves([inv])

    fetched_obs = obs_repo.get_by_batch("batch_db_test")
    assert len(fetched_obs) == 1
    assert fetched_obs[0].observation_id == "obs_test_1"
    assert fetched_obs[0].amount == Decimal("999.50")

    fetched_inv = obs_repo.get_inventory_by_batch("batch_db_test")
    assert len(fetched_inv) == 1
    assert fetched_inv[0].move_id == "inv_test_1"
    assert fetched_inv[0].retail_value == Decimal("100.00")


def test_case_and_batch_metadata_roundtrip(test_db: DatabaseManager, case_repo: CaseRepository):
    """Verify storing and querying Cases, Decisions, and BatchMetadata."""
    case = Case(
        case_id="case_db_1",
        batch_id="batch_db_test",
        observation_ids=["obs_1", "obs_2"],
        residual_amount=Decimal("150.00"),
        financial_impact=Decimal("150.00"),
        decision=Decision(
            decision_id="dec_1",
            case_id="case_db_1",
            decision=DecisionType.HUMAN_REVIEW,
            reason_codes=["UNMATCHED_RESIDUAL"],
            evidence_ids=["obs_1", "obs_2"],
            evidence_confidence=0.85,
            financial_materiality=Decimal("150.00"),
        ),
    )

    case_repo.save_cases([case])
    fetched_cases = case_repo.get_cases_by_batch("batch_db_test")
    assert len(fetched_cases) == 1
    assert fetched_cases[0].case_id == "case_db_1"
    assert fetched_cases[0].decision is not None
    assert fetched_cases[0].decision.decision == DecisionType.HUMAN_REVIEW
    assert fetched_cases[0].decision.evidence_confidence == 0.85

    meta = BatchMetadata(
        batch_id="batch_db_test",
        record_count=100,
        matched_count=90,
        exception_count=10,
        total_volume_inr=Decimal("50000.00"),
    )
    case_repo.save_batch_metadata(meta)

    fetched_meta = case_repo.get_batch_metadata("batch_db_test")
    assert fetched_meta is not None
    assert fetched_meta.record_count == 100
    assert fetched_meta.total_volume_inr == Decimal("50000.00")
