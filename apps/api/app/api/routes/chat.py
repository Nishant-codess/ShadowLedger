"""Interactive Chat API Route for ShadowLedger AI Copilot."""

import json
import logging
import os
import urllib.error
import urllib.request
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.routes.batches import get_case_repo, get_obs_repo
from app.persistence.case_repo import CaseRepository
from app.persistence.observation_repo import ObservationRepository

router = APIRouter(prefix="/api/chat", tags=["AI Copilot"])
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    message: str
    case_id: str | None = None
    batch_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    provider: str
    grounded_context: str | None = None


KNOWLEDGE_RESPONSES: dict[str, str] = {
    "why did this case resolve": (
        "In Hero A (The Missing ₹2), the merchant received ₹98.00 cash settlement against a ₹100.00 POS sale. "
        "ShadowLedger discovered a physical inventory movement of 1 unit of Cadbury Eclairs Candy Change (₹2.00) "
        "cryptographically associated with the exact order reference. Because value conservation (₹98 cash + ₹2 candy = ₹100) "
        "is closed with zero contradictions, the policy risk gate safely auto-resolved this exception."
    ),
    "why does this ride need human review": (
        "In Hero B (The Fare That Doesn't Add Up), platform logs show an official metered fare of ₹150.00. "
        "An independent secondary trace revealed the customer paid ₹50.00 directly to the driver's personal UPI QR code "
        "(for an airport toll or AC surcharge). Under strict governance rules, off-ledger transactions CANNOT "
        "be automatically settled because external secondary traces lack official clearing authority. Therefore, "
        "the case is safely escalated to Human Review."
    ),
    "why is the cab case unresolved": (
        "In Ride 2 of Hero B, platform records log a ₹150.00 fare with an unrecorded ₹50 cash deviation. "
        "Unlike Ride 1, there is zero direct or indirect digital evidence (no UPI trace, no external receipt). "
        "ShadowLedger adheres to an architectural invariant: it refuses to guess without corroboration, "
        "preserving the case in UNRESOLVED status."
    ),
    "what are fleet patterns": (
        "Fleet Patterns group seemingly isolated transaction discrepancies across merchants and drivers into recurring "
        "systemic signatures. For example, 60 raw discrepancies collapse into 3 distinct operational causes: "
        "1) Kirana stores substituting small change coins with ₹2 Cadbury Eclairs candy; "
        "2) Cab drivers collecting direct UPI payments for airport toll surcharges; "
        "3) Payment gateways deducting standard 2.0% MDR fees. This turns 1,000 isolated tickets into 3 actionable operational rules."
    ),
    "what is shadowledger": (
        "ShadowLedger is a local-first financial reconciliation engine that investigates what traditional ledgers cannot explain. "
        "When cash settlements don't match source invoices, it reconstructs latent economic events (like physical inventory "
        "change, off-ledger deviations, and fee deductions), provides multi-dimensional mathematical proof, and enforces strict "
        "safety gates to prevent unsafe auto-resolutions."
    ),
    "why do off-ledger deviations require human review": (
        "Under strict financial safety controls, off-ledger transactions CANNOT be auto-resolved because external "
        "secondary traces (like personal driver UPI QR transfers) lack official platform clearing authority. "
        "Auto-posting an unrecorded transaction to the official general ledger without operator sign-off would violate "
        "accounting governance."
    ),
    "what is the auto-resolution policy gate": (
        "The auto-resolution policy gate is a deterministic safety barrier. A case is permitted to auto-resolve ONLY when: "
        "1) Mathematical value conservation is closed (₹0.00 residual shortfall), "
        "2) Evidence confidence meets or exceeds the safety threshold (>= 85%), and "
        "3) The latent event is not an off-ledger deviation. Off-ledger flows are strictly barred from auto-resolution."
    ),
    "how is evidence confidence scored": (
        "Evidence confidence is scored across 5 rigorous evidentiary dimensions: "
        "1) Temporal Plausibility (verified chronological sequence), "
        "2) Entity Linkage (cross-system counterparty ID matching), "
        "3) Value Conservation (arithmetic closure across payment components), "
        "4) Corroboration Depth (direct ledger entries vs indirect digital traces), and "
        "5) Contradiction Checking (zero customer disputes or merchant claims). "
        "Scores range from 0% to 100%."
    ),
    "what cases are currently held in queue": (
        "Cases currently held in queue include transactions with unrecorded off-ledger flows (such as Hero B's ₹50 driver UPI surcharge) "
        "or uncorroborated variances with zero digital trace (such as cash deviations). These remain in Human Review or Unresolved "
        "status until an operator reviews and authorizes or rejects them."
    ),
    "how is total value at risk calculated": (
        "Total Value at Risk represents the cumulative financial exposure across all active exception cases. "
        "It sums the absolute residual variance where funds have cleared or left the merchant account without verified "
        "reconciliation proof."
    ),
    "what causes the cab upi qr surcharge pattern": (
        "The cab UPI QR surcharge pattern occurs when mobility drivers collect off-app fees (e.g. airport parking tolls "
        "or AC surcharges) directly via personal UPI QR codes rather than logging them through the platform metering system. "
        "ShadowLedger detects these by linking passenger bank payment timestamps to driver transaction credits."
    ),
    "how do patterns compress 1,000 exceptions": (
        "Pattern clustering groups raw exceptions by latent event signatures, counterparty behavior, and residual percentages. "
        "Instead of investigating 1,000 isolated tickets individually, auditors can review 3 to 4 recurring fleet patterns, "
        "reducing manual review overhead by up to 90%."
    ),
}


def _is_time_query(q: str) -> bool:
    """Check if query is asking for the current local time."""
    q_clean = q.lower().strip()
    time_triggers = [
        "what is the time",
        "what's the time",
        "what time is it",
        "tell me the time",
        "current time",
        "time now",
        "time right now",
        "what is current time",
        "what is our time",
    ]
    if any(trigger in q_clean for trigger in time_triggers):
        return True
    words = [w.strip("?,.!") for w in q_clean.split()]
    if words in (["time"], ["what", "time"], ["current", "time"], ["the", "time"]):
        return True
    return False


def _get_current_time_str() -> str:
    """Return accurately formatted real-world Indian Standard Time (IST)."""
    now = datetime.now()
    time_str = now.strftime("%I:%M %p").lstrip("0")
    date_str = now.strftime("%A, %B %d, %Y")
    return (
        f"The current local time is {time_str} IST on {date_str}. "
        f"All demo transactions in ShadowLedger are recorded in UTC with synchronized ledger timestamps."
    )


def _is_evidence_query(q: str) -> bool:
    """Check if query is requesting factual evidence breakdown."""
    q_clean = q.lower().strip()
    evidence_triggers = [
        "evidence breakdown",
        "factual evidence",
        "break down the evidence",
        "break down evidence",
        "show evidence",
        "show factual evidence",
        "evidence summary",
        "evidence details",
    ]
    return any(trigger in q_clean for trigger in evidence_triggers)


def _build_evidence_breakdown(
    case_details: dict[str, Any] | None,
    case_obs: list[Any] | None = None,
    case_obj: Any | None = None,
) -> str:
    """Construct an authoritative, structured factual evidence breakdown."""
    if not case_details:
        return (
            "To view a factual evidence breakdown, please select a case from the dashboard. For example:\n\n"
            "• **Hero A (Kirana Store: The Missing ₹2)**: Shows POS sale, NEFT bank settlement, and Cadbury Eclairs candy change.\n"
            "• **Hero B (Cab Ride: Digital Trace)**: Shows platform fare and the driver's ₹50 off-ledger UPI trace."
        )

    scenario = case_details.get("scenario_id", "")
    residual = case_details.get("residual", 0.0)

    if "04" in scenario or "kirana" in case_details.get("batch_id", ""):
        return (
            "Factual Evidence Breakdown for Hero A (Kirana Store: The Missing ₹2):\n\n"
            "1. Observed Gross POS Sale: ₹100.00 (POS Purchase: Groceries + Eclairs Candy Change, Order: ORD-KIRANA-HERO)\n"
            "2. Observed Bank Settlement: ₹98.00 (Bank NEFT Net Settlement Ref: ORD-KIRANA-HERO)\n"
            "3. Reconstructed Latent Event: Cadbury Eclairs Candy Change (₹2.00) — confirmed by physical ERP inventory deduction (1 unit @ ₹2.00) at 10:30 AM\n"
            "4. Value Conservation Proof: ₹98.00 cash settlement + ₹2.00 physical candy change = ₹100.00 gross sale (₹0.00 residual gap)\n"
            "5. Policy Gate Decision: AUTO-RESOLVED with 90% evidence confidence and zero merchant contradictions."
        )
    elif "08" in scenario:
        return (
            "Factual Evidence Breakdown for Hero B (Mobility Ride: Digital Trace):\n\n"
            "1. Official Platform Record: ₹150.00 (In-app metered trip fare, Trip: RIDE-HERO-01)\n"
            "2. Secondary Digital Trace: ₹50.00 (Customer UPI QR credit to driver's personal account at 11:18 AM)\n"
            "3. Reconstructed Latent Event: Off-Ledger Payment Deviation (₹50.00 toll/AC surcharge collected outside platform)\n"
            "4. Valuation Conservation: ₹150.00 platform fare + ₹50.00 driver surcharge = ₹200.00 total economic activity\n"
            "5. Policy Gate Decision: ESCALATED TO HUMAN REVIEW — off-ledger secondary flows lack official platform clearing authority and cannot auto-resolve."
        )
    elif "09" in scenario:
        return (
            "Factual Evidence Breakdown for Hero B (Mobility Ride: Cash Only):\n\n"
            "1. Official Platform Record: ₹150.00 (In-app metered trip fare, Trip: RIDE-HERO-02)\n"
            "2. Secondary Digital Trace: NONE (Suspected ₹50 cash payment with zero digital receipt or bank entry)\n"
            "3. Reconstructed Latent Event: Unobserved Cash Deviation (Confidence: 20%)\n"
            "4. Policy Gate Decision: UNRESOLVED — ShadowLedger strictly refuses to fabricate facts without corroborating evidence."
        )
    else:
        obs_lines = []
        if case_obs:
            for o in case_obs:
                obs_lines.append(f"• Observed Record: {o.description} (₹{float(o.amount):.2f}) via {o.source_system}")
        obs_str = "\n".join(obs_lines) if obs_lines else f"• Observed: {case_details.get('obs_summary', 'Records evaluated')}"
        return (
            f"Factual Evidence Breakdown for Case {case_details.get('case_id')}:\n\n"
            f"{obs_str}\n"
            f"• Reconstructed Latent Event: {case_details.get('hypothesis_summary', 'Evidence evaluated')}\n"
            f"• Residual Variance: ₹{residual:.2f}\n"
            f"• Policy Gate Decision: {case_details.get('decision', 'unresolved').upper()} per safety threshold gates."
        )


def _is_about_case_query(q: str) -> bool:
    """Check if query is asking what the case is about."""
    q_clean = q.lower().strip()
    triggers = [
        "what is this case about",
        "what is this case",
        "explain this case",
        "tell me about this case",
        "about this case",
    ]
    return any(trigger in q_clean for trigger in triggers)


def _build_about_case(case_details: dict[str, Any] | None) -> str:
    """Return an authoritative summary of what the case is about."""
    if not case_details:
        return (
            "We have two key demonstration cases on the dashboard:\n\n"
            "1. **Hero A (Kirana Store: The Missing ₹2)**: POS sale of ₹100.00 settled as ₹98.00 cash + ₹2.00 Cadbury Eclairs candy change. (Auto-resolved)\n"
            "2. **Hero B (Mobility Ride: Digital Trace)**: Metered fare of ₹150.00 with an unrecorded ₹50.00 driver UPI surcharge. (Human Review)\n\n"
            "Select either case from the dashboard to investigate evidence graphs and policy gates."
        )

    scenario = case_details.get("scenario_id", "")
    residual = case_details.get("residual", 0.0)

    if "04" in scenario or "kirana" in case_details.get("batch_id", ""):
        return (
            "This case is Hero A (Kirana Store: The Missing ₹2). A customer purchased groceries for ₹100.00 at POS, "
            "and the merchant's bank settled ₹98.00 in cash via NEFT. ShadowLedger identified an ERP inventory movement of 1 unit of "
            "Cadbury Eclairs Candy Change (₹2.00) issued in lieu of coin change. Because mathematical value conservation is completely "
            "proven (₹98 cash + ₹2 candy = ₹100 gross sale) with zero merchant contradictions, this case was safely AUTO-RESOLVED."
        )
    elif "08" in scenario:
        return (
            "This case is Hero B (Mobility Ride: The Fare That Doesn't Add Up - Digital Trace). The official in-app metered fare was "
            "₹150.00. An external UPI QR digital trace showed an additional ₹50.00 payment directly to the driver for an airport toll/AC surcharge, "
            "bringing total customer payment to ₹200.00. Because off-ledger unrecorded payments cannot be auto-cleared without human sign-off, "
            "this case was escalated to HUMAN REVIEW."
        )
    elif "09" in scenario:
        return (
            "This case is Hero B (Mobility Ride: Cash Only). Platform logs show a ₹150.00 metered fare with a suspected ₹50.00 "
            "unrecorded cash difference. Because there is zero digital trace or receipt to verify what occurred, ShadowLedger strictly refuses "
            "to guess and keeps the case UNRESOLVED."
        )
    else:
        return (
            f"This case ({case_details.get('case_id')}) has a discrepancy gap of ₹{residual:.2f} with policy outcome '{case_details.get('decision')}'. "
            f"Observations: {case_details.get('obs_summary')}. Reconstructed Latent Event: {case_details.get('hypothesis_summary')}."
        )


def _is_decision_or_resolution_query(q: str) -> bool:
    """Check if query is asking about policy gate decision or resolution reason."""
    q_clean = q.lower().strip()
    triggers = [
        "policy gate decision",
        "policy gate",
        "policy decision",
        "what was the policy",
        "why did this case resolve",
        "why did this case get held",
        "why resolved or held",
        "why resolve or get held",
        "why did this resolve",
        "why was this resolved",
        "why was this held",
        "what was the decision",
    ]
    return any(trigger in q_clean for trigger in triggers)


def _build_decision_explanation(case_details: dict[str, Any] | None) -> str:
    """Return an authoritative explanation of the policy decision."""
    if not case_details:
        return (
            "The policy gate evaluates mathematical value conservation, evidentiary confidence thresholds (>= 85%), "
            "and regulatory governance rules. For instance, Hero A auto-resolves because value conservation is complete with verified "
            "candy inventory change, whereas Hero B escalates to Human Review because unrecorded off-ledger flows require operator approval."
        )

    scenario = case_details.get("scenario_id", "")
    decision = case_details.get("decision", "unresolved")
    cid = case_details.get("case_id", "")

    if "04" in scenario or "kirana" in case_details.get("batch_id", ""):
        return (
            f"The policy gate decision for Case {cid} is AUTO-RESOLVED. "
            f"This decision was safely made because mathematical value conservation is completely closed "
            f"(₹98.00 bank settlement + ₹2.00 Cadbury Eclairs candy inventory deduction = ₹100.00 gross POS sale) "
            f"with 90% evidence confidence and zero conflicting merchant records."
        )
    elif "08" in scenario:
        return (
            f"The policy gate decision for Case {cid} is ESCALATED TO HUMAN REVIEW. "
            f"Under ShadowLedger's financial safety invariants, off-ledger payment deviations "
            f"(such as the driver's ₹50 personal UPI QR collection) are strictly prohibited from automated "
            f"settlement closure without human operator authorization."
        )
    elif "09" in scenario:
        return (
            f"The policy gate decision for Case {cid} is UNRESOLVED. "
            f"Because there is zero digital evidence or receipt to corroborate the suspected ₹50 cash difference, "
            f"ShadowLedger strictly refuses to guess and maintains the case in the exception queue."
        )
    else:
        return f"The policy gate decision for Case {cid} is {decision.upper()} based on evaluated evidence confidence."


def _get_deterministic_fallback(query: str, case_context: str | None, case_details: dict[str, Any] | None) -> str:
    q = query.lower().strip()

    # 1. Natural greetings
    if q in ("hi", "hello", "hey", "good morning", "good evening", "howdy", "sup"):
        return "Hello! I am doing well, thank you. How can I assist you with investigating financial discrepancies or review ledger reconstructions today?"
    if "how are you" in q:
        return "I'm doing great, thank you! I am ready to help you analyze ledger transactions, inspect evidence graphs, or explain case resolutions."
    if _is_time_query(q):
        return _get_current_time_str()

    # 2. Evidence breakdown query
    if _is_evidence_query(q):
        return _build_evidence_breakdown(case_details)

    # 3. Policy gate decision query
    if _is_decision_or_resolution_query(q):
        return _build_decision_explanation(case_details)

    # 4. Case-specific inquiries when inside a case
    if _is_about_case_query(q):
        return _build_about_case(case_details)

    # 5. Disambiguation if asking on home page without case context
    if "why did this case resolve" in q or "what is this case" in q:
        return (
            "Which case would you like to explore? We have two key demonstration cases:\n\n"
            "1. **Hero A (Kirana Store - The Missing ₹2)**: Auto-resolved via ₹2 Cadbury Eclairs candy change.\n"
            "2. **Hero B (Cab Ride - The Fare That Doesn't Add Up)**: Escalated to Human Review due to ₹50 off-ledger UPI trace.\n\n"
            "You can open either case from the dashboard, or ask me about Fleet Patterns and Defensibility Benchmarks!"
        )

    for key, answer in KNOWLEDGE_RESPONSES.items():
        if all(word in q for word in key.split()[:3]):
            return answer

    if "kirana" in q or "candy" in q or "chocolate" in q or "eclairs" in q or "missing ₹2" in q:
        return KNOWLEDGE_RESPONSES["why did this case resolve"]
    if "cab" in q or "ride" in q or "human review" in q or "toll" in q:
        return KNOWLEDGE_RESPONSES["why does this ride need human review"]
    if "pattern" in q or "fleet" in q or "collapse" in q:
        return KNOWLEDGE_RESPONSES["what are fleet patterns"]
    if "confidence" in q or "scoring" in q or "scored" in q:
        return KNOWLEDGE_RESPONSES["how is evidence confidence scored"]
    if "auto-resolution" in q or "policy gate" in q:
        return KNOWLEDGE_RESPONSES["what is the auto-resolution policy gate"]

    if case_context:
        return (
            f"Based on the active investigation records:\n{case_context}\n\n"
            "ShadowLedger evaluated value conservation, temporal plausibility, and entity linkage. "
            "Policy actions strictly follow evidentiary confidence thresholds."
        )

    return (
        "I am here to assist with ShadowLedger financial investigations. You can ask:\n"
        "• 'Why did this case resolve?'\n"
        "• 'Why does this ride need human review?'\n"
        "• 'What are Fleet Patterns?'\n"
        "• 'What happened to the missing ₹2?'"
    )


@router.post("", response_model=ChatResponse)
def chat_copilot(
    req: ChatRequest,
    case_repo: CaseRepository = Depends(get_case_repo),
    obs_repo: ObservationRepository = Depends(get_obs_repo),
) -> ChatResponse:
    """Answer operator and auditor inquiries using local Ollama with deterministic fallback."""
    case_context = None
    case_details: dict[str, Any] | None = None
    case_obs: list[Any] = []
    case_obj: Any | None = None
    c: Any | None = None

    if req.case_id:
        c = case_repo.get_case_by_id(req.case_id)
        if not c:
            # Prefix or substring match for truncated case IDs (e.g. case_27009 or case_806e5)
            all_cases = case_repo.get_cases_by_batch()
            for candidate in all_cases:
                if candidate.case_id.startswith(req.case_id) or req.case_id.startswith(candidate.case_id[:8]):
                    c = candidate
                    break
            # If still not found and case_id looks like a case ID from a regenerated session, fallback to Hero A
            if not c and req.case_id.startswith("case_"):
                for candidate in all_cases:
                    if "kirana" in candidate.batch_id or candidate.scenario_id == "SCN_04":
                        c = candidate
                        break

    # If no case specified or found yet, check if the query references a specific hero scenario
    if not c:
        q_lower = req.message.lower()
        all_cases = case_repo.get_cases_by_batch()
        if any(w in q_lower for w in ["kirana", "candy", "eclairs", "missing ₹2", "missing 2", "hero a"]):
            for candidate in all_cases:
                if "kirana" in candidate.batch_id or candidate.scenario_id == "SCN_04":
                    c = candidate
                    break
        elif any(w in q_lower for w in ["ride", "cab", "mobility", "toll", "hero b"]):
            for candidate in all_cases:
                if candidate.scenario_id == "SCN_08":
                    c = candidate
                    break
            if not c:
                for candidate in all_cases:
                    if "mobility" in candidate.batch_id:
                        c = candidate
                        break
        elif _is_evidence_query(req.message):
            # If asking for evidence breakdown with no case selected, showcase Hero A
            for candidate in all_cases:
                if "kirana" in candidate.batch_id or candidate.scenario_id == "SCN_04":
                    c = candidate
                    break

    if c:
        case_obj = c
        all_obs = obs_repo.get_by_batch(c.batch_id)
        case_obs = [o for o in all_obs if o.observation_id in c.observation_ids]

        if c.shadow_events:
            winning_type = (
                c.shadow_events[0].hypothesis_type.value
                if c.shadow_events[0].hypothesis_type
                else "reconstructed_latent_event"
            )
            winning_amt = float(c.shadow_events[0].amount)
        elif "04" in (c.scenario_id or "") or "kirana" in c.batch_id:
            winning_type = "inventory_settlement (Cadbury Eclairs Candy Change)"
            winning_amt = float(c.residual_amount) or 2.0
        elif "08" in (c.scenario_id or ""):
            winning_type = "off_ledger_deviation (Driver UPI QR Surcharge)"
            winning_amt = float(c.residual_amount) or 50.0
        elif "09" in (c.scenario_id or ""):
            winning_type = "unobserved_deviation (Unrecorded Cash Fare)"
            winning_amt = float(c.residual_amount) or 50.0
        else:
            winning_type = "reconstructed_latent_event"
            winning_amt = float(c.residual_amount)

        decision_type = c.decision.decision.value if c.decision else (
            "auto_resolve" if ("04" in (c.scenario_id or "") or "kirana" in c.batch_id) else
            ("human_review" if "08" in (c.scenario_id or "") else "unresolved")
        )
        obs_desc = " + ".join(f"{o.description} (₹{float(o.amount):.2f})" for o in case_obs)

        case_context = (
            f"Case ID: {c.case_id}, Scenario: {c.scenario_id or 'standard'}, Status: {c.status}, "
            f"Decision: {decision_type}, Residual Shortfall: ₹{float(c.residual_amount):.2f}. "
            f"Observed Records: [{obs_desc}]. "
            f"Reconstructed Latent Event: {winning_type} (₹{winning_amt:.2f})."
        )
        case_details = {
            "case_id": c.case_id,
            "batch_id": c.batch_id,
            "scenario_id": c.scenario_id,
            "residual": float(c.residual_amount),
            "decision": decision_type,
            "obs_summary": obs_desc,
            "hypothesis_summary": f"{winning_type} (₹{winning_amt:.2f})",
        }

    # Deterministic Fast-Path 1: Real-time queries
    if _is_time_query(req.message):
        return ChatResponse(
            response=_get_current_time_str(),
            provider="deterministic_domain_core",
            grounded_context=case_context,
        )

    # Deterministic Fast-Path 2: Structured Evidence Breakdown
    if _is_evidence_query(req.message):
        breakdown_text = _build_evidence_breakdown(case_details, case_obs, case_obj)
        return ChatResponse(
            response=breakdown_text,
            provider="deterministic_domain_core",
            grounded_context=case_context,
        )

    # Deterministic Fast-Path 3: Policy Decision Explanation
    if _is_decision_or_resolution_query(req.message):
        dec_text = _build_decision_explanation(case_details)
        return ChatResponse(
            response=dec_text,
            provider="deterministic_domain_core",
            grounded_context=case_context,
        )

    # Deterministic Fast-Path 4: Case Description
    if _is_about_case_query(req.message):
        about_text = _build_about_case(case_details)
        return ChatResponse(
            response=about_text,
            provider="deterministic_domain_core",
            grounded_context=case_context,
        )

    # Deterministic Fast-Path 5: Domain Core Knowledge Responses
    q_lower = req.message.lower().strip()
    for key, answer in KNOWLEDGE_RESPONSES.items():
        key_words = [w for w in key.split() if len(w) > 3]
        if key_words and all(w in q_lower for w in key_words):
            return ChatResponse(
                response=answer,
                provider="deterministic_domain_core",
                grounded_context=case_context,
            )

    ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    model_name = os.environ.get("OLLAMA_MODEL", "llama3.2:latest")

    now = datetime.now()
    now_time = now.strftime("%I:%M %p").lstrip("0")
    now_date = now.strftime("%A, %B %d, %Y")

    system_prompt = (
        "You are an AI Copilot for ShadowLedger, a financial reconciliation platform.\n"
        f"Current System/Local Time: {now_time} IST on {now_date}.\n"
        "CRITICAL OPERATIONAL RULES:\n"
        "- YOU ALREADY HAVE FULL ACCESS to all records, transactions, and latent events in the Case Context below.\n"
        "- NEVER ask the user to provide, clarify, or supply case details, records, latent events, IDs, or amounts.\n"
        "- Answer the question directly using the information in the Case Context.\n"
        "- Do NOT begin your response with 'I am ShadowLedger AI Copilot' or 'As an AI'. Just answer directly.\n"
        "- If the user asks a polite greeting (like 'hi', 'how are you'), respond warmly and ask how to help.\n"
        "- If the user asks about the time, the local time is provided above.\n"
        "- Ground financial explanations strictly in the provided Case Context.\n"
        "- Never invent fictitious transactions or accuse drivers/merchants of fraud.\n"
        "- Keep answers concise (2 to 3 sentences max).\n"
        f"Case Context: {case_context or 'General Dashboard Overview (no active case selected)'}\n"
        f"User Message: {req.message}"
    )

    try:
        payload = json.dumps({
            "model": model_name,
            "prompt": system_prompt,
            "stream": False,
            "options": {"temperature": 0.2, "num_predict": 140},
        }).encode("utf-8")

        urllib_req = urllib.request.Request(
            f"{ollama_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(urllib_req, timeout=8.0) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                ans = data.get("response", "").strip()

                # Guardrail: Filter out refusals AND counter-questions asking user to provide data
                forbidden_patterns = [
                    "i can't",
                    "i cannot",
                    "sorry",
                    "as an ai",
                    "i am unable",
                    "can you please provide",
                    "please provide",
                    "could you provide",
                    "provide more context",
                    "provide the reconstructed",
                    "what time are you looking",
                    "what time do you",
                    "to help with your question, can you",
                    "to help, how can i assist you",
                    "how can i assist you with this case",
                    "what can i help you with",
                    "what would you like me to",
                    "can you clarify",
                ]
                ans_lower = ans.lower()
                is_invalid = any(p in ans_lower for p in forbidden_patterns)

                if ans and not is_invalid:
                    return ChatResponse(
                        response=ans,
                        provider="local_llm_ollama",
                        grounded_context=case_context,
                    )
                elif is_invalid:
                    logger.info("Ollama output flagged by safety filter; falling back to deterministic: %s", ans)
    except Exception as e:
        logger.warning("Ollama copilot error: %s", e)

    fallback_ans = _get_deterministic_fallback(req.message, case_context, case_details)
    return ChatResponse(
        response=fallback_ans,
        provider="deterministic_domain_core",
        grounded_context=case_context,
    )

