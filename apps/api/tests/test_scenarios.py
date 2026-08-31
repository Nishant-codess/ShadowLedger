"""Unit tests verifying the complete Scenario Library."""

import random
from datetime import UTC, datetime

from app.domain.scenarios import SCENARIOS


def test_all_twelve_scenarios_exist():
    """Verify exactly 12 scenarios are defined."""
    assert len(SCENARIOS) == 12
    for i in range(1, 13):
        assert f"SCN_{i:02d}" in SCENARIOS


def test_scenario_generators_output_valid_records():
    """Verify every scenario generator produces valid observed records and ground truth."""
    rng = random.Random(42)
    base_time = datetime(2026, 8, 31, 9, 0, 0, tzinfo=UTC)

    for scn_id, defn in SCENARIOS.items():
        obs_list, truth = defn.generator(rng, 1, base_time)

        assert len(obs_list) >= 1, f"{scn_id} generated empty observed list"
        assert isinstance(truth, dict), f"{scn_id} generated invalid truth"
        assert truth["scenario_id"] == scn_id
        assert "is_reconciled" in truth, f"{scn_id} truth missing is_reconciled flag"

        for obs in obs_list:
            assert "source_system" in obs
            assert "source_record_id" in obs
            assert "event_type" in obs
            assert "amount" in obs
            assert "currency" in obs
            assert "timestamp" in obs


def test_kirana_inventory_scenario_hero_a():
    """Verify SCN_04 (Hero A) includes chocolate inventory change."""
    rng = random.Random(42)
    base_time = datetime(2026, 8, 31, 9, 0, 0, tzinfo=UTC)
    obs_list, truth = SCENARIOS["SCN_04"].generator(rng, 1, base_time)

    assert truth["bill_amount"] == 98.0
    assert truth["tendered_cash"] == 100.0
    assert truth["inventory_change_retail"] == 2.0

    inv_records = [o for o in obs_list if o["event_type"] == "inventory_move"]
    assert len(inv_records) == 1
    assert "inventory_move" in inv_records[0]
    assert inv_records[0]["inventory_move"]["retail_value"] == 2.0


def test_off_ledger_ride_scenarios_hero_b():
    """Verify SCN_08 and SCN_09 ground truths contain hidden cash deviations."""
    rng = random.Random(42)
    base_time = datetime(2026, 8, 31, 9, 0, 0, tzinfo=UTC)

    # SCN_08: Digital trace available
    _, truth_08 = SCENARIOS["SCN_08"].generator(rng, 1, base_time)
    assert truth_08["official_fare"] == 150.0
    assert truth_08["off_ledger_extra"] == 50.0
    assert truth_08["digital_trace_available"] is True
    assert truth_08["expected_decision"] == "human_review"

    # SCN_09: Cash-only invisible
    obs_09, truth_09 = SCENARIOS["SCN_09"].generator(rng, 1, base_time)
    assert len(obs_09) == 1  # Only official fare recorded in digital systems
    assert truth_09["official_fare"] == 150.0
    assert truth_09["hidden_economic_deviation"] == 50.0
    assert truth_09["digital_trace_available"] is False
    assert truth_09["expected_decision"] == "unresolved"
