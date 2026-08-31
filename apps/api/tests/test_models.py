"""Unit tests for domain models and taxonomy validation."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.domain.enums import (
    EventStatus,
    EventType,
    HypothesisType,
    ValuationBasis,
    ValueType,
)
from app.domain.models import (
    Event,
    Hypothesis,
    InventoryMove,
    ValueFlow,
)


def test_four_level_event_taxonomy():
    """Verify all four levels of the event taxonomy exist and validate."""
    t = datetime.now(UTC)

    # Level 1: Observed fact
    e1 = Event(status=EventStatus.OBSERVED, event_type=EventType.PAYMENT, amount=Decimal("100.00"), timestamp=t)
    assert e1.status == EventStatus.OBSERVED
    assert e1.confidence is None

    # Level 2: Derived fact
    e2 = Event(status=EventStatus.DERIVED, event_type=EventType.FEE, amount=Decimal("-2.00"), timestamp=t)
    assert e2.status == EventStatus.DERIVED

    # Level 3: Inferred latent event
    e3 = Event(
        status=EventStatus.INFERRED_LATENT,
        event_type=EventType.REFUND,
        amount=Decimal("15.00"),
        timestamp=t,
        confidence=0.88,
        hypothesis_type=HypothesisType.REFUND,
    )
    assert e3.status == EventStatus.INFERRED_LATENT
    assert e3.confidence == 0.88

    # Level 4: Unobserved deviation
    e4 = Event(
        status=EventStatus.UNOBSERVED_DEVIATION,
        event_type=EventType.PAYMENT,
        amount=Decimal("50.00"),
        timestamp=t,
        confidence=0.72,
        hypothesis_type=HypothesisType.OFF_LEDGER_DEVIATION,
    )
    assert e4.status == EventStatus.UNOBSERVED_DEVIATION


def test_off_ledger_deviation_cannot_auto_resolve():
    """Verify strict safety rule: OFF_LEDGER_DEVIATION can never have can_auto_resolve=True."""
    t = datetime.now(UTC)
    ev = Event(
        status=EventStatus.UNOBSERVED_DEVIATION,
        event_type=EventType.PAYMENT,
        amount=Decimal("50.00"),
        timestamp=t,
        confidence=0.99,
        hypothesis_type=HypothesisType.OFF_LEDGER_DEVIATION,
    )

    hyp = Hypothesis(
        hypothesis_type=HypothesisType.OFF_LEDGER_DEVIATION,
        case_id="case_uber_123",
        generated_event=ev,
        evidence_confidence=0.99,
        can_auto_resolve=True,  # Attempt to force True
    )

    # Validator must enforce False
    assert hyp.can_auto_resolve is False


def test_inventory_move_valuation_breakdown():
    """Verify inventory move preserves unit_cost, retail_value, and valuation basis."""
    inv = InventoryMove(
        observation_id="obs_001",
        sku="SKU-CHOC-02",
        item_description="Dairy Milk Chocolate 2 INR",
        quantity=Decimal("1.0"),
        unit_cost=Decimal("1.20"),
        retail_value=Decimal("2.00"),
        valuation_basis=ValuationBasis.RETAIL,
        linked_order_id="ORD-100",
    )

    assert inv.unit_cost == Decimal("1.20")
    assert inv.retail_value == Decimal("2.00")
    assert inv.valuation_basis == ValuationBasis.RETAIL


def test_value_flow_conservation():
    """Verify ValueFlow model captures directed edge and value denomination."""
    vf = ValueFlow(
        source_event_id="evt_01",
        target_event_id="evt_02",
        amount=Decimal("2.00"),
        value_type=ValueType.INVENTORY,
        direction="settles",
        valuation_basis=ValuationBasis.RETAIL,
    )
    assert vf.value_type == ValueType.INVENTORY
    assert vf.amount == Decimal("2.00")


def test_confidence_validation_bounds():
    """Verify confidence must be strictly in [0.0, 1.0]."""
    t = datetime.now(UTC)
    with pytest.raises(ValueError):
        Event(status=EventStatus.INFERRED_LATENT, event_type=EventType.PAYMENT, amount=Decimal("10.00"), timestamp=t, confidence=1.5)
