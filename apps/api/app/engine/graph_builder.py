"""Case-local NetworkX Value-Flow Graph Builder.

Constructs focused directed acyclic/cyclic value-flow graphs for individual
reconciliation cases, linking observed facts, derived events, and candidate
latent economic hypotheses.
"""

from typing import Any

import networkx as nx

from app.domain.enums import EventStatus, EventType, ValueType
from app.domain.models import Hypothesis, InventoryMove, Observation


class ValueFlowGraphBuilder:
    """Constructs and serializes case-local directed value-flow graphs."""

    def build_case_graph(
        self,
        observations: list[Observation],
        inventory_moves: list[InventoryMove] | None = None,
        hypotheses: list[Hypothesis] | None = None,
        winning_hypothesis: Hypothesis | None = None,
    ) -> nx.DiGraph:
        """Build a case-local NetworkX DiGraph connecting observed and inferred events."""
        graph: nx.DiGraph = nx.DiGraph()

        obs_map: dict[str, Observation] = {obs.observation_id: obs for obs in observations}
        inv_list = inventory_moves or []
        hyp_list = hypotheses or []

        # 1. Add Observed Event Nodes
        for obs in observations:
            graph.add_node(
                obs.observation_id,
                id=obs.observation_id,
                label=f"{obs.source_system.upper()} {obs.event_type.value}: ₹{float(obs.amount):.2f}",
                node_type=EventStatus.OBSERVED.value,
                status=EventStatus.OBSERVED.value,
                event_type=obs.event_type.value,
                amount=float(obs.amount),
                currency=obs.currency,
                source_system=obs.source_system,
                timestamp=obs.timestamp.isoformat(),
                description=obs.description or f"{obs.source_system} record",
                confidence=1.0,
                is_source_truth=True,
            )

        # 2. Add Inventory Asset Nodes
        for inv in inv_list:
            inv_node_id = inv.move_id
            graph.add_node(
                inv_node_id,
                id=inv_node_id,
                label=f"INVENTORY: {inv.item_description} (₹{float(inv.retail_value or 0):.2f})",
                node_type="inventory_asset",
                status=EventStatus.OBSERVED.value,
                event_type=EventType.INVENTORY_MOVE.value,
                amount=float(inv.retail_value or inv.unit_cost or 0),
                currency="INR",
                source_system="inventory",
                timestamp=inv.timestamp.isoformat(),
                description=f"{inv.quantity}x {inv.item_description} [{inv.valuation_basis.value}]",
                confidence=1.0,
                is_source_truth=True,
            )
            # Link inventory to parent observation
            if inv.observation_id in obs_map:
                graph.add_edge(
                    inv_node_id,
                    inv.observation_id,
                    amount=float(inv.retail_value or 0),
                    value_type=ValueType.INVENTORY.value,
                    direction="settlement_change",
                    confidence=1.0,
                    status="proven",
                )

        # 3. Add Candidate & Inferred Latent Event Nodes
        for hyp in hyp_list:
            gen_event = hyp.generated_event
            is_winner = winning_hypothesis is not None and hyp.hypothesis_id == winning_hypothesis.hypothesis_id

            node_status = gen_event.status.value
            confidence = hyp.evidence_confidence

            graph.add_node(
                gen_event.event_id,
                id=gen_event.event_id,
                label=f"SHADOW {gen_event.event_type.value.upper()}: ₹{float(gen_event.amount):.2f}",
                node_type=node_status,
                status=node_status,
                event_type=gen_event.event_type.value,
                amount=float(gen_event.amount),
                currency=gen_event.currency,
                source_system="shadow_ledger",
                timestamp=gen_event.timestamp.isoformat(),
                description=f"Latent {hyp.hypothesis_type.value} (conf={confidence:.2f})",
                confidence=confidence,
                hypothesis_id=hyp.hypothesis_id,
                hypothesis_type=hyp.hypothesis_type.value,
                is_winner=is_winner,
                is_source_truth=False,
            )

            # Connect Latent Node to its supporting evidence observations
            for ev_id in hyp.evidence_ids:
                if ev_id in obs_map:
                    graph.add_edge(
                        ev_id,
                        gen_event.event_id,
                        amount=float(gen_event.amount),
                        value_type=ValueType.CASH.value,
                        direction="explains_residual",
                        confidence=confidence,
                        status="inferred" if is_winner else "candidate",
                    )

            # Connect Latent Node to indirect evidence
            for ind_id in hyp.indirect_evidence_ids:
                if ind_id in obs_map:
                    graph.add_edge(
                        ind_id,
                        gen_event.event_id,
                        amount=float(gen_event.amount),
                        value_type="indirect_trace",
                        direction="supporting_evidence",
                        confidence=confidence,
                        status="indirect",
                    )

        # 4. Connect Observed Payments to Settlements (Conservation Edges)
        payments = [o for o in observations if o.event_type == EventType.PAYMENT]
        settlements = [o for o in observations if o.event_type == EventType.SETTLEMENT]
        fees = [o for o in observations if o.event_type == EventType.FEE]

        for p in payments:
            for s in settlements:
                if not graph.has_edge(p.observation_id, s.observation_id):
                    graph.add_edge(
                        p.observation_id,
                        s.observation_id,
                        amount=float(min(p.amount, s.amount)),
                        value_type=ValueType.CASH.value,
                        direction="transfer",
                        confidence=1.0,
                        status="observed_link",
                    )

        for s in settlements:
            for f in fees:
                if not graph.has_edge(f.observation_id, s.observation_id):
                    graph.add_edge(
                        f.observation_id,
                        s.observation_id,
                        amount=float(f.amount),
                        value_type="fee_deduction",
                        direction="fee_offset",
                        confidence=1.0,
                        status="observed_fee",
                    )

        return graph

    def serialize_graph(self, graph: nx.DiGraph) -> dict[str, Any]:
        """Convert NetworkX DiGraph into JSON format for front-end graph visualization."""
        nodes = []
        for node_id, data in graph.nodes(data=True):
            node_dict = dict(data)
            node_dict["id"] = str(node_id)
            nodes.append(node_dict)

        links = []
        for source, target, data in graph.edges(data=True):
            link_dict = dict(data)
            link_dict["source"] = str(source)
            link_dict["target"] = str(target)
            links.append(link_dict)

        return {
            "nodes": nodes,
            "links": links,
            "node_count": len(nodes),
            "link_count": len(links),
        }
