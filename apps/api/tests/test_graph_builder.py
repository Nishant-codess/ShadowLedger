"""Unit tests for the Case-Local Value-Flow Graph Builder."""

from datetime import UTC, datetime
from decimal import Decimal

from app.domain.enums import EventStatus, EventType, HypothesisType, ValuationBasis
from app.domain.models import Event, Hypothesis, InventoryMove, Observation
from app.engine.graph_builder import ValueFlowGraphBuilder


def test_graph_builder_creates_nodes_and_edges():
    """Verify building a case graph with observed, inventory, and latent nodes."""
    builder = ValueFlowGraphBuilder()
    t0 = datetime(2026, 8, 31, 10, 0, 0, tzinfo=UTC)

    obs = [
        Observation(
            observation_id="obs_pos_1",
            source_system="pos",
            source_record_id="pos_100",
            event_type=EventType.PAYMENT,
            amount=Decimal("100.00"),
            timestamp=t0,
            entity_ids={"order_id": "ORD-1"},
        ),
        Observation(
            observation_id="obs_bank_1",
            source_system="bank",
            source_record_id="bnk_100",
            event_type=EventType.SETTLEMENT,
            amount=Decimal("98.00"),
            timestamp=t0,
            entity_ids={"order_id": "ORD-1"},
        ),
    ]

    inv = [
        InventoryMove(
            move_id="inv_choc_1",
            observation_id="obs_pos_1",
            item_description="Dairy Milk Chocolate",
            retail_value=Decimal("2.00"),
            valuation_basis=ValuationBasis.RETAIL,
            linked_order_id="ORD-1",
            timestamp=t0,
        )
    ]

    latent_evt = Event(
        event_id="evt_shd_1",
        status=EventStatus.INFERRED_LATENT,
        event_type=EventType.INVENTORY_MOVE,
        amount=Decimal("2.00"),
        timestamp=t0,
        hypothesis_type=HypothesisType.INVENTORY_SETTLEMENT,
    )

    hyp = Hypothesis(
        hypothesis_id="hyp_1",
        hypothesis_type=HypothesisType.INVENTORY_SETTLEMENT,
        case_id="case_1",
        generated_event=latent_evt,
        evidence_ids=["obs_pos_1"],
        evidence_confidence=0.95,
        can_auto_resolve=True,
    )

    graph = builder.build_case_graph(
        observations=obs,
        inventory_moves=inv,
        hypotheses=[hyp],
        winning_hypothesis=hyp,
    )

    assert graph.number_of_nodes() == 4  # 2 obs + 1 inv + 1 latent
    assert graph.number_of_edges() >= 2

    # Verify serialization format
    serialized = builder.serialize_graph(graph)
    assert serialized["node_count"] == 4
    assert len(serialized["nodes"]) == 4
    assert len(serialized["links"]) >= 2

    # Check node attributes
    node_ids = [n["id"] for n in serialized["nodes"]]
    assert "obs_pos_1" in node_ids
    assert "obs_bank_1" in node_ids
    assert "inv_choc_1" in node_ids
    assert "evt_shd_1" in node_ids
