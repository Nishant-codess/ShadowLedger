"""Integration tests for Demo, Explain, and Action API endpoints."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_api_hero_demo_endpoints():
    """Verify executing Hero A, Hero B, and Hero C via the API."""
    for hero_id in ("hero_a", "hero_b", "hero_c"):
        resp = client.post(f"/api/demo/hero/{hero_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["hero_id"] == hero_id
        assert "batch_summary" in data
        assert data["batch_summary"]["record_count"] > 0


def test_api_explain_and_action_endpoints():
    """Verify explaining and performing operator action on a case."""
    # 1. Run Hero B to create cases
    demo_resp = client.post("/api/demo/hero/hero_b")
    assert demo_resp.status_code == 200
    cases = demo_resp.json()["cases"]
    assert len(cases) > 0

    case_id = cases[0]["case_id"]

    # 2. Test explain endpoint
    explain_resp = client.post(f"/api/cases/{case_id}/explain")
    assert explain_resp.status_code == 200
    exp_data = explain_resp.json()
    assert exp_data["case_id"] == case_id
    assert len(exp_data["narrative"]) > 0
    assert "provider" in exp_data

    # 3. Test operator action endpoint
    action_resp = client.post(
        f"/api/cases/{case_id}/action",
        json={"action": "escalate_ops", "operator_notes": "Requires supervisor follow-up on driver cash."},
    )
    assert action_resp.status_code == 200
    act_data = action_resp.json()
    assert act_data["status"] == "escalated_to_supervisor"
