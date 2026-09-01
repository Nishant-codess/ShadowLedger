"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { formatINR } from "../../lib/utils";
import { fetchPatterns, PatternCluster } from "../../lib/api";

export default function PatternsPage() {
  const [patterns, setPatterns] = useState<PatternCluster[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPatterns();
  }, []);

  async function loadPatterns() {
    setLoading(true);
    try {
      const data = await fetchPatterns();
      setPatterns(data);
    } finally {
      setLoading(false);
    }
  }

  const totalValueAtRisk = patterns.reduce((sum, p) => sum + p.total_value_at_risk, 0);
  const totalExceptions = patterns.reduce((sum, p) => sum + p.exception_count, 0);

  return (
    <div className="space-y-6 font-mono text-xs">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight font-sans">
            Fleet Cross-Case Pattern Discovery (P0)
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Aggregated structural anomaly clusters: &ldquo;N individual exceptions &rarr; 1 likely common operational cause.&rdquo;
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <div className="text-right">
            <div className="text-[10px] uppercase text-slate-400">Total Value at Risk</div>
            <div className="text-sm font-bold text-amber-400">{formatINR(totalValueAtRisk)}</div>
          </div>
          <span className="text-purple-400 bg-purple-500/10 border border-purple-500/30 px-3 py-1.5 rounded-lg font-bold">
            {patterns.length} Clusters &bull; {totalExceptions} Cases
          </span>
        </div>
      </div>

      {loading ? (
        <div className="py-20 text-center text-slate-500">
          Discovering cross-case patterns across exception clusters...
        </div>
      ) : patterns.length === 0 ? (
        <div className="bg-slate-900/40 border border-slate-800/80 rounded-xl p-12 text-center space-y-3">
          <div className="text-slate-300 font-bold">No pattern clusters discovered</div>
          <p className="text-slate-500 max-w-sm mx-auto">
            Launch Hero C or process a custom batch from the Command Center to discover structural patterns.
          </p>
          <Link
            href="/"
            className="inline-block px-4 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold rounded-lg uppercase tracking-wider transition"
          >
            Go to Command Center
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {patterns.map((p) => (
            <div
              key={p.cluster_id}
              className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-6 space-y-4 shadow-xl relative overflow-hidden"
            >
              <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                <div className="flex items-center space-x-2">
                  <span className="w-2 h-2 rounded-full bg-purple-400 animate-pulse"></span>
                  <span className="font-bold text-xs text-white uppercase tracking-wider">
                    {p.pattern_signature}
                  </span>
                </div>
                <span className="px-2.5 py-0.5 rounded bg-purple-500/20 text-purple-300 font-bold text-[10px]">
                  {p.exception_count} Cases
                </span>
              </div>

              <div>
                <div className="text-[10px] uppercase text-slate-400 mb-1">Likely Common Operational Cause</div>
                <p className="text-xs text-slate-200 leading-relaxed bg-slate-950/60 p-3 rounded-lg border border-slate-800">
                  {p.likely_common_cause}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3 pt-2">
                <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                  <div className="text-[10px] uppercase text-slate-400">Total Value at Risk</div>
                  <div className="text-sm font-bold text-amber-400 mt-0.5">{formatINR(p.total_value_at_risk)}</div>
                </div>
                <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                  <div className="text-[10px] uppercase text-slate-400">Evidence Strength</div>
                  <div className="text-sm font-bold text-emerald-400 mt-0.5">{(p.evidence_strength * 100).toFixed(0)}%</div>
                </div>
              </div>

              <div className="pt-2 flex items-center justify-between">
                <span className="text-[10px] text-slate-500">Cluster ID: {p.cluster_id}</span>
                <Link
                  href="/exceptions"
                  className="text-purple-400 hover:text-purple-300 text-xs font-bold"
                >
                  View Linked Cases &rarr;
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
