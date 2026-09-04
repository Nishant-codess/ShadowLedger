"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { formatINR, cn } from "../lib/utils";
import { useViewMode } from "../lib/ViewModeContext";
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
  const router = useRouter();
  const { isExplain } = useViewMode();
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

  async function handleLaunchHero(heroId: string, autoNavigate: boolean = false) {
    setLoading(true);
    setActiveHero(heroId);
    try {
      const demoData = await triggerHeroDemo(heroId);
      if (demoData) {
        setHeroResult(demoData);
        setMetrics(demoData.batch_summary);
        setPatterns(demoData.pattern_clusters);

        if (heroId === "hero_c") {
          // Hero C → navigate to Fleet Patterns page
          router.push("/patterns");
        } else if (autoNavigate && demoData.cases.length > 0) {
          // Hero A / B → navigate directly to the case detail
          router.push(`/cases/${demoData.cases[0].case_id}`);
        }
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8">
      {/* 1. Hero Showcase / Main Product Pitch */}
      <section className="bg-white border border-[#e7e2d9] rounded-2xl p-6 sm:p-8 md:p-10 shadow-xs relative overflow-hidden">
        {/* Decorative Notebook Sticky Accent */}
        <div className="absolute top-4 right-5 sm:right-8 hidden md:block">
          <div className="sticky-note-butter px-4 py-2.5 rounded-lg rotate-1 transform border border-amber-300">
            <span className="font-handwriting text-amber-900 text-lg leading-none block">
              ✨ &ldquo;Reconstructs the hidden value flow&rdquo;
            </span>
          </div>
        </div>

        <div className="max-w-3xl space-y-4">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-[#f3e8ff] border border-[#d8b4fe] text-[#581c87] text-xs font-bold tracking-wide">
            <span className="w-2 h-2 rounded-full bg-purple-500 animate-pulse"></span>
            <span>SHADOWLEDGER VALUE-FLOW ENGINE</span>
          </div>

          <h1 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-stone-900 tracking-tight leading-tight font-sans">
            &ldquo;Show me what the ledger cannot explain.&rdquo;
          </h1>

          <p className="text-base sm:text-lg text-stone-600 font-sans leading-relaxed">
            ShadowLedger investigates financial mismatches, reconstructs possible missing value
            flows (like non-cash inventory change, multi-party fee splits, and timing gaps), shows the
            evidence behind them, and refuses to guess when evidence is insufficient.
          </p>

          {/* Unambiguous Primary & Secondary Action CTAs */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 pt-2">
            <button
              onClick={() => handleLaunchHero("hero_a", true)}
              disabled={loading}
              className="px-6 py-3.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm text-center transition-all shadow-sm hover:shadow-md flex items-center justify-center space-x-2"
            >
              <span>{loading && activeHero === "hero_a" ? "Loading Hero A..." : "Explore a live case"}</span>
              <span className="text-emerald-200">&rarr;</span>
            </button>

            <Link
              href="/exceptions"
              className="px-6 py-3.5 rounded-xl bg-stone-100 hover:bg-stone-200 text-stone-800 font-bold text-sm text-center transition border border-[#e2ddd5] flex items-center justify-center space-x-2"
            >
              <span>Investigate real exceptions</span>
              <span className="text-stone-400">&rarr;</span>
            </Link>
          </div>
        </div>

        {/* Active Hero Result Notification */}
        {heroResult && (
          <div className="mt-8 p-4 rounded-xl bg-[#f0fdf4] border border-[#86efac] flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs animate-in fade-in duration-300">
            <div>
              <span className="text-emerald-900 font-bold text-sm">
                Active Showcase: {heroResult.title}
              </span>
              <p className="text-stone-600 text-xs mt-0.5">{heroResult.description}</p>
            </div>
            {heroResult.cases.length > 0 && (
              <Link
                href={`/cases/${heroResult.cases[0].case_id}`}
                className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs uppercase tracking-wider text-center shrink-0 transition"
              >
                Inspect Case ({heroResult.cases[0].case_id.slice(0, 12)}...) &rarr;
              </Link>
            )}
          </div>
        )}
      </section>

      {/* 2. Three Story-Driven Hero Cards */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-extrabold text-stone-900 tracking-tight font-sans">
              Interactive Hero Investigations
            </h2>
            <p className="text-xs text-stone-500 mt-0.5">
              Select an economic scenario to watch ShadowLedger reconstruct the latent value flow.
            </p>
          </div>
          <span className="font-handwriting text-stone-400 text-base hidden sm:inline">
            Click to explore each story ✎
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* Hero A: Kirana */}
          <div
            onClick={() => handleLaunchHero("hero_a", true)}
            className={cn(
              "cursor-pointer p-6 rounded-2xl border transition-all text-left flex flex-col justify-between space-y-4 bg-white shadow-xs hover:shadow-md",
              activeHero === "hero_a"
                ? "border-emerald-500 ring-2 ring-emerald-400/40 bg-[#f0fdf4]"
                : "border-[#e7e2d9] hover:border-emerald-300"
            )}
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="badge-resolved text-[11px] font-bold px-2.5 py-1 rounded-full uppercase tracking-wider">
                  Hero A &bull; Kirana
                </span>
                <span className="text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                  Auto-Resolved
                </span>
              </div>

              <div>
                <h3 className="text-lg font-bold text-stone-900 font-sans">
                  THE MISSING ₹2
                </h3>
                <p className="text-xs text-stone-600 mt-1 leading-relaxed">
                  A ₹100 purchase settled as ₹98 cash + ₹2 physical inventory change.
                </p>
              </div>

              {/* Why this matters callout */}
              <div className="p-3 rounded-xl bg-[#faf8f5] border border-[#e7e2d9] text-xs text-stone-600 space-y-1">
                <span className="font-bold text-[10px] uppercase text-stone-400 block tracking-wider">
                  Why this matters
                </span>
                <p className="text-[11px] text-stone-700 italic">
                  &ldquo;Traditional reconciliation sees ₹2 missing. ShadowLedger investigates where that value may have gone.&rdquo;
                </p>
              </div>
            </div>

            <div className="pt-2 flex items-center justify-between border-t border-stone-100 text-xs font-bold text-emerald-700">
              <span>{loading && activeHero === "hero_a" ? "Reconstructing..." : "Explore Kirana Story"}</span>
              <span>&rarr;</span>
            </div>
          </div>

          {/* Hero B: Mobility Ride-Hailing */}
          <div
            onClick={() => handleLaunchHero("hero_b", true)}
            className={cn(
              "cursor-pointer p-6 rounded-2xl border transition-all text-left flex flex-col justify-between space-y-4 bg-white shadow-xs hover:shadow-md",
              activeHero === "hero_b"
                ? "border-amber-500 ring-2 ring-amber-400/40 bg-[#fefce8]"
                : "border-[#e7e2d9] hover:border-amber-300"
            )}
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="badge-review text-[11px] font-bold px-2.5 py-1 rounded-full uppercase tracking-wider">
                  Hero B &bull; Mobility
                </span>
                <span className="text-[11px] font-bold text-amber-800 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                  Off-Ledger Safety
                </span>
              </div>

              <div>
                <h3 className="text-lg font-bold text-stone-900 font-sans">
                  THE FARE THAT DOESN&apos;T ADD UP
                </h3>
                <p className="text-xs text-stone-600 mt-1 leading-relaxed">
                  See how ShadowLedger separates verifiable evidence from uncertainty in off-ledger payments.
                </p>
              </div>

              {/* Why this matters callout */}
              <div className="p-3 rounded-xl bg-[#faf8f5] border border-[#e7e2d9] text-xs text-stone-600 space-y-1">
                <span className="font-bold text-[10px] uppercase text-stone-400 block tracking-wider">
                  Why this matters
                </span>
                <p className="text-[11px] text-stone-700 italic">
                  &ldquo;Not every anomaly can be proven. ShadowLedger distinguishes evidence from uncertainty.&rdquo;
                </p>
              </div>
            </div>

            <div className="pt-2 flex items-center justify-between border-t border-stone-100 text-xs font-bold text-amber-700">
              <span>{loading && activeHero === "hero_b" ? "Reconstructing..." : "Explore Mobility Story"}</span>
              <span>&rarr;</span>
            </div>
          </div>

          {/* Hero C: Pattern Discovery */}
          <div
            onClick={() => handleLaunchHero("hero_c", false)}
            className={cn(
              "cursor-pointer p-6 rounded-2xl border transition-all text-left flex flex-col justify-between space-y-4 bg-white shadow-xs hover:shadow-md",
              activeHero === "hero_c"
                ? "border-purple-500 ring-2 ring-purple-400/40 bg-[#faf5ff]"
                : "border-[#e7e2d9] hover:border-purple-300"
            )}
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="badge-reconstructed text-[11px] font-bold px-2.5 py-1 rounded-full uppercase tracking-wider">
                  Hero C &bull; Fleet
                </span>
                <span className="text-[11px] font-bold text-purple-800 bg-purple-50 px-2 py-0.5 rounded border border-purple-200">
                  Pattern Collapse
                </span>
              </div>

              <div>
                <h3 className="text-lg font-bold text-stone-900 font-sans">
                  THE PATTERN HIDING IN EXCEPTIONS
                </h3>
                <p className="text-xs text-stone-600 mt-1 leading-relaxed">
                  60 discrepancy records collapse into 3 recurring systemic structural patterns.
                </p>
              </div>

              {/* Why this matters callout */}
              <div className="p-3 rounded-xl bg-[#faf8f5] border border-[#e7e2d9] text-xs text-stone-600 space-y-1">
                <span className="font-bold text-[10px] uppercase text-stone-400 block tracking-wider">
                  Why this matters
                </span>
                <p className="text-[11px] text-stone-700 italic">
                  &ldquo;Repeated exceptions can reveal operational patterns invisible in individual transactions.&rdquo;
                </p>
              </div>
            </div>

            <div className="pt-2 flex items-center justify-between border-t border-stone-100 text-xs font-bold text-purple-700">
              <span>{loading && activeHero === "hero_c" ? "Discovering..." : "Explore Pattern Story"}</span>
              <span>&rarr;</span>
            </div>
          </div>
        </div>
      </section>

      {/* 3. Simple Status Summary (Semantic Pastel Cards) */}
      <section className="space-y-3">
        <h2 className="text-sm font-bold uppercase tracking-wider text-stone-500 font-sans">
          Reconciliation Status Summary
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {/* Resolved */}
          <div className="p-5 rounded-2xl bg-[#f0fdf4] border border-[#86efac] flex items-center justify-between shadow-2xs">
            <div>
              <div className="text-xs font-bold uppercase tracking-wider text-[#14532d]">
                Auto-Resolved
              </div>
              <div className="text-2xl font-extrabold text-[#14532d] mt-1 font-sans">
                {metrics ? (metrics.auto_resolved_count || 0).toLocaleString() : "0"} cases
              </div>
              <div className="text-xs text-emerald-700/80 mt-0.5">
                Multi-dimensional proof closed
              </div>
            </div>
            <div className="w-10 h-10 rounded-xl bg-emerald-200/50 flex items-center justify-center text-emerald-800 text-lg font-bold">
              ✓
            </div>
          </div>

          {/* Human Review */}
          <div className="p-5 rounded-2xl bg-[#fefce8] border border-[#fde047] flex items-center justify-between shadow-2xs">
            <div>
              <div className="text-xs font-bold uppercase tracking-wider text-[#713f12]">
                Human Review
              </div>
              <div className="text-2xl font-extrabold text-[#713f12] mt-1 font-sans">
                {metrics ? (metrics.human_review_count || 0).toLocaleString() : "0"} cases
              </div>
              <div className="text-xs text-amber-800/80 mt-0.5">
                Evidence graph ranked for ops
              </div>
            </div>
            <div className="w-10 h-10 rounded-xl bg-amber-200/50 flex items-center justify-center text-amber-800 text-lg font-bold">
              !
            </div>
          </div>

          {/* Unresolved */}
          <div className="p-5 rounded-2xl bg-[#fff7ed] border border-[#fdba74] flex items-center justify-between shadow-2xs">
            <div>
              <div className="text-xs font-bold uppercase tracking-wider text-[#7c2d12]">
                Unresolved
              </div>
              <div className="text-2xl font-extrabold text-[#7c2d12] mt-1 font-sans">
                {metrics ? (metrics.unresolved_count || 0).toLocaleString() : "0"} cases
              </div>
              <div className="text-xs text-orange-800/80 mt-0.5">
                Refused false guesses (Safe)
              </div>
            </div>
            <div className="w-10 h-10 rounded-xl bg-orange-200/50 flex items-center justify-center text-orange-800 text-lg font-bold">
              ?
            </div>
          </div>
        </div>
      </section>

      {/* 4. Value Conservation Overview */}
      <section className="bg-white border border-[#e7e2d9] rounded-2xl p-6 sm:p-7 space-y-6 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-[#e7e2d9] pb-4 gap-2">
          <div>
            <h2 className="text-base font-bold text-stone-900 font-sans">
              Financial Value Conservation Overview
            </h2>
            <p className="text-xs text-stone-500 mt-0.5">
              Gross Ingested Volume vs Reconstructed Economic Value vs Residual Shortfall
            </p>
          </div>
          {metrics && (
            <span className="text-xs text-stone-500 bg-stone-100 px-2.5 py-1 rounded-md font-mono self-start sm:self-auto">
              Batch: {metrics.batch_id}
            </span>
          )}
        </div>

        <div className="space-y-5">
          {/* Total Ingested */}
          <div>
            <div className="flex justify-between text-xs mb-1.5 font-semibold text-stone-700">
              <span>Total Ingested Gross Volume</span>
              <span className="font-mono text-stone-900 font-bold">
                {metrics ? formatINR(metrics.total_volume_inr) : "₹0.00"}
              </span>
            </div>
            <div className="w-full h-3 bg-stone-100 rounded-full overflow-hidden border border-stone-200">
              <div className="h-full bg-stone-400" style={{ width: "100%" }}></div>
            </div>
          </div>

          {/* Explained Volume */}
          <div>
            <div className="flex justify-between text-xs mb-1.5 font-semibold text-emerald-800">
              <span className="flex items-center space-x-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                <span>Explained Value (Proven Matches + Latent Inferences)</span>
              </span>
              <span className="font-mono font-bold">
                {metrics ? formatINR(metrics.explained_volume_inr) : "₹0.00"}
              </span>
            </div>
            <div className="w-full h-3 bg-stone-100 rounded-full overflow-hidden border border-stone-200">
              <div
                className="h-full bg-emerald-500 transition-all duration-500 rounded-full"
                style={{
                  width:
                    metrics && metrics.total_volume_inr > 0
                      ? `${Math.min(
                          100,
                          (metrics.explained_volume_inr / metrics.total_volume_inr) * 100
                        )}%`
                      : "0%",
                }}
              ></div>
            </div>
          </div>

          {/* Unexplained Volume */}
          <div>
            <div className="flex justify-between text-xs mb-1.5 font-semibold text-orange-800">
              <span className="flex items-center space-x-1.5">
                <span className="w-2 h-2 rounded-full bg-orange-500"></span>
                <span>Unexplained Value at Risk (Unresolved Exceptions)</span>
              </span>
              <span className="font-mono font-bold">
                {metrics ? formatINR(metrics.unexplained_volume_inr) : "₹0.00"}
              </span>
            </div>
            <div className="w-full h-3 bg-stone-100 rounded-full overflow-hidden border border-stone-200">
              <div
                className="h-full bg-orange-400 transition-all duration-500 rounded-full"
                style={{
                  width:
                    metrics && metrics.total_volume_inr > 0
                      ? `${Math.min(
                          100,
                          (metrics.unexplained_volume_inr / metrics.total_volume_inr) * 100
                        )}%`
                      : "0%",
                }}
              ></div>
            </div>
          </div>
        </div>
      </section>

      {/* 5. Cross-Case Patterns Preview */}
      <section className="bg-white border border-[#e7e2d9] rounded-2xl p-6 sm:p-7 space-y-4 shadow-xs">
        <div className="flex items-center justify-between border-b border-[#e7e2d9] pb-4">
          <div>
            <h2 className="text-base font-bold text-stone-900 font-sans flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-purple-500"></span>
              <span>Cross-Case Pattern Discovery (P0)</span>
            </h2>
            <p className="text-xs text-stone-500 mt-0.5">
              Aggregated structural anomaly clusters: &ldquo;N exceptions &rarr; 1 likely common operational cause&rdquo;
            </p>
          </div>
          <Link
            href="/patterns"
            className="text-xs font-bold text-purple-700 hover:text-purple-900 flex items-center space-x-1"
          >
            <span>View All ({patterns.length})</span>
            <span>&rarr;</span>
          </Link>
        </div>

        {patterns.length === 0 ? (
          <div className="py-8 text-center text-xs text-stone-500">
            Launch Hero C or process a custom batch to discover recurring structural patterns.
          </div>
        ) : (
          <div className="divide-y divide-stone-100">
            {patterns.slice(0, 3).map((p) => (
              <div
                key={p.cluster_id}
                className="py-3.5 flex flex-col md:flex-row md:items-center justify-between gap-3"
              >
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-xs text-stone-900 font-mono">
                      {p.pattern_signature}
                    </span>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-purple-100 text-purple-800">
                      {p.exception_count} Cases Linked
                    </span>
                  </div>
                  <p className="text-xs text-stone-600">{p.likely_common_cause}</p>
                </div>

                <div className="text-left md:text-right shrink-0">
                  <div className="text-[10px] text-stone-500">Total Value at Risk</div>
                  <div className="text-sm font-bold text-amber-700 font-mono">
                    {formatINR(p.total_value_at_risk)}
                  </div>
                  <div className="text-[10px] text-emerald-700 font-semibold">
                    Evidence: {(p.evidence_strength * 100).toFixed(0)}%
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* 6. Technical Batch Processor (Available / Highlighted in Investigate Mode) */}
      <section
        className={cn(
          "rounded-2xl p-6 transition-all",
          isExplain
            ? "bg-[#faf8f5] border border-[#e7e2d9]"
            : "bg-white border-2 border-stone-900 shadow-sm"
        )}
      >
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-bold text-stone-900 uppercase tracking-wider font-mono">
                Custom Synthetic Batch Harness
              </span>
              {!isExplain && (
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-stone-900 text-white">
                  Investigate Mode Active
                </span>
              )}
            </div>
            <p className="text-xs text-stone-500 mt-0.5">
              Execute deterministic synthetic batch reconciliation with custom row counts and seeds.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3 text-xs">
            <div className="flex items-center space-x-2 text-stone-600">
              <span className="font-semibold">Size:</span>
              <select
                value={batchSize}
                onChange={(e) => setBatchSize(Number(e.target.value))}
                className="bg-white border border-[#e2ddd5] text-stone-800 rounded-lg px-2.5 py-1.5 text-xs font-mono focus:outline-none focus:ring-1 focus:ring-emerald-500"
              >
                <option value={100}>100 Rows</option>
                <option value={1000}>1,000 Rows</option>
                <option value={10000}>10,000 Rows</option>
              </select>
            </div>

            <div className="flex items-center space-x-2 text-stone-600">
              <span className="font-semibold">Seed:</span>
              <input
                type="number"
                value={seed}
                onChange={(e) => setSeed(Number(e.target.value))}
                className="w-16 bg-white border border-[#e2ddd5] text-stone-800 rounded-lg px-2 py-1.5 text-xs font-mono text-center focus:outline-none focus:ring-1 focus:ring-emerald-500"
              />
            </div>

            <button
              onClick={handleRunBatch}
              disabled={loading}
              className={cn(
                "px-4 py-1.5 rounded-lg font-bold text-xs uppercase tracking-wider transition shadow-xs",
                loading
                  ? "bg-stone-200 text-stone-400 cursor-not-allowed"
                  : "bg-stone-900 hover:bg-stone-800 text-white"
              )}
            >
              {loading && !activeHero ? "Reconstructing..." : "Process Batch"}
            </button>
          </div>
        </div>

        {/* Technical Throughput Stats */}
        {metrics && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4 pt-4 border-t border-[#e7e2d9] text-xs">
            <div>
              <span className="text-[10px] text-stone-500 uppercase font-mono">Ingested</span>
              <div className="font-mono font-bold text-stone-800">
                {metrics.record_count.toLocaleString()}
              </div>
            </div>
            <div>
              <span className="text-[10px] text-stone-500 uppercase font-mono">Exact Match</span>
              <div className="font-mono font-bold text-blue-700">
                {metrics.match_rate.toFixed(1)}%
              </div>
            </div>
            <div>
              <span className="text-[10px] text-stone-500 uppercase font-mono">Throughput</span>
              <div className="font-mono font-bold text-emerald-700">
                {metrics.throughput_records_per_sec.toLocaleString()} r/s
              </div>
            </div>
            <div>
              <span className="text-[10px] text-stone-500 uppercase font-mono">Latency</span>
              <div className="font-mono font-bold text-stone-800">
                {metrics.processing_time_ms.toFixed(1)} ms
              </div>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
