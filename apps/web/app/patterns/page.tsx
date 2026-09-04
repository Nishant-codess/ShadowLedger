"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { formatINR } from "../../lib/utils";
import { useViewMode } from "../../lib/ViewModeContext";
import { fetchPatterns, triggerHeroDemo, PatternCluster } from "../../lib/api";

export default function PatternsPage() {
  const { isExplain } = useViewMode();
  const [patterns, setPatterns] = useState<PatternCluster[]>([]);
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);

  useEffect(() => {
    loadPatterns();
  }, []);

  async function loadPatterns() {
    setLoading(true);
    try {
      const data = await fetchPatterns();
      if (data.length === 0) {
        // Auto-seed Hero C fleet scenario so the page is never blank
        setSeeding(true);
        const demo = await triggerHeroDemo("hero_c");
        if (demo) {
          setPatterns(demo.pattern_clusters);
        }
      } else {
        setPatterns(data);
      }
    } finally {
      setLoading(false);
      setSeeding(false);
    }
  }


  const totalValueAtRisk = patterns.reduce((sum, p) => sum + p.total_value_at_risk, 0);
  const totalExceptions = patterns.reduce((sum, p) => sum + p.exception_count, 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#e7e2d9] pb-4">
        <div>
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-purple-50 text-purple-800 text-xs font-bold tracking-wide border border-purple-200 mb-2">
            <span>Hero C &bull; Fleet Investigation</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-stone-900 tracking-tight font-sans">
            THE PATTERN HIDING IN THE EXCEPTIONS
          </h1>
          <p className="text-xs sm:text-sm text-stone-600 mt-1 font-sans">
            &ldquo;One mismatch may be noise. Repeated mismatches can reveal a systemic pattern.&rdquo;
          </p>
        </div>

        <div className="flex items-center space-x-3 bg-white p-3 rounded-2xl border border-[#e7e2d9] shadow-2xs">
          <div className="text-right">
            <div className="text-[10px] uppercase font-bold text-stone-400">Total Value at Risk</div>
            <div className="text-sm font-bold text-amber-800 font-mono">{formatINR(totalValueAtRisk)}</div>
          </div>
          <div className="h-6 w-px bg-stone-200"></div>
          <span className="badge-reconstructed text-xs px-3 py-1 rounded-full font-bold">
            {patterns.length} Clusters &bull; {totalExceptions} Cases
          </span>
        </div>
      </div>

      {loading ? (
        <div className="py-20 text-center text-stone-500 text-sm space-y-2">
          <div className="animate-pulse text-purple-700 font-bold">
            {seeding ? "🔍 Discovering fleet patterns across 60 exception clusters..." : "Loading pattern clusters..."}
          </div>
          {seeding && (
            <p className="text-xs text-stone-400">Running Hero C: Fleet Investigation — this takes a moment</p>
          )}
        </div>
      ) : patterns.length === 0 ? (
        <div className="bg-white border border-[#e7e2d9] rounded-2xl p-12 text-center space-y-3 shadow-xs">
          <div className="text-stone-800 font-bold text-base">No pattern clusters discovered</div>
          <p className="text-stone-500 text-xs max-w-sm mx-auto">
            Launch Hero C or process a custom batch from the Command Center to discover structural patterns.
          </p>
          <Link
            href="/"
            className="inline-block px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl text-xs uppercase tracking-wider transition shadow-sm"
          >
            Go to Command Center
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {patterns.map((p) => (
            <div
              key={p.cluster_id}
              className="bg-white border border-[#e7e2d9] rounded-2xl p-6 sm:p-7 space-y-4 shadow-xs relative overflow-hidden flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between border-b border-stone-100 pb-3">
                  <div className="flex items-center space-x-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-purple-500 animate-pulse"></span>
                    <h3 className="font-bold text-sm text-stone-900 uppercase tracking-wider font-mono">
                      {p.pattern_signature}
                    </h3>
                  </div>
                  <span className="badge-reconstructed text-xs px-2.5 py-0.5 rounded-full font-bold">
                    {p.exception_count} Linked Cases
                  </span>
                </div>

                <div>
                  <div className="text-[10px] uppercase font-bold text-stone-400 mb-1">
                    Likely Common Operational Cause
                  </div>
                  <p className="text-xs text-stone-800 leading-relaxed bg-[#faf8f5] p-3.5 rounded-xl border border-[#e7e2d9]">
                    {p.likely_common_cause}
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-3 pt-1">
                  <div className="p-3 bg-[#fff7ed] rounded-xl border border-[#fdba74]">
                    <div className="text-[10px] uppercase font-bold text-orange-800">Value at Risk</div>
                    <div className="text-base font-extrabold text-orange-950 font-mono mt-0.5">
                      {formatINR(p.total_value_at_risk)}
                    </div>
                  </div>
                  <div className="p-3 bg-[#f0fdf4] rounded-xl border border-[#86efac]">
                    <div className="text-[10px] uppercase font-bold text-emerald-800">Evidence Strength</div>
                    <div className="text-base font-extrabold text-emerald-950 font-mono mt-0.5">
                      {(p.evidence_strength * 100).toFixed(0)}% Factual Proof
                    </div>
                  </div>
                </div>
              </div>

              <div className="pt-3 border-t border-stone-100 flex items-center justify-between text-xs">
                <span className="text-[11px] text-stone-400 font-mono">
                  {isExplain ? `Pattern #${p.cluster_id.slice(0, 10)}...` : `Cluster ID: ${p.cluster_id}`}
                </span>
                <Link
                  href="/exceptions"
                  className="text-purple-700 hover:text-purple-900 font-bold flex items-center space-x-1"
                >
                  <span>Inspect Linked Exceptions</span>
                  <span>&rarr;</span>
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
