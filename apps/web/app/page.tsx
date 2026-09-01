"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { formatINR, cn } from "../lib/utils";
import {
  fetchLatestMetrics,
  fetchPatterns,
  processBatch,
  triggerHeroDemo,
  BatchSummary,
  PatternCluster,
  HeroDemoResponse,
} from "../lib/api";

export default function CommandCenterPage() {
  const [metrics, setMetrics] = useState<BatchSummary | null>(null);
  const [patterns, setPatterns] = useState<PatternCluster[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeHero, setActiveHero] = useState<string | null>(null);
  const [heroResult, setHeroResult] = useState<HeroDemoResponse | null>(null);
  const [batchSize, setBatchSize] = useState<number>(1000);
  const [seed, setSeed] = useState<number>(42);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    const data = await fetchLatestMetrics();
    if (data && data.batch_id) {
      setMetrics(data);
      const pats = await fetchPatterns(data.batch_id);
      setPatterns(pats);
    }
  }

  async function handleRunBatch() {
    setLoading(true);
    setActiveHero(null);
    setHeroResult(null);
    try {
      const summary = await processBatch(batchSize, seed);
      if (summary) {
        setMetrics(summary);
        const pats = await fetchPatterns(summary.batch_id);
        setPatterns(pats);
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleLaunchHero(heroId: string) {
    setLoading(true);
    setActiveHero(heroId);
    try {
      const demoData = await triggerHeroDemo(heroId);
      if (demoData) {
        setHeroResult(demoData);
        setMetrics(demoData.batch_summary);
        setPatterns(demoData.pattern_clusters);
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8 font-mono">
      {/* Hero Showcase: "Show Me What The Ledger Cannot Explain" */}
      <div className="bg-gradient-to-br from-purple-950/40 via-slate-900/80 to-slate-950 border border-purple-800/40 rounded-2xl p-6 md:p-8 shadow-2xl relative overflow-hidden">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
          <div className="space-y-2 max-w-2xl">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-purple-500/10 border border-purple-500/30 text-purple-300 text-xs tracking-wider uppercase font-bold">
              <span className="w-2 h-2 rounded-full bg-purple-400 animate-ping"></span>
              <span>The Core Differentiator</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight font-sans">
              &ldquo;Show me what the ledger cannot explain.&rdquo;
            </h1>
            <p className="text-xs md:text-sm text-slate-300 font-sans leading-relaxed">
              Traditional ERPs and rule engines stop when amounts fail to match. ShadowLedger reconstructs
              the missing latent economic events (non-cash inventory, off-ledger surcharges, multi-party fee splits)
              and verifies them with rigorous multi-dimensional evidence.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-3">
            <Link
              href="/exceptions"
              className="w-full sm:w-auto px-5 py-3 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs uppercase tracking-wider text-center transition shadow-lg shadow-purple-600/30"
            >
              Investigate Exception Queue &rarr;
            </Link>
          </div>
        </div>

        {/* 3 Interactive Hero Scenario Launchers */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8 pt-6 border-t border-slate-800/80">
          {/* Hero A: Kirana */}
          <div
            onClick={() => handleLaunchHero("hero_a")}
            className={cn(
              "cursor-pointer p-4 rounded-xl border transition-all text-left space-y-2 bg-slate-900/80",
              activeHero === "hero_a"
                ? "border-emerald-500 ring-2 ring-emerald-500/50 bg-emerald-950/20"
                : "border-slate-800 hover:border-slate-700 hover:bg-slate-800/40"
            )}
          >
            <div className="flex items-center justify-between">
              <span className="text-[10px] uppercase tracking-wider font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                Hero Scenario A
              </span>
              <span className="text-[10px] text-slate-400">100% Safe Resolution</span>
            </div>
            <div className="text-xs font-bold text-white">The Kirana Chocolate Problem</div>
            <p className="text-[11px] text-slate-400 leading-normal">
              ₹100 POS sale settled at ₹98 cash. Resolved via linked ₹2 chocolate inventory change.
            </p>
            <div className="pt-1 flex items-center text-[10px] font-bold text-emerald-400">
              {loading && activeHero === "hero_a" ? "Reconstructing..." : "Launch Kirana Demo &rarr;"}
            </div>
          </div>

          {/* Hero B: Mobility Ride-Hailing */}
          <div
            onClick={() => handleLaunchHero("hero_b")}
            className={cn(
              "cursor-pointer p-4 rounded-xl border transition-all text-left space-y-2 bg-slate-900/80",
              activeHero === "hero_b"
                ? "border-amber-500 ring-2 ring-amber-500/50 bg-amber-950/20"
                : "border-slate-800 hover:border-slate-700 hover:bg-slate-800/40"
            )}
          >
            <div className="flex items-center justify-between">
              <span className="text-[10px] uppercase tracking-wider font-bold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                Hero Scenario B
              </span>
              <span className="text-[10px] text-slate-400">Off-Ledger Safety</span>
            </div>
            <div className="text-xs font-bold text-white">The Mobility Cab Problem</div>
            <p className="text-[11px] text-slate-400 leading-normal">
              ₹150 official fare vs ₹200 true payment. Demonstrates QR trace (Review) vs cash (Unresolved).
            </p>
            <div className="pt-1 flex items-center text-[10px] font-bold text-amber-400">
              {loading && activeHero === "hero_b" ? "Reconstructing..." : "Launch Mobility Demo &rarr;"}
            </div>
          </div>

          {/* Hero C: Pattern Collapse */}
          <div
            onClick={() => handleLaunchHero("hero_c")}
            className={cn(
              "cursor-pointer p-4 rounded-xl border transition-all text-left space-y-2 bg-slate-900/80",
              activeHero === "hero_c"
                ? "border-purple-500 ring-2 ring-purple-500/50 bg-purple-950/20"
                : "border-slate-800 hover:border-slate-700 hover:bg-slate-800/40"
            )}
          >
            <div className="flex items-center justify-between">
              <span className="text-[10px] uppercase tracking-wider font-bold text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded border border-purple-500/20">
                Hero Scenario C (P0)
              </span>
              <span className="text-[10px] text-slate-400">Structural Aggregation</span>
            </div>
            <div className="text-xs font-bold text-white">Cross-Case Pattern Collapse</div>
            <p className="text-[11px] text-slate-400 leading-normal">
              60 multi-party discrepancy records collapse into 3 systemic recurring operational root causes.
            </p>
            <div className="pt-1 flex items-center text-[10px] font-bold text-purple-400">
              {loading && activeHero === "hero_c" ? "Discovering..." : "Launch Pattern Demo &rarr;"}
            </div>
          </div>
        </div>

        {/* Hero Active Banner */}
        {heroResult && (
          <div className="mt-6 p-4 rounded-xl bg-slate-950/90 border border-slate-700 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
            <div>
              <span className="text-emerald-400 font-bold">Active Showcase: {heroResult.title}</span>
              <p className="text-[11px] text-slate-400 mt-0.5">{heroResult.description}</p>
            </div>
            {heroResult.cases.length > 0 && (
              <Link
                href={`/cases/${heroResult.cases[0].case_id}`}
                className="px-4 py-2 rounded-lg bg-emerald-500 text-slate-950 font-bold text-xs uppercase tracking-wider text-center shrink-0 hover:bg-emerald-400 transition"
              >
                Inspect Hero Case &rarr;
              </Link>
            )}
          </div>
        )}
      </div>

      {/* Control Bar: Custom Batch Processing */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl bg-slate-900/60 border border-slate-800/80">
        <div>
          <div className="text-xs font-bold text-white uppercase tracking-wider">Custom Batch Evaluation Engine</div>
          <div className="text-[11px] text-slate-400">Execute deterministic synthetic batch reconciliation</div>
        </div>

        <div className="flex items-center space-x-3 text-xs">
          <div className="flex items-center space-x-2 text-slate-400">
            <span>Size:</span>
            <select
              value={batchSize}
              onChange={(e) => setBatchSize(Number(e.target.value))}
              className="bg-slate-800 border border-slate-700 text-white rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            >
              <option value={100}>100 Rows</option>
              <option value={1000}>1,000 Rows</option>
              <option value={10000}>10,000 Rows</option>
            </select>
          </div>

          <div className="flex items-center space-x-2 text-slate-400">
            <span>Seed:</span>
            <input
              type="number"
              value={seed}
              onChange={(e) => setSeed(Number(e.target.value))}
              className="w-16 bg-slate-800 border border-slate-700 text-white rounded px-2 py-1 text-center focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
          </div>

          <button
            onClick={handleRunBatch}
            disabled={loading}
            className={cn(
              "px-4 py-2 rounded-lg font-bold text-xs tracking-wider uppercase transition shadow-lg",
              loading
                ? "bg-slate-800 text-slate-500 cursor-not-allowed"
                : "bg-emerald-500 hover:bg-emerald-400 text-slate-950 shadow-emerald-500/20"
            )}
          >
            {loading && !activeHero ? "Reconstructing..." : "Process Custom Batch"}
          </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Ingested */}
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-5 relative overflow-hidden">
          <div className="text-xs uppercase text-slate-400 tracking-wider">Total Ingested</div>
          <div className="text-3xl font-bold text-white mt-2 font-mono">
            {metrics ? metrics.record_count.toLocaleString() : "0"}
          </div>
          <div className="text-xs text-slate-500 mt-1">Multi-source records</div>
          <div className="absolute right-3 top-3 w-10 h-10 bg-slate-800/40 rounded-lg flex items-center justify-center text-slate-500 font-mono text-sm">
            #
          </div>
        </div>

        {/* Baseline Match Rate */}
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-5 relative overflow-hidden">
          <div className="text-xs uppercase text-slate-400 tracking-wider">Deterministic Match Rate</div>
          <div className="text-3xl font-bold text-blue-400 mt-2 font-mono">
            {metrics ? `${metrics.match_rate.toFixed(1)}%` : "0.0%"}
          </div>
          <div className="text-xs text-slate-500 mt-1">
            {metrics ? `${metrics.matched_count.toLocaleString()} exact rule matches` : "Awaiting batch"}
          </div>
          <div className="absolute right-3 top-3 w-10 h-10 bg-blue-500/10 border border-blue-500/20 rounded-lg flex items-center justify-center text-blue-400 text-sm">
            ✓
          </div>
        </div>

        {/* Exceptions Structured */}
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-5 relative overflow-hidden">
          <div className="text-xs uppercase text-slate-400 tracking-wider">Exceptions Structured</div>
          <div className="text-3xl font-bold text-amber-400 mt-2 font-mono">
            {metrics ? metrics.exception_count.toLocaleString() : "0"}
          </div>
          <div className="text-xs text-slate-500 mt-1">
            {metrics ? `${metrics.human_review_count || 0} Review | ${metrics.unresolved_count || 0} Unresolved` : "0 cases"}
          </div>
          <div className="absolute right-3 top-3 w-10 h-10 bg-amber-500/10 border border-amber-500/20 rounded-lg flex items-center justify-center text-amber-400 text-sm">
            !
          </div>
        </div>

        {/* Throughput */}
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-5 relative overflow-hidden">
          <div className="text-xs uppercase text-slate-400 tracking-wider">Engine Throughput</div>
          <div className="text-3xl font-bold text-emerald-400 mt-2 font-mono">
            {metrics ? `${metrics.throughput_records_per_sec.toLocaleString()}` : "0"}
          </div>
          <div className="text-xs text-slate-500 mt-1">records / second</div>
          <div className="absolute right-3 top-3 w-10 h-10 bg-emerald-500/10 border border-emerald-500/20 rounded-lg flex items-center justify-center text-emerald-400 text-sm">
            ⚡
          </div>
        </div>
      </div>

      {/* Cross-Case Pattern Discovery Panel (P0) */}
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800/60 pb-4">
          <div>
            <h2 className="text-base font-semibold text-white flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-purple-400 animate-ping"></span>
              <span>Cross-Case Pattern Discovery (P0)</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Aggregated structural anomaly clusters &bull; &ldquo;N exceptions &rarr; 1 likely common operational cause&rdquo;
            </p>
          </div>
          <span className="text-xs text-purple-400 bg-purple-500/10 border border-purple-500/20 px-2.5 py-1 rounded-full">
            {patterns.length} Pattern Clusters Discovered
          </span>
        </div>

        {patterns.length === 0 ? (
          <div className="py-8 text-center text-xs text-slate-500">
            Launch Hero C or process a custom batch to discover recurring structural patterns across exception cases.
          </div>
        ) : (
          <div className="divide-y divide-slate-800/60">
            {patterns.map((p) => (
              <div key={p.cluster_id} className="py-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-xs text-white">{p.pattern_signature}</span>
                    <span className="px-2 py-0.5 rounded text-[10px] bg-purple-500/20 text-purple-300">
                      {p.exception_count} Cases Linked
                    </span>
                  </div>
                  <p className="text-xs text-slate-300">{p.likely_common_cause}</p>
                </div>

                <div className="text-right flex-shrink-0">
                  <div className="text-xs text-slate-400">Total Value at Risk</div>
                  <div className="text-sm font-bold text-amber-400">{formatINR(p.total_value_at_risk)}</div>
                  <div className="text-[10px] text-emerald-400">Evidence: {(p.evidence_strength * 100).toFixed(0)}%</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Financial Value Conservation Overview */}
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-6 space-y-6">
        <div className="flex items-center justify-between border-b border-slate-800/60 pb-4">
          <div>
            <h2 className="text-base font-semibold text-white">Financial Value Conservation Overview</h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Ingested Gross Volume vs Reconstructed Economic Value vs Residual Shortfall
            </p>
          </div>
          {metrics && (
            <span className="text-xs text-slate-500 bg-slate-800 px-2 py-1 rounded">
              Batch: {metrics.batch_id}
            </span>
          )}
        </div>

        <div className="space-y-6">
          {/* Total Volume */}
          <div>
            <div className="flex justify-between text-xs mb-2">
              <span className="text-slate-400">Total Ingested Gross Volume</span>
              <span className="text-white font-bold">{metrics ? formatINR(metrics.total_volume_inr) : "₹0.00"}</span>
            </div>
            <div className="w-full h-3 bg-slate-800 rounded-full overflow-hidden">
              <div className="h-full bg-slate-400" style={{ width: "100%" }}></div>
            </div>
          </div>

          {/* Explained Volume */}
          <div>
            <div className="flex justify-between text-xs mb-2">
              <span className="text-emerald-400 flex items-center space-x-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                <span>Explained Volume (Proven Matches + Latent Inferences)</span>
              </span>
              <span className="text-emerald-400 font-bold">
                {metrics ? formatINR(metrics.explained_volume_inr) : "₹0.00"}
              </span>
            </div>
            <div className="w-full h-3 bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-emerald-500 transition-all duration-500"
                style={{
                  width: metrics && metrics.total_volume_inr > 0
                    ? `${Math.min(100, (metrics.explained_volume_inr / metrics.total_volume_inr) * 100)}%`
                    : "0%",
                }}
              ></div>
            </div>
          </div>

          {/* Unexplained Residual */}
          <div>
            <div className="flex justify-between text-xs mb-2">
              <span className="text-amber-400 flex items-center space-x-1.5">
                <span className="w-2 h-2 rounded-full bg-amber-400"></span>
                <span>Unexplained Value at Risk (Unresolved Exceptions)</span>
              </span>
              <span className="text-amber-400 font-bold">
                {metrics ? formatINR(metrics.unexplained_volume_inr) : "₹0.00"}
              </span>
            </div>
            <div className="w-full h-3 bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-amber-500 transition-all duration-500"
                style={{
                  width: metrics && metrics.total_volume_inr > 0
                    ? `${Math.min(100, (metrics.unexplained_volume_inr / metrics.total_volume_inr) * 100)}%`
                    : "0%",
                }}
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
