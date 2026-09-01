"""Local AI / Natural Language Investigation Narrative Generator.

Provides evidence-grounded natural language explanations for financial discrepancies.
Integrates with local Ollama/compatible endpoints when available, with an authoritative,
deterministic evidence-grounded fallback generator when offline.

Strict Invariants:
- The LLM is NEVER authoritative over arithmetic, source facts, or final policy decisions.
- Explanations are strictly bounded by structured evidence passed from the engine.
- 100% local-first, zero cloud dependencies.
"""

import json
import logging
import os
import re
import urllib.error
import urllib.request
from decimal import Decimal
from typing import Any

from app.domain.enums import DecisionType, EventStatus, HypothesisType
from app.domain.models import Case, Decision, Hypothesis, Observation

logger = logging.getLogger(__name__)


def sanitize_text(text: str, max_length: int = 250) -> str:
    """Sanitize user/transaction descriptions against prompt injection attempts."""
    if not text:
        return ""
    # Strip potential instruction injection strings
    cleaned = re.sub(r"(?i)(system\s*:|ignore\s+previous|you\s+are\s+now|override|developer\s+mode)", "[filtered]", text)
    # Strip non-printable characters and truncate
    cleaned = "".join(ch for ch in cleaned if ch.isprintable())
    return cleaned[:max_length].strip()


class LocalAIExplainer:
    """Generates evidence-grounded audit narratives using local LLMs with deterministic fallback."""

    def __init__(
        self,
        ollama_base_url: str | None = None,
        model_name: str | None = None,
        timeout_seconds: float = 2.0,
    ) -> None:
        self.ollama_base_url = ollama_base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model_name = model_name or os.environ.get("LLM_MODEL", os.environ.get("OLLAMA_MODEL", "llama3.2:latest"))
        self.provider = os.environ.get("LLM_PROVIDER", "ollama")
        self.timeout_seconds = timeout_seconds

    def generate_case_explanation(
        self,
        case: Case,
        observations: list[Observation],
        winning_hypothesis: Hypothesis | None = None,
        decision: Decision | None = None,
    ) -> dict[str, Any]:
        """Generate a complete investigation narrative for a case."""
        # 1. First build the structured deterministic evidence briefing
        briefing = self._build_deterministic_briefing(case, observations, winning_hypothesis, decision)

        # 2. Try Local LLM for natural phrasing if available
        llm_response = self._try_local_llm(briefing)
        if llm_response:
            briefing["narrative"] = llm_response
            briefing["provider"] = "local_llm_ollama"
        else:
            briefing["narrative"] = briefing["deterministic_narrative"]
            briefing["provider"] = "deterministic_synthesis_fallback"

        return briefing

    def _build_deterministic_briefing(
        self,
        case: Case,
        observations: list[Observation],
        winning_hypothesis: Hypothesis | None,
        decision: Decision | None,
    ) -> dict[str, Any]:
        """Construct deterministic, evidence-grounded facts for the investigation workspace."""
        total_payment = sum((o.amount for o in observations if o.event_type.value == "payment"), Decimal("0.00"))
        total_settlement = sum((o.amount for o in observations if o.event_type.value == "settlement"), Decimal("0.00"))
        residual = case.residual_amount

        hyp_type = winning_hypothesis.hypothesis_type if winning_hypothesis else HypothesisType.UNKNOWN
        confidence = decision.evidence_confidence if decision else (winning_hypothesis.evidence_confidence if winning_hypothesis else 0.0)
        dec_type = decision.decision if decision else DecisionType.UNRESOLVED
        reason_codes = decision.reason_codes if decision else []

        # Executive Summary
        if hyp_type == HypothesisType.INVENTORY_SETTLEMENT:
            headline = f"Non-Monetary Retail Settlement: ₹{float(residual):.2f} residual resolved via linked inventory change."
            economic_story = (
                f"Official POS recorded a sale of ₹{float(total_payment):.2f}, but net bank settlement was "
                f"₹{float(total_settlement):.2f} (shortfall of ₹{float(residual):.2f}). The system identified a verified "
                f"retail item adjustment (e.g. chocolate change) linked to the same order ID with known valuation basis. "
                f"Value conservation is satisfied exactly."
            )
            taxonomy_level = EventStatus.INFERRED_LATENT.value
        elif hyp_type == HypothesisType.OFF_LEDGER_DEVIATION:
            has_indirect = winning_hypothesis and len(winning_hypothesis.indirect_evidence_ids) > 0
            if has_indirect:
                headline = f"Potential Off-Ledger Payment Deviation: ₹{float(residual):.2f} shortfall with supporting indirect digital trace."
                economic_story = (
                    f"Platform records show fare of ₹{float(total_payment):.2f}. An indirect digital payment trace "
                    f"of ₹{float(residual):.2f} was detected matching the driver identifier. Because off-ledger transactions "
                    f"lack official source authorization, this case CANNOT auto-resolve and is routed to Human Review."
                )
            else:
                headline = f"Unobserved Cash Deviation: ₹{float(residual):.2f} unrecorded transaction with zero direct trace."
                economic_story = (
                    f"Discrepancy of ₹{float(residual):.2f} detected without any direct or indirect confirmation trace. "
                    f"Preserved as an unverified economic hypothesis in UNRESOLVED status."
                )
            taxonomy_level = EventStatus.UNOBSERVED_DEVIATION.value
        elif hyp_type == HypothesisType.FEE_ADJUSTMENT:
            headline = f"Gateway MDR Fee Adjustment: ₹{float(residual):.2f} deduction matching standard merchant fee schedule."
            economic_story = (
                f"Gross payment of ₹{float(total_payment):.2f} settled as ₹{float(total_settlement):.2f}. "
                f"The difference of ₹{float(residual):.2f} corresponds exactly to a standard MDR fee percentage. "
                f"Arithmetic closure is proven with 100% confidence."
            )
            taxonomy_level = EventStatus.DERIVED.value
        elif hyp_type == HypothesisType.REFUND:
            headline = f"Unrecorded Partial Customer Refund: ₹{float(residual):.2f} latent customer return."
            economic_story = (
                f"Observed payment of ₹{float(total_payment):.2f} settled for ₹{float(total_settlement):.2f}. "
                f"A latent customer refund of ₹{float(residual):.2f} is inferred. Because official credit memo records "
                f"are absent, this case is escalated to supervisor review."
            )
            taxonomy_level = EventStatus.INFERRED_LATENT.value
        elif hyp_type == HypothesisType.TIMING_OFFSET:
            headline = f"Cross-Batch Settlement Cutoff: ₹{float(residual):.2f} timing offset across settlement windows."
            economic_story = (
                "Exact amount matching transaction found in adjacent settlement window, representing normal "
                "banking cutoff timing rather than operational loss."
            )
            taxonomy_level = EventStatus.DERIVED.value
        else:
            headline = f"Unexplained Discrepancy: ₹{float(residual):.2f} residual requiring manual investigation."
            economic_story = (
                f"No candidate hypothesis met the required evidence threshold to explain the ₹{float(residual):.2f} "
                f"residual between source systems."
            )
            taxonomy_level = EventStatus.OBSERVED.value

        # Formulate structured decision rationale
        if dec_type == DecisionType.AUTO_RESOLVE:
            action_statement = f"AUTO_RESOLVED — Factual evidence confidence ({confidence * 100:.0f}%) exceeds safety threshold with zero contradictions."
        elif dec_type == DecisionType.HUMAN_REVIEW:
            action_statement = f"HUMAN_REVIEW — Escalated to operator review. Reason: {', '.join(reason_codes)}."
        else:
            action_statement = "UNRESOLVED — Held in exception queue pending additional documentation or operational trace."

        full_text = f"{headline}\n\n{economic_story}\n\nPolicy Action: {action_statement}"

        return {
            "case_id": case.case_id,
            "headline": headline,
            "economic_story": economic_story,
            "policy_action": action_statement,
            "deterministic_narrative": full_text,
            "hypothesis_type": hyp_type.value if hasattr(hyp_type, "value") else str(hyp_type),
            "taxonomy_level": taxonomy_level,
            "evidence_confidence": confidence,
            "decision": dec_type.value if hasattr(dec_type, "value") else str(dec_type),
            "reason_codes": reason_codes,
            "total_payment": float(total_payment),
            "total_settlement": float(total_settlement),
            "residual_amount": float(residual),
        }

    def _try_local_llm(self, briefing: dict[str, Any]) -> str | None:
        """Attempt to call local Ollama endpoint if running, with immediate timeout fallback."""
        try:
            prompt = (
                "You are an AI Finance Controller auditor. Summarize this financial discrepancy case concisely "
                "for a human finance operator. Ground your answer strictly in these facts:\n"
                f"- Case ID: {briefing['case_id']}\n"
                f"- Headline: {briefing['headline']}\n"
                f"- Hypothesis: {briefing['hypothesis_type']} (Taxonomy Level: {briefing['taxonomy_level']})\n"
                f"- Evidence Confidence: {briefing['evidence_confidence'] * 100:.1f}%\n"
                f"- Decision Gate: {briefing['decision']}\n"
                f"- Reason Codes: {', '.join(briefing['reason_codes'])}\n"
                f"- Context: {briefing['economic_story']}\n"
                "Provide a 2-3 sentence executive explanation of what happened, what was inferred, and the required action."
            )

            url = f"{self.ollama_base_url}/api/generate"
            payload = json.dumps({
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1},
            }).encode("utf-8")

            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    response_text = data.get("response", "").strip()
                    if response_text:
                        return response_text
        except Exception:
            # Local model unavailable, connection refused, or timed out.
            # Gracefully fallback to deterministic synthesis without logging trace noise.
            return None

        return None
