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

  return (
    <div className="space-y-6">
      {/* Navigation and Case Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <Link href="/exceptions" className="text-xs text-slate-400 hover:text-white font-mono flex items-center space-x-1 mb-2">
            <span>&larr; Exception Queue</span>
          </Link>
          <div className="flex items-center space-x-3">
            <h1 className="text-2xl font-bold text-white tracking-tight">{caseDetail.case_id}</h1>
            <span className="px-2.5 py-0.5 rounded text-xs font-mono uppercase font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
              {caseDetail.decision?.decision || "unresolved"}
            </span>
          </div>
        </div>

        <div className="text-right font-mono">
          <div className="text-xs text-slate-400">Residual Discrepancy</div>
          <div className="text-xl font-bold text-amber-400">{formatINR(caseDetail.residual_amount)}</div>
        </div>
      </div>

      {/* Official vs Shadow Ledger Comparison Header */}
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
            <span className="text-xs font-mono text-slate-500">Chunk 2 Engine</span>
          </div>

          <div className="p-6 rounded-lg bg-slate-950/40 border border-slate-800/60 border-dashed text-center font-mono text-xs text-slate-400">
            <div className="text-amber-400 font-bold mb-1">Deterministic Rule Status: UNRESOLVED</div>
            <p className="text-[11px] text-slate-500 max-w-sm mx-auto">
              Reason Codes: {caseDetail.decision?.reason_codes?.join(", ") || "AMOUNT_MISMATCH"}
            </p>
            <div className="mt-4 inline-block px-3 py-1 rounded bg-slate-900 text-purple-400 border border-purple-500/20 text-[10px] uppercase tracking-wider">
              Awaiting Latent Hypothesis Engine (Chunk 2)
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
