"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { formatINR } from "../../../lib/utils";
import { fetchCase, performCaseAction, CaseDetail } from "../../../lib/api";
import { ValueFlowGraph } from "../../../components/ValueFlowGraph";
import { EvidenceConfidenceCard } from "../../../components/EvidenceConfidenceCard";
import { LocalAIExplanationCard } from "../../../components/LocalAIExplanationCard";

export default function CaseDetailPage() {
  const params = useParams();
  const caseId = params.id as string;
  const [caseDetail, setCaseDetail] = useState<CaseDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [operatorNotes, setOperatorNotes] = useState("");
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

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

  if (loading) {
    return (
      <div className="py-24 text-center font-mono text-sm text-slate-500">
        Loading case workspace...
      </div>
    );
  }

  if (!caseDetail) {
    return (
      <div className="text-center py-20 font-mono space-y-3">
        <h2 className="text-xl font-bold text-white">Case Not Found</h2>
        <p className="text-sm text-slate-400">The requested investigation case does not exist.</p>
        <Link href="/exceptions" className="inline-block text-purple-400 text-xs">
          &larr; Back to Exception Queue
        </Link>
      </div>
    );
  }

  const decisionType = caseDetail.decision?.decision || "unresolved";
  const confidence = caseDetail.decision?.evidence_confidence || 0;
  const isAuto = decisionType === "auto_resolve";
  const isHuman = decisionType === "human_review";
  const isOffLedger = (caseDetail.scenario_id || "").includes("08") ||
    (caseDetail.scenario_id || "").includes("09") ||
    (caseDetail.scenario_id || "").includes("10") ||
    (caseDetail.decision?.reason_codes || []).some((rc) => rc.includes("OFF_LEDGER"));

  const hasIndirectTrace = caseDetail.observations?.some(
    (o) => o.source_system === "external_trace" || o.description.includes("QR")
  );

  return (
    <div className="space-y-8 font-mono text-xs">
      {/* Top Header & Investigation Breadcrumb */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div className="space-y-2">
          <Link
            href="/exceptions"
            className="text-[11px] text-slate-400 hover:text-white flex items-center space-x-1"
          >
            <span>&larr; Return to Exception Queue</span>
          </Link>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-extrabold text-white tracking-tight font-sans">
              Case Investigation Workspace: {caseDetail.case_id}
            </h1>
            <span
              className={`px-3 py-1 rounded-full uppercase font-bold text-xs border ${
                isAuto
                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                  : isHuman
                  ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                  : "bg-rose-500/10 text-rose-400 border-rose-500/20"
              }`}
            >
              {decisionType}
            </span>
            {caseDetail.status !== "open" && (
              <span className="px-2.5 py-1 rounded uppercase font-bold text-[10px] bg-purple-500/20 text-purple-300 border border-purple-500/30">
                Status: {caseDetail.status.replace("_", " ")}
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center space-x-6 text-right">
          <div>
            <div className="text-[10px] uppercase text-slate-400">Evidence Confidence</div>
            <div className="text-xl font-bold text-emerald-400">{(confidence * 100).toFixed(0)}%</div>
          </div>
          <div>
            <div className="text-[10px] uppercase text-slate-400">Residual Discrepancy</div>
            <div className="text-xl font-bold text-amber-400">{formatINR(caseDetail.residual_amount)}</div>
          </div>
        </div>
      </div>

      {/* 4-Level Event Taxonomy Reference Banner */}
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-4">
        <div className="text-[11px] uppercase text-slate-400 font-bold tracking-wider mb-2">
          Applied Four-Level Event Taxonomy
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-[11px]">
          <div className="p-2.5 rounded-lg bg-blue-950/30 border border-blue-600/40 text-blue-200">
            <span className="font-bold">Level 1: OBSERVED</span>
            <p className="text-[10px] text-slate-400 mt-0.5">Authoritative source facts from POS, Bank, Gateway.</p>
          </div>
          <div className="p-2.5 rounded-lg bg-cyan-950/30 border border-cyan-600/40 text-cyan-200">
            <span className="font-bold">Level 2: DERIVED</span>
            <p className="text-[10px] text-slate-400 mt-0.5">Exact calculated events (e.g. 2.0% MDR fee math).</p>
          </div>
          <div className="p-2.5 rounded-lg bg-purple-950/30 border border-purple-600/40 text-purple-200">
            <span className="font-bold">Level 3: INFERRED_LATENT</span>
            <p className="text-[10px] text-slate-400 mt-0.5">Hypothesized unrecorded economic events (e.g. refund, inventory change).</p>
          </div>
          <div className="p-2.5 rounded-lg bg-amber-950/30 border border-amber-600/40 text-amber-200">
            <span className="font-bold">Level 4: UNOBSERVED_DEVIATION</span>
            <p className="text-[10px] text-slate-400 mt-0.5">Off-ledger payments. Prohibited from auto-resolving.</p>
          </div>
        </div>
      </div>

      {/* Off-Ledger Special Safety Warning (for Hero B & SCN_08-10) */}
      {isOffLedger && (
        <div className="p-4 rounded-xl bg-amber-950/30 border border-amber-500/40 text-amber-200 space-y-2">
          <div className="flex items-center space-x-2 font-bold text-xs">
            <span>🛡️ OFF-LEDGER DEVIATION POLICY ENFORCED:</span>
            <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 text-[10px]">NEVER AUTO-RESOLVED</span>
          </div>
          <p className="text-[11px] text-slate-300 leading-relaxed">
            This case represents an unrecorded off-ledger economic movement (e.g., driver direct toll/AC payment).
            By architectural invariant, off-ledger hypotheses are <strong>never presented as confirmed facts</strong> and are
            strictly barred from automated settlement. Direct Evidence: <strong>{hasIndirectTrace ? "Secondary Trace Linked" : "None (Cash/Invisible)"}</strong>.
          </p>
        </div>
      )}

      {/* Official Ledger vs Shadow Ledger Side-by-Side View */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Official Ledger Records (Source Facts) */}
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <h2 className="text-xs font-bold text-white uppercase tracking-wider flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-blue-400"></span>
              <span>Official Ledger (Observed Source Facts)</span>
            </h2>
            <span className="text-[10px] text-slate-400 bg-slate-800 px-2 py-0.5 rounded">
              {caseDetail.observations?.length || 0} Records
            </span>
          </div>

          <div className="space-y-2.5">
            {caseDetail.observations && caseDetail.observations.length > 0 ? (
              caseDetail.observations.map((obs) => (
                <div
                  key={obs.observation_id}
                  className="p-3.5 rounded-lg bg-slate-950/70 border border-slate-800/80 space-y-1.5"
                >
                  <div className="flex justify-between items-center text-slate-400">
                    <span className="uppercase text-[10px] px-2 py-0.5 rounded bg-blue-950/50 border border-blue-600/30 text-blue-300 font-bold">
                      {obs.source_system} &bull; {obs.event_type}
                    </span>
                    <span className="text-white font-bold text-sm">{formatINR(obs.amount)}</span>
                  </div>
                  <div className="text-slate-200 font-bold text-xs">{obs.description}</div>
                  <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1 border-t border-slate-900">
                    <span>ID: {obs.observation_id}</span>
                    <span>{obs.timestamp}</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-slate-500 py-6 text-center">
                {caseDetail.observation_ids.length} observation ID(s) linked
              </div>
            )}
          </div>
        </div>

        {/* Shadow Ledger Reconstructed Economic Events */}
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <h2 className="text-xs font-bold text-white uppercase tracking-wider flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-purple-400"></span>
              <span>Shadow Ledger (Latent Economic Reconstruction)</span>
            </h2>
            <span className="text-[10px] text-purple-300 bg-purple-950/50 border border-purple-800/40 px-2 py-0.5 rounded">
              {caseDetail.shadow_events?.length || 0} Shadow Events
            </span>
          </div>

          <div className="space-y-2.5">
            {caseDetail.shadow_events && caseDetail.shadow_events.length > 0 ? (
              caseDetail.shadow_events.map((se) => (
                <div
                  key={se.event_id}
                  className="p-3.5 rounded-lg bg-purple-950/20 border border-purple-800/40 space-y-1.5"
                >
                  <div className="flex justify-between items-center text-purple-300">
                    <span className="uppercase text-[10px] px-2 py-0.5 rounded bg-purple-900/60 text-purple-200 font-bold">
                      {se.status} &bull; {se.event_type}
                    </span>
                    <span className="text-emerald-400 font-bold text-sm">{formatINR(se.amount)}</span>
                  </div>
                  <div className="text-slate-200 text-xs">
                    Inferred Candidate: <span className="text-purple-300 font-bold">{se.hypothesis_type}</span>
                  </div>
                  <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1 border-t border-purple-950">
                    <span>Shadow ID: {se.event_id}</span>
                    <span>Confidence: {((se.confidence || confidence) * 100).toFixed(0)}%</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="p-8 rounded-lg bg-slate-950/40 border border-slate-800 border-dashed text-center text-slate-400 space-y-1">
                <div className="text-amber-400 font-bold">No latent events materialized</div>
                <p className="text-[11px] text-slate-500">
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

      {/* Evidence Confidence Radar & Local AI Assistant */}
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

      {/* Human-in-the-Loop Operator Actions & Audit Trail */}
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
          <div>
            <h2 className="text-xs font-bold text-white uppercase tracking-wider">
              Human-in-the-Loop Operator Controls
            </h2>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Confirm inferred latent event settlement, escalate for senior accounting review, or reject hypothesis.
            </p>
          </div>
        </div>

        {actionSuccess && (
          <div className="p-3 bg-emerald-950/40 border border-emerald-500/40 text-emerald-300 rounded-lg">
            ✓ {actionSuccess}
          </div>
        )}

        <div className="flex flex-col sm:flex-row items-center gap-3">
          <input
            type="text"
            placeholder="Optional operator investigation notes..."
            value={operatorNotes}
            onChange={(e) => setOperatorNotes(e.target.value)}
            className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
          />

          <div className="flex items-center space-x-2 shrink-0">
            <button
              onClick={() => handleAction("confirm_settlement")}
              disabled={actionLoading}
              className="px-4 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold rounded-lg uppercase tracking-wider transition"
            >
              Approve Settlement
            </button>
            <button
              onClick={() => handleAction("escalate_ops")}
              disabled={actionLoading}
              className="px-4 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-lg uppercase tracking-wider transition"
            >
              Escalate to Senior Ops
            </button>
            <button
              onClick={() => handleAction("reject_hypothesis")}
              disabled={actionLoading}
              className="px-4 py-2 bg-slate-800 hover:bg-rose-900 text-slate-300 hover:text-white font-bold rounded-lg uppercase tracking-wider border border-slate-700 transition"
            >
              Reject
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
