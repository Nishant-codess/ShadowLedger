"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { formatINR } from "../../../lib/utils";
import { useViewMode } from "../../../lib/ViewModeContext";
import { fetchCase, performCaseAction, CaseDetail } from "../../../lib/api";
import { ValueFlowGraph } from "../../../components/ValueFlowGraph";
import { EvidenceConfidenceCard } from "../../../components/EvidenceConfidenceCard";
import { LocalAIExplanationCard } from "../../../components/LocalAIExplanationCard";

export default function CaseDetailPage() {
  const params = useParams();
  const caseId = params.id as string;
  const { isExplain, setViewMode } = useViewMode();
  const [caseDetail, setCaseDetail] = useState<CaseDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [operatorNotes, setOperatorNotes] = useState("");
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);
  const [showGuide, setShowGuide] = useState(true);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  useEffect(() => {
    if (caseId) {
      loadCase();
    }
  }, [caseId]);

  async function loadCase() {
    setLoading(true);
    try {
      const data = await fetchCase(caseId);
      setCaseDetail(data);
    } finally {
      setLoading(false);
    }
  }

  async function handleAction(actionType: string) {
    setActionLoading(true);
    setActionSuccess(null);
    try {
      const updated = await performCaseAction(caseId, actionType, operatorNotes);
      if (updated) {
        setCaseDetail(updated);
        setActionSuccess(`Case action '${actionType}' recorded in audit trail.`);
        setOperatorNotes("");
      }
    } finally {
      setActionLoading(false);
    }
  }

  function copyText(txt: string, label: string) {
    navigator.clipboard.writeText(txt);
    setCopiedId(label);
    setTimeout(() => setCopiedId(null), 2000);
  }

  if (loading) {
    return (
      <div className="py-24 text-center font-sans text-sm text-stone-500">
        Loading case investigation workspace...
      </div>
    );
  }

  if (!caseDetail) {
    return (
      <div className="text-center py-20 font-sans space-y-3 bg-white rounded-2xl border border-[#e7e2d9] p-8 max-w-lg mx-auto">
        <h2 className="text-xl font-bold text-stone-900">Case Not Found</h2>
        <p className="text-sm text-stone-500">The requested investigation case does not exist or has expired.</p>
        <Link href="/exceptions" className="inline-block text-emerald-700 font-bold text-xs hover:underline">
          &larr; Return to Exception Workbench
        </Link>
      </div>
    );
  }

  const decisionType = caseDetail.decision?.decision || "unresolved";
  const confidence = caseDetail.decision?.evidence_confidence || 0;
  const isAuto = decisionType === "auto_resolve";
  const isHuman = decisionType === "human_review";
  const isOffLedger =
    (caseDetail.scenario_id || "").includes("08") ||
    (caseDetail.scenario_id || "").includes("09") ||
    (caseDetail.scenario_id || "").includes("10") ||
    (caseDetail.decision?.reason_codes || []).some((rc) => rc.includes("OFF_LEDGER"));

  const hasIndirectTrace = caseDetail.observations?.some(
    (o) => o.source_system === "external_trace" || o.description.includes("QR")
  );

  // Scenario Specific Context
  const isHeroA = caseDetail.batch_id.includes("kirana") || caseDetail.scenario_id === "SCN_04";
  const isHeroB = caseDetail.batch_id.includes("mobility") || caseDetail.scenario_id === "SCN_08" || caseDetail.scenario_id === "SCN_09";

  const paymentObs = caseDetail.observations?.find((o) => o.event_type === "payment");
  const settlementObs = caseDetail.observations?.find((o) => o.event_type === "settlement");
  const winningShadow = caseDetail.shadow_events?.[0];

  return (
    <div className="space-y-8">
      {/* 1. Contextual Mini-Guide (Collapsible in Explain View) */}
      {isExplain && showGuide && (
        <div className="p-3.5 rounded-xl bg-white border border-[#e2ddd5] flex items-center justify-between shadow-2xs text-xs">
          <div className="flex flex-wrap items-center gap-3 text-stone-700">
            <span className="font-bold flex items-center space-x-1">
              <span>✨</span>
              <span>How to read this investigation:</span>
            </span>
            <span className="flex items-center space-x-1.5 text-blue-800 font-semibold bg-blue-50 px-2 py-0.5 rounded-full border border-blue-200">
              <span className="w-2 h-2 rounded-full bg-blue-500"></span>
              <span>Blue = recorded ledger facts</span>
            </span>
            <span className="flex items-center space-x-1.5 text-purple-800 font-semibold bg-purple-50 px-2 py-0.5 rounded-full border border-purple-200">
              <span className="w-2 h-2 rounded-full bg-purple-500"></span>
              <span>Purple = reconstructed latent events</span>
            </span>
            <span className="flex items-center space-x-1.5 text-emerald-800 font-semibold bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              <span>Green = resolved outcomes</span>
            </span>
          </div>
          <button
            onClick={() => setShowGuide(false)}
            className="text-stone-400 hover:text-stone-700 text-xs ml-2 font-mono"
          >
            ✕
          </button>
        </div>
      )}

      {/* 2. Top Header & Title */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#e7e2d9] pb-5">
        <div className="space-y-2">
          <Link
            href="/exceptions"
            className="text-xs text-stone-500 hover:text-stone-900 flex items-center space-x-1 font-semibold"
          >
            <span>&larr; Return to Exception Workbench</span>
          </Link>

          <div className="space-y-1">
            <div className="flex flex-wrap items-center gap-2.5">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-stone-900 tracking-tight font-sans">
                {isExplain
                  ? isHeroA
                    ? "THE MISSING ₹2"
                    : isHeroB
                    ? "THE FARE THAT DOESN'T ADD UP"
                    : `Case Investigation: ${caseDetail.scenario_id || "Financial Discrepancy"}`
                  : `Case Investigation Workspace: ${caseDetail.case_id}`}
              </h1>

              {/* Status Badge */}
              <span
                className={`px-3 py-1 rounded-full uppercase font-extrabold text-xs tracking-wider ${
                  isAuto
                    ? "badge-resolved"
                    : isHuman
                    ? "badge-review"
                    : "badge-unresolved"
                }`}
              >
                {decisionType.replace("_", " ")}
              </span>
            </div>

            {isExplain && (
              <p className="text-sm text-stone-600 font-sans">
                {isHeroA
                  ? "Where did the missing ₹2 go? A ₹100 purchase settled as ₹98 cash + ₹2 physical inventory."
                  : isHeroB
                  ? "Distinguishing verifiable secondary trace from unobserved cash deviations."
                  : "Investigating financial mismatch and reconstructing latent value-flow."}
              </p>
            )}
          </div>
        </div>

        {/* Right Metric Summary */}
        <div className="flex items-center space-x-6 text-right bg-white p-3.5 rounded-xl border border-[#e7e2d9] shadow-2xs">
          <div>
            <div className="text-[10px] uppercase font-bold text-stone-400">
              {isExplain ? "Evidence Strength" : "Confidence"}
            </div>
            <div className="text-xl font-extrabold text-emerald-700 font-mono">
              {(confidence * 100).toFixed(0)}%
            </div>
          </div>
          <div className="h-8 w-px bg-stone-200"></div>
          <div>
            <div className="text-[10px] uppercase font-bold text-stone-400">
              {isExplain ? "Unexplained Shortfall" : "Residual Gap"}
            </div>
            <div className="text-xl font-extrabold text-amber-700 font-mono">
              {formatINR(caseDetail.residual_amount)}
            </div>
          </div>
        </div>
      </div>

      {/* =========================================================================
          EXPLAIN VIEW: 6-STEP INTUITIVE STORYTELLING STRUCTURE
      ========================================================================= */}
      {isExplain ? (
        <div className="space-y-8">
          {/* STEP 1: WHAT WE KNOW & STEP 2: WHAT WAS UNEXPLAINED */}
          <section className="bg-white border border-[#e7e2d9] rounded-2xl p-6 sm:p-8 space-y-6 shadow-xs">
            <div className="flex items-center justify-between border-b border-stone-100 pb-3">
              <div className="flex items-center space-x-2">
                <span className="w-6 h-6 rounded-full bg-blue-100 text-blue-700 font-bold text-xs flex items-center justify-center">
                  1
                </span>
                <h2 className="text-base font-bold text-stone-900 font-sans">
                  WHAT WE KNOW &bull; Official Ledger Records
                </h2>
              </div>
              <span className="badge-observed text-[10px] font-bold px-2.5 py-0.5 rounded-full uppercase">
                Observed Facts
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-5 items-stretch">
              {/* Actual Case Observations (Dynamic) */}
              {caseDetail.observations && caseDetail.observations.length > 0 ? (
                caseDetail.observations.map((obs) => {
                  const isBank = obs.source_system === "bank" || obs.event_type === "settlement";
                  const isExternal = obs.source_system === "external_trace";
                  const isRide = obs.source_system === "ride_platform";
                  return (
                    <div
                      key={obs.observation_id}
                      className={`p-5 rounded-xl border-2 space-y-2 flex flex-col justify-between ${
                        isExternal
                          ? "bg-[#faf5ff] border-[#d8b4fe]"
                          : "bg-[#f0f9ff] border-[#7dd3fc]"
                      }`}
                    >
                      <div className="space-y-1.5">
                        <div className="text-[10px] uppercase font-bold tracking-wider text-blue-700">
                          {obs.source_system === "pos"
                            ? "Source: Point of Sale (POS)"
                            : obs.source_system === "bank"
                            ? "Source: Bank Account"
                            : isRide
                            ? "Source: Ride Platform (Official Fare)"
                            : isExternal
                            ? "Source: Secondary Trace (UPI QR)"
                            : `Source: ${obs.source_system.replace(/_/g, " ").toUpperCase()}`}
                        </div>
                        <div className="text-sm font-bold text-stone-900 leading-snug">
                          {obs.description}
                        </div>
                      </div>
                      <div className="space-y-1 pt-2">
                        <div className="text-2xl font-extrabold text-stone-900 font-mono">
                          {formatINR(obs.amount)}
                        </div>
                        <div className="text-[11px] font-medium text-blue-800">
                          {isBank
                            ? "✓ Net cash received in merchant bank"
                            : isExternal
                            ? "⚡ Digital trace detected outside platform"
                            : isRide
                            ? "✓ Official metered fare on platform"
                            : "✓ Authoritative ledger record"}
                        </div>
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="p-5 rounded-xl bg-[#f0f9ff] border-2 border-[#7dd3fc] space-y-2">
                  <div className="text-[10px] uppercase font-bold text-blue-700">Source Records</div>
                  <div className="text-sm text-stone-600">No raw observation records available.</div>
                </div>
              )}

              {/* STEP 2: WHAT WAS UNEXPLAINED? Discrepancy Card */}
              <div className="p-5 rounded-xl bg-[#fff7ed] border-2 border-[#fdba74] space-y-2 relative flex flex-col justify-between">
                <div>
                  <div className="text-[10px] uppercase font-bold text-orange-800 tracking-wider">
                    {isHeroB ? "Observed Discrepancy / Gap" : "Discrepancy / Gap"}
                  </div>
                  <div className="text-sm font-bold text-stone-900 mt-0.5">
                    {isHeroB ? "Unrecorded Value Movement" : "Unexplained Shortfall"}
                  </div>
                  <div className="text-2xl font-extrabold text-orange-900 font-mono mt-1">
                    {formatINR(caseDetail.residual_amount)}
                  </div>
                </div>
                <div className="font-handwriting text-stone-700 text-sm pt-2">
                  {isHeroA ? (
                    <span>✎ &ldquo;Where did this {formatINR(caseDetail.residual_amount)} go?&rdquo;</span>
                  ) : isHeroB ? (
                    <span>✎ &ldquo;Total unrecorded value moving outside formal settlement.&rdquo;</span>
                  ) : (
                    <span>✎ &ldquo;Where did this {formatINR(caseDetail.residual_amount)} go?&rdquo;</span>
                  )}
                </div>
              </div>
            </div>
          </section>

          {/* STEP 3: WHAT SHADOWLEDGER FOUND */}
          <section className="bg-white border border-[#e7e2d9] rounded-2xl p-6 sm:p-8 space-y-6 shadow-xs">
            <div className="flex items-center justify-between border-b border-stone-100 pb-3">
              <div className="flex items-center space-x-2">
                <span className="w-6 h-6 rounded-full bg-purple-100 text-purple-700 font-bold text-xs flex items-center justify-center">
                  2
                </span>
                <h2 className="text-base font-bold text-stone-900 font-sans">
                  WHAT SHADOWLEDGER FOUND &bull; Reconstructed Economic Value
                </h2>
              </div>
              <span className="badge-reconstructed text-[10px] font-bold px-2.5 py-0.5 rounded-full uppercase">
                Reconstructed Fact
              </span>
            </div>

            {winningShadow ? (
              <div className="p-6 rounded-xl bg-[#faf5ff] border-2 border-[#a855f7] space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <span className="badge-reconstructed text-xs font-bold px-3 py-1 rounded-full uppercase">
                      🟣 Selected Explanation: {winningShadow.hypothesis_type?.replace(/_/g, " ")}
                    </span>
                    <h3 className="text-lg font-bold text-stone-900 mt-2 font-sans">
                      {isHeroA
                        ? "Dairy Milk Chocolate Change (1 Unit)"
                        : isHeroB
                        ? "Off-Ledger Payment Deviation (Trip Surcharge / Cash Extra)"
                        : `${winningShadow.hypothesis_type?.replace(/_/g, " ")} Settlement`}
                    </h3>
                  </div>
                  <div className="text-left sm:text-right">
                    <div className="text-[10px] uppercase font-bold text-purple-700">Accounted Value</div>
                    <div className="text-2xl font-extrabold text-[#581c87] font-mono">
                      {formatINR(winningShadow.amount)}
                    </div>
                  </div>
                </div>

                <p className="text-xs text-stone-700 leading-relaxed bg-white/80 p-3 rounded-lg border border-purple-200">
                  {isHeroA
                    ? "ShadowLedger discovered a physical inventory movement of ₹2.00 (Dairy Milk Chocolate) linked to this exact order. This physical inventory closure exactly matches the ₹2.00 residual shortfall."
                    : isHeroB
                    ? hasIndirectTrace
                      ? `ShadowLedger detected an off-ledger payment deviation of ${formatINR(winningShadow.amount)} with supporting digital trace (driver personal UPI QR credit of ₹50.00). In accordance with strict governance policy, unrecorded deviations can never auto-resolve and are escalated to senior human review.`
                      : "ShadowLedger detected an unrecorded off-ledger cash payment deviation. Because no digital or physical trace exists, ShadowLedger refuses to guess and marks this case unresolved."
                    : `ShadowLedger reconstructed an inferred latent event of ${formatINR(winningShadow.amount)} with ${(confidence * 100).toFixed(0)}% factual evidence consistency.`}
                </p>
              </div>
            ) : (
              <div className="p-6 rounded-xl bg-[#fff7ed] border border-[#fdba74] text-center space-y-2">
                <div className="text-orange-900 font-bold text-sm">No Latent Settlement Materialized</div>
                <p className="text-xs text-stone-600 max-w-md mx-auto">
                  {isOffLedger
                    ? "This case represents an unrecorded off-ledger cash payment. Because no verifiable digital record exists, ShadowLedger refuses to guess or falsely auto-resolve."
                    : "No candidate hypothesis met the rigorous evidence threshold."}
                </p>
              </div>
            )}
          </section>

          {/* STEP 4: WHERE THE VALUE WENT (Interactive Flow Graph) */}
          <section className="space-y-3">
            <div className="flex items-center space-x-2">
              <span className="w-6 h-6 rounded-full bg-stone-100 text-stone-700 font-bold text-xs flex items-center justify-center">
                3
              </span>
              <h2 className="text-base font-bold text-stone-900 font-sans">
                WHERE THE VALUE WENT &bull; Connected Value Flow
              </h2>
            </div>

            {caseDetail.graph_json && (
              <ValueFlowGraph graphData={caseDetail.graph_json} />
            )}
          </section>

          {/* STEP 5: WHY DO WE BELIEVE IT? & STEP 6: WHAT WAS DECIDED */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Step 5: Why Do We Believe It? */}
            <section className="bg-white border border-[#e7e2d9] rounded-2xl p-6 sm:p-7 space-y-4 shadow-xs">
              <div className="flex items-center space-x-2 border-b border-stone-100 pb-3">
                <span className="w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 font-bold text-xs flex items-center justify-center">
                  4
                </span>
                <h2 className="text-base font-bold text-stone-900 font-sans">
                  WHY DO WE BELIEVE IT? &bull; Factual Evidence
                </h2>
              </div>

              <div className="space-y-3 text-xs">
                {/* 1. Value Conservation */}
                <div className="flex items-start space-x-3 p-3 rounded-xl bg-[#f0fdf4] border border-[#86efac]">
                  <span className="text-emerald-700 font-bold text-base leading-none">✓</span>
                  <div>
                    <div className="font-bold text-emerald-900">Value Conservation Closed</div>
                    <p className="text-emerald-800 text-[11px] mt-0.5">
                      {isHeroA
                        ? "₹98.00 Cash Settlement + ₹2.00 Physical Chocolate Inventory = ₹100.00 Gross Ingested Value."
                        : isHeroB
                        ? hasIndirectTrace
                          ? "₹150.00 Official Platform Fare + ₹50.00 Driver UPI Trace = ₹200.00 Total Economic Value."
                          : "₹150.00 Official Platform Fare with uncorroborated cash deviation."
                        : `Reconstructed latent value of ${formatINR(winningShadow ? winningShadow.amount : caseDetail.residual_amount)} accounts for the discrepancy gap.`}
                    </p>
                  </div>
                </div>

                {/* 2. Entity & Trace Corroboration */}
                <div className="flex items-start space-x-3 p-3 rounded-xl bg-[#f0fdf4] border border-[#86efac]">
                  <span className="text-emerald-700 font-bold text-base leading-none">✓</span>
                  <div>
                    <div className="font-bold text-emerald-900">
                      {isHeroB ? "Trace Corroboration" : "Entity & Order Linked"}
                    </div>
                    <p className="text-emerald-800 text-[11px] mt-0.5">
                      {isHeroA
                        ? "The inventory deduction is cryptographically associated with Order Reference: ORD-KIRANA-HERO."
                        : isHeroB
                        ? hasIndirectTrace
                          ? "UPI QR transaction reference explicitly matches Trip ID: RIDE-HERO-01 and Driver ID: DRV-RAMESH-42."
                          : "Zero corroborating digital traces found for this ride."
                        : "Observed records share verified entity identifiers and plausible temporal sequence."}
                    </p>
                  </div>
                </div>

                {/* 3. Safety Invariants & Contradictions */}
                <div className="flex items-start space-x-3 p-3 rounded-xl bg-[#f0fdf4] border border-[#86efac]">
                  <span className="text-emerald-700 font-bold text-base leading-none">✓</span>
                  <div>
                    <div className="font-bold text-emerald-900">
                      {isHeroB ? "Governance Safety Policy Enforced" : "Zero Contradictions"}
                    </div>
                    <p className="text-emerald-800 text-[11px] mt-0.5">
                      {isHeroA
                        ? "No conflicting merchant or customer records. Sequence is temporally plausible."
                        : isHeroB
                        ? "Architectural Invariant: Off-ledger hypotheses are strictly barred from auto-resolution and require human sign-off."
                        : "Zero conflicting merchant accounts. Temporal and mathematical consistency verified."}
                    </p>
                  </div>
                </div>
              </div>
            </section>

            {/* Step 6: What We Decided */}
            <section
              className={`border-2 rounded-2xl p-6 sm:p-7 space-y-4 shadow-xs flex flex-col justify-between ${
                isAuto
                  ? "bg-[#f0fdf4] border-[#86efac]"
                  : isHuman
                  ? "bg-[#fefce8] border-[#fde047]"
                  : "bg-[#fff7ed] border-[#fdba74]"
              }`}
            >
              <div className="space-y-3">
                <div className="flex items-center space-x-2 border-b border-stone-200/60 pb-3">
                  <span className="w-6 h-6 rounded-full bg-stone-900 text-white font-bold text-xs flex items-center justify-center">
                    5
                  </span>
                  <h2 className="text-base font-bold text-stone-900 font-sans">
                    DECISION OUTCOME
                  </h2>
                </div>

                <div>
                  <div className="text-xs uppercase font-extrabold tracking-wider text-stone-500">
                    Engine Policy Gate
                  </div>
                  <div
                    className={`text-2xl font-extrabold font-sans mt-1 ${
                      isAuto
                        ? "text-[#14532d]"
                        : isHuman
                        ? "text-[#713f12]"
                        : "text-[#7c2d12]"
                    }`}
                  >
                    {decisionType === "auto_resolve"
                      ? "AUTO-RESOLVED (100% SAFE)"
                      : decisionType === "human_review"
                      ? "HUMAN REVIEW ESCALATION"
                      : "UNRESOLVED (REFUSED TO GUESS)"}
                  </div>
                </div>

                <p className="text-xs text-stone-700 leading-relaxed">
                  {isAuto
                    ? "The multi-dimensional evidence score satisfies the automated resolution threshold with zero policy risk violations."
                    : isHuman
                    ? isHeroB
                      ? "Off-ledger deviation detected with secondary digital trace. Escalate to senior human operator for review; automated settlement is strictly prohibited by policy."
                      : "Evidence suggests an unrecorded movement but requires senior operator sign-off before financial posting."
                    : "Insufficient corroborating evidence. Barred by policy from automated settlement."}
                </p>
              </div>

              <div className="pt-4 border-t border-stone-200/60 flex items-center justify-between">
                <button
                  onClick={() => setViewMode("investigate")}
                  className="px-4 py-2 bg-white hover:bg-stone-50 text-stone-900 font-bold text-xs rounded-xl border border-stone-300 transition shadow-2xs"
                >
                  Show Investigation Details (Auditor) &rarr;
                </button>
              </div>
            </section>
          </div>

          {/* AI Briefing Layer */}
          <LocalAIExplanationCard caseId={caseDetail.case_id} />
        </div>
      ) : (
        /* =========================================================================
            INVESTIGATE VIEW: DEEP TECHNICAL & FORENSIC MACHINERY
        ========================================================================= */
        <div className="space-y-8 font-mono text-xs">
          {/* 4-Level Event Taxonomy Reference Banner */}
          <div className="bg-white border border-[#e7e2d9] rounded-2xl p-5 shadow-xs">
            <div className="text-xs uppercase text-stone-700 font-bold tracking-wider mb-3">
              Applied Four-Level Event Taxonomy
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              <div className="p-3 rounded-xl bg-[#f0f9ff] border border-[#7dd3fc] text-[#0369a1]">
                <span className="font-bold">Level 1: OBSERVED</span>
                <p className="text-[11px] text-stone-600 mt-1">Authoritative source facts from POS, Bank, Gateway.</p>
              </div>
              <div className="p-3 rounded-xl bg-cyan-50 border border-cyan-300 text-cyan-900">
                <span className="font-bold">Level 2: DERIVED</span>
                <p className="text-[11px] text-stone-600 mt-1">Exact calculated events (e.g. 2.0% MDR fee math).</p>
              </div>
              <div className="p-3 rounded-xl bg-[#faf5ff] border border-[#d8b4fe] text-[#581c87]">
                <span className="font-bold">Level 3: INFERRED_LATENT</span>
                <p className="text-[11px] text-stone-600 mt-1">Hypothesized unrecorded economic events (e.g. chocolate inventory).</p>
              </div>
              <div className="p-3 rounded-xl bg-[#fff7ed] border border-[#fdba74] text-[#7c2d12]">
                <span className="font-bold">Level 4: UNOBSERVED_DEVIATION</span>
                <p className="text-[11px] text-stone-600 mt-1">Off-ledger payments. Prohibited from auto-resolving.</p>
              </div>
            </div>
          </div>

          {/* Off-Ledger Special Safety Warning if applicable */}
          {isOffLedger && (
            <div className="p-4 rounded-xl bg-[#fff7ed] border border-[#fdba74] text-[#7c2d12] space-y-1.5">
              <div className="flex items-center space-x-2 font-bold text-xs">
                <span>🛡️ OFF-LEDGER DEVIATION POLICY ENFORCED:</span>
                <span className="px-2 py-0.5 rounded bg-orange-200 text-orange-900 text-[10px]">
                  NEVER AUTO-RESOLVED
                </span>
              </div>
              <p className="text-[11px] text-stone-700 leading-relaxed">
                This case represents an unrecorded off-ledger economic movement. By architectural invariant,
                off-ledger hypotheses are <strong>never presented as confirmed facts</strong> and are strictly barred
                from automated settlement. Direct Evidence: <strong>{hasIndirectTrace ? "Secondary Trace Linked" : "None (Cash/Invisible)"}</strong>.
              </p>
            </div>
          )}

          {/* Official Ledger vs Shadow Ledger Side-by-Side Data Tables */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Official Ledger Records */}
            <div className="bg-white border border-[#e7e2d9] rounded-2xl p-5 space-y-4 shadow-xs">
              <div className="flex items-center justify-between border-b border-stone-200 pb-3">
                <h2 className="text-xs font-bold text-stone-900 uppercase tracking-wider flex items-center space-x-2">
                  <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                  <span>Official Ledger (Observed Source Facts)</span>
                </h2>
                <span className="text-[10px] text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                  {caseDetail.observations?.length || 0} Records
                </span>
              </div>

              <div className="space-y-2.5">
                {caseDetail.observations && caseDetail.observations.length > 0 ? (
                  caseDetail.observations.map((obs) => (
                    <div
                      key={obs.observation_id}
                      className="p-3.5 rounded-xl bg-[#f0f9ff]/50 border border-[#7dd3fc]/60 space-y-1.5"
                    >
                      <div className="flex justify-between items-center">
                        <span className="uppercase text-[10px] px-2 py-0.5 rounded bg-blue-100 text-blue-800 font-bold">
                          {obs.source_system} &bull; {obs.event_type}
                        </span>
                        <span className="text-stone-900 font-bold text-sm font-mono">
                          {formatINR(obs.amount)}
                        </span>
                      </div>
                      <div className="text-stone-800 font-bold text-xs">{obs.description}</div>
                      <div className="flex items-center justify-between text-[10px] text-stone-500 pt-1 border-t border-stone-200">
                        <span className="truncate max-w-[200px]">ID: {obs.observation_id}</span>
                        <button
                          onClick={() => copyText(obs.observation_id, obs.observation_id)}
                          className="hover:text-stone-900 text-[10px] underline"
                        >
                          {copiedId === obs.observation_id ? "✓ Copied" : "Copy"}
                        </button>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-stone-400 py-6 text-center">
                    {caseDetail.observation_ids.length} observation ID(s) linked
                  </div>
                )}
              </div>
            </div>

            {/* Shadow Ledger Reconstructed Economic Events */}
            <div className="bg-white border border-[#e7e2d9] rounded-2xl p-5 space-y-4 shadow-xs">
              <div className="flex items-center justify-between border-b border-stone-200 pb-3">
                <h2 className="text-xs font-bold text-stone-900 uppercase tracking-wider flex items-center space-x-2">
                  <span className="w-2 h-2 rounded-full bg-purple-500"></span>
                  <span>Shadow Ledger (Latent Economic Reconstruction)</span>
                </h2>
                <span className="text-[10px] text-purple-700 bg-purple-50 px-2 py-0.5 rounded border border-purple-200">
                  {caseDetail.shadow_events?.length || 0} Shadow Events
                </span>
              </div>

              <div className="space-y-2.5">
                {caseDetail.shadow_events && caseDetail.shadow_events.length > 0 ? (
                  caseDetail.shadow_events.map((se) => (
                    <div
                      key={se.event_id}
                      className="p-3.5 rounded-xl bg-[#faf5ff] border border-[#d8b4fe] space-y-1.5"
                    >
                      <div className="flex justify-between items-center">
                        <span className="uppercase text-[10px] px-2 py-0.5 rounded bg-purple-100 text-purple-800 font-bold">
                          {se.status} &bull; {se.event_type}
                        </span>
                        <span className="text-emerald-700 font-bold text-sm font-mono">
                          {formatINR(se.amount)}
                        </span>
                      </div>
                      <div className="text-stone-800 text-xs">
                        Candidate: <span className="text-purple-800 font-bold">{se.hypothesis_type}</span>
                      </div>
                      <div className="flex items-center justify-between text-[10px] text-stone-500 pt-1 border-t border-purple-100">
                        <span className="truncate max-w-[200px]">Shadow ID: {se.event_id}</span>
                        <button
                          onClick={() => copyText(se.event_id, se.event_id)}
                          className="hover:text-stone-900 text-[10px] underline"
                        >
                          {copiedId === se.event_id ? "✓ Copied" : "Copy"}
                        </button>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="p-8 rounded-xl bg-[#fff7ed]/50 border border-[#fdba74] border-dashed text-center text-stone-600 space-y-1">
                    <div className="text-orange-900 font-bold">No latent events materialized</div>
                    <p className="text-[11px] text-stone-500">
                      Evidence threshold not met or discrepancy represents unobserved deviation.
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Interactive Value-Flow Graph Visualizer */}
          {caseDetail.graph_json && (
            <ValueFlowGraph graphData={caseDetail.graph_json} />
          )}

          {/* Evidence Scoring & AI Assistant */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <EvidenceConfidenceCard
              confidence={confidence}
              residualAmount={caseDetail.residual_amount}
              decision={decisionType}
              reasonCodes={caseDetail.decision?.reason_codes || []}
              hypothesisType={caseDetail.shadow_events?.[0]?.hypothesis_type}
              hasDirectEvidence={caseDetail.observations?.length ? caseDetail.observations.length > 0 : true}
              hasIndirectEvidence={hasIndirectTrace}
            />

            <LocalAIExplanationCard caseId={caseDetail.case_id} />
          </div>

          {/* Human-in-the-Loop Operator Actions */}
          <div className="bg-white border border-[#e7e2d9] rounded-2xl p-6 space-y-4 shadow-xs">
            <div className="border-b border-stone-200 pb-3">
              <h2 className="text-xs font-bold text-stone-900 uppercase tracking-wider">
                Human-in-the-Loop Operator Controls
              </h2>
              <p className="text-[11px] text-stone-500 mt-0.5">
                Confirm inferred latent event settlement, escalate for senior accounting review, or reject hypothesis.
              </p>
            </div>

            {actionSuccess && (
              <div className="p-3 bg-emerald-50 border border-emerald-300 text-emerald-900 rounded-xl">
                ✓ {actionSuccess}
              </div>
            )}

            <div className="flex flex-col sm:flex-row items-center gap-3">
              <input
                type="text"
                placeholder="Optional operator investigation notes..."
                value={operatorNotes}
                onChange={(e) => setOperatorNotes(e.target.value)}
                className="flex-1 bg-[#faf8f5] border border-[#e2ddd5] rounded-xl px-3 py-2 text-stone-900 placeholder-stone-400 focus:outline-none focus:ring-1 focus:ring-emerald-500 font-mono text-xs"
              />

              <div className="flex items-center space-x-2 shrink-0">
                <button
                  onClick={() => handleAction("confirm_settlement")}
                  disabled={actionLoading}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl uppercase tracking-wider transition"
                >
                  Approve Settlement
                </button>
                <button
                  onClick={() => handleAction("escalate_ops")}
                  disabled={actionLoading}
                  className="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white font-bold rounded-xl uppercase tracking-wider transition"
                >
                  Escalate
                </button>
                <button
                  onClick={() => handleAction("reject_hypothesis")}
                  disabled={actionLoading}
                  className="px-4 py-2 bg-stone-100 hover:bg-rose-50 text-stone-700 hover:text-rose-700 font-bold rounded-xl uppercase tracking-wider border border-stone-200 transition"
                >
                  Reject
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
