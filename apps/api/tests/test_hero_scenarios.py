"""Unit tests for the Deterministic Hero Case Scenarios."""

from decimal import Decimal

from app.data.normalize import normalize_batch
from app.domain.enums import DecisionType
from app.domain.hero_scenarios import (
    get_hero_a_kirana,
    get_hero_b_mobility,
    get_hero_c_patterns,
)
from app.engine.shadow_engine import ValueFlowReconstructionEngine


def test_hero_a_kirana_resolves_via_chocolate_inventory():
    """Verify Hero A: Kirana non-cash inventory closes residual with 100% precision."""
    batch_id, raw_records, meta = get_hero_a_kirana()
    obs, inv = normalize_batch(raw_records, batch_id=batch_id)

    engine = ValueFlowReconstructionEngine()
    result = engine.process_batch(batch_id, obs, inv)

    assert result.total_records == 2
    # Baseline rules alone couldn't reconcile the ₹2 shortfall
    assert result.baseline_match_rate == 0.0
    # ShadowLedger Value-Flow Engine reconstructs the latent inventory move and resolves with 100% rate
    assert result.enhanced_resolution_rate == 100.0
    assert result.auto_resolved_count == 1
    assert result.unexplained_volume_inr == Decimal("0.00")

    # Regression 1: Prove Hero A normalizes an InventoryMove
    assert len(inv) == 1
    assert inv[0].item_description == "Dairy Milk Chocolate Change"
    assert inv[0].retail_value == Decimal("2.0")

    # Regression 2: Prove Hero A selects INVENTORY_SETTLEMENT
    assert len(result.cases) == 1
    case = result.cases[0]
    assert case.decision is not None
    assert "AUTO_RESOLVED_INVENTORY_SETTLEMENT_HIGH_CONFIDENCE" in case.decision.reason_codes

    # Regression 3: Prove a shadow event is materialized and serialized
    assert len(case.shadow_events) == 1
    shadow_event = case.shadow_events[0]
    assert shadow_event.hypothesis_type.value == "inventory_settlement"
    assert shadow_event.amount == Decimal("2.0")

    # Ensure it serializes correctly to JSON via Pydantic
    serialized = case.model_dump(mode="json")
    assert len(serialized["shadow_events"]) == 1
    assert serialized["shadow_events"][0]["hypothesis_type"] == "inventory_settlement"

def test_hero_b_mobility_enforces_off_ledger_safety_gate():
    """Verify Hero B: Ride 1 goes to HUMAN_REVIEW with trace; Ride 2 is not auto-resolved."""
    batch_id, raw_records, meta = get_hero_b_mobility()
    obs, inv = normalize_batch(raw_records, batch_id=batch_id)
    obs_map = {o.observation_id: o for o in obs}

    engine = ValueFlowReconstructionEngine()
    result = engine.process_batch(batch_id, obs, inv)

    assert result.total_records == 3
    assert len(result.cases) == 2

    # Invariant: NO off-ledger case may auto-resolve
    for c in result.cases:
        assert c.decision is not None
        assert c.decision.decision != DecisionType.AUTO_RESOLVE

    # Find the case with indirect digital trace (RIDE-HERO-01)
    trace_case = next(
        c for c in result.cases
        if any(obs_map[oid].entity_ids.get("ride_id") == "RIDE-HERO-01" for oid in c.observation_ids)
    )
    assert trace_case.decision.decision == DecisionType.HUMAN_REVIEW


def test_hero_c_patterns_discovers_three_distinct_clusters():
    """Verify Hero C: 60 fleet records collapse into 3 systemic structural patterns."""
    batch_id, raw_records, meta = get_hero_c_patterns()
    obs, inv = normalize_batch(raw_records, batch_id=batch_id)

    engine = ValueFlowReconstructionEngine()
    result = engine.process_batch(batch_id, obs, inv)

    assert result.total_records == 60
    assert len(result.pattern_clusters) == 3  # Discovered exactly 3 structural patterns: Fee, Off-Ledger, Inventory
