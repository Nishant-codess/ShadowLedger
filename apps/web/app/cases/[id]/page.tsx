"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { formatINR } from "../../../lib/utils";
import { fetchCase, CaseDetail } from "../../../lib/api";

export default function CaseDetailPage() {
  const params = useParams();
  const caseId = params.id as string;
  const [caseDetail, setCaseDetail] = useState<CaseDetail | null>(null);
  const [loading, setLoading] = useState(true);

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

  if (loading) {
    return <div className="py-20 text-center text-slate-500 font-mono text-sm">Loading case workspace...</div>;
  }

  if (!caseDetail) {
    return (
      <div className="text-center py-20">
        <h2 className="text-xl font-bold text-white">Case Not Found</h2>
        <p className="text-sm text-slate-400 mt-1">The requested investigation case does not exist.</p>
        <Link href="/exceptions" className="mt-4 inline-block text-emerald-400 font-mono text-xs">
          &larr; Back to Exception Queue
        </Link>
      </div>
    );
  }

  const decisionType = caseDetail.decision?.decision || "unresolved";
  const confidence = caseDetail.decision?.evidence_confidence || 0;
  const isAuto = decisionType === "auto_resolve";
  const isHuman = decisionType === "human_review";

  return (
    <div className="space-y-6">
      {/* Navigation and Case Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <Link href="/exceptions" className="text-xs text-slate-400 hover:text-white font-mono flex items-center space-x-1 mb-2">
            <span>&larr; Exception Queue</span>
          </Link>
          <div className="flex items-center space-x-3">
            <h1 className="text-2xl font-bold text-white tracking-tight">{caseDetail.case_id}</h1>
            <span
              className={`px-2.5 py-0.5 rounded text-xs font-mono uppercase font-bold border ${
                isAuto
                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                  : isHuman
                  ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                  : "bg-rose-500/10 text-rose-400 border-rose-500/20"
              }`}
            >
              {decisionType}
            </span>
            {caseDetail.scenario_id && (
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-300">
                {caseDetail.scenario_id}
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center space-x-6 text-right font-mono">
          <div>
            <div className="text-xs text-slate-400">Evidence Confidence</div>
            <div className="text-xl font-bold text-emerald-400">{(confidence * 100).toFixed(0)}%</div>
          </div>
          <div>
            <div className="text-xs text-slate-400">Residual Discrepancy</div>
            <div className="text-xl font-bold text-amber-400">{formatINR(caseDetail.residual_amount)}</div>
          </div>
        </div>
      </div>

      {/* Official vs Shadow Ledger Comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Official Ledger Records */}
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-5">
          <div className="flex items-center justify-between border-b border-slate-800/60 pb-3 mb-4">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-blue-400"></span>
              <span>Official Ledger (Observed Source Facts)</span>
            </h2>
            <span className="text-xs font-mono text-slate-500">
              {caseDetail.observations?.length || 0} Records
            </span>
          </div>

          <div className="space-y-3">
            {caseDetail.observations && caseDetail.observations.length > 0 ? (
              caseDetail.observations.map((obs) => (
                <div key={obs.observation_id} className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 font-mono text-xs">
                  <div className="flex justify-between items-center text-slate-400 mb-1">
                    <span className="uppercase text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                      {obs.source_system} &bull; {obs.event_type}
                    </span>
                    <span className="text-white font-bold">{formatINR(obs.amount)}</span>
                  </div>
                  <div className="text-slate-300 text-[11px] truncate">{obs.description || obs.observation_id}</div>
                  <div className="text-slate-500 text-[10px] mt-1">{obs.timestamp}</div>
                </div>
              ))
            ) : (
              <div className="text-slate-500 text-xs font-mono py-4 text-center">
                {caseDetail.observation_ids.length} observation ID(s) linked
              </div>
            )}
          </div>
        </div>

        {/* Shadow Ledger Inferred Events */}
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-5">
          <div className="flex items-center justify-between border-b border-slate-800/60 pb-3 mb-4">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-purple-400"></span>
              <span>Shadow Ledger (Latent Economic Reconstruction)</span>
            </h2>
            <span className="text-xs font-mono text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded">
              {caseDetail.shadow_events?.length || 0} Inferred Events
            </span>
          </div>

          <div className="space-y-3">
            {caseDetail.shadow_events && caseDetail.shadow_events.length > 0 ? (
              caseDetail.shadow_events.map((se) => (
                <div key={se.event_id} className="p-3 rounded-lg bg-purple-950/20 border border-purple-800/40 font-mono text-xs">
                  <div className="flex justify-between items-center text-purple-300 mb-1">
                    <span className="uppercase text-[10px] px-1.5 py-0.5 rounded bg-purple-900/60 text-purple-200">
                      {se.status} &bull; {se.event_type}
                    </span>
                    <span className="text-emerald-400 font-bold">{formatINR(se.amount)}</span>
                  </div>
                  <div className="text-slate-300 text-[11px]">
                    Hypothesis: <span className="text-purple-300 font-bold">{se.hypothesis_type || "LATENT_EVENT"}</span>
                  </div>
                  <div className="text-slate-500 text-[10px] mt-1">{se.timestamp}</div>
                </div>
              ))
            ) : (
              <div className="p-6 rounded-lg bg-slate-950/40 border border-slate-800/60 border-dashed text-center font-mono text-xs text-slate-400">
                <div className="text-slate-300 font-bold mb-1">No latent shadow events generated</div>
                <p className="text-[11px] text-slate-500">
                  This discrepancy requires direct operational inquiry or off-ledger investigation.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Case-Local Value-Flow Graph Structure */}
      {caseDetail.graph_json && (
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-5">
          <div className="flex items-center justify-between border-b border-slate-800/60 pb-3 mb-4">
            <div>
              <h2 className="text-sm font-bold text-white uppercase tracking-wider">
                Case-Local Value-Flow Graph Network
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Directed graph connecting observed transactions, inventory assets, and latent hypothesis nodes
              </p>
            </div>
            <div className="text-xs font-mono text-slate-400">
              {caseDetail.graph_json.node_count} Nodes &bull; {caseDetail.graph_json.link_count} Edges
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-xs">
            {/* Nodes */}
            <div className="space-y-2">
              <div className="text-[11px] uppercase text-slate-400 tracking-wider">Graph Nodes</div>
              <div className="space-y-1.5 max-h-48 overflow-y-auto pr-2">
                {caseDetail.graph_json.nodes.map((n) => (
                  <div key={n.id} className="p-2 rounded bg-slate-950/60 border border-slate-800 flex justify-between items-center">
                    <div>
                      <span className="text-slate-300 font-bold">{n.label}</span>
                      <span className="text-slate-500 text-[10px] ml-2">({n.node_type})</span>
                    </div>
                    <span className="text-emerald-400">{formatINR(n.amount)}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Links */}
            <div className="space-y-2">
              <div className="text-[11px] uppercase text-slate-400 tracking-wider">Value Flow Edges</div>
              <div className="space-y-1.5 max-h-48 overflow-y-auto pr-2">
                {caseDetail.graph_json.links.map((l, i) => (
                  <div key={i} className="p-2 rounded bg-slate-950/60 border border-slate-800 flex justify-between items-center">
                    <div>
                      <span className="text-slate-400 truncate text-[11px]">{l.source}</span>
                      <span className="text-slate-600 mx-1.5">&rarr;</span>
                      <span className="text-slate-400 truncate text-[11px]">{l.target}</span>
                    </div>
                    <span className="text-cyan-400">{formatINR(l.amount)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Decision Rationale & Reason Codes */}
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-5">
        <h2 className="text-sm font-bold text-white uppercase tracking-wider mb-2">
          Decision Gate Evaluation & Reason Codes
        </h2>
        <div className="flex flex-wrap gap-2 mt-3">
          {caseDetail.decision?.reason_codes?.map((rc, i) => (
            <span key={i} className="px-2.5 py-1 rounded bg-slate-800 border border-slate-700 text-xs font-mono text-slate-300">
              {rc}
            </span>
          )) || <span className="text-xs font-mono text-slate-500">None</span>}
        </div>
      </div>
    </div>
  );
}
