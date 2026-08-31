"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { formatINR, cn } from "../lib/utils";
import { fetchLatestMetrics, processBatch, BatchSummary } from "../lib/api";

export default function CommandCenterPage() {
  const [metrics, setMetrics] = useState<BatchSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [batchSize, setBatchSize] = useState<number>(100);
  const [seed, setSeed] = useState<number>(42);

  useEffect(() => {
    loadMetrics();
  }, []);

  async function loadMetrics() {
    const data = await fetchLatestMetrics();
    if (data && data.batch_id) {
      setMetrics(data);
    }
  }

  async function handleRunBatch() {
    setLoading(true);
    try {
      const summary = await processBatch(batchSize, seed);
      if (summary) {
        setMetrics(summary);
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8">
      {/* Top Header & Batch Action Trigger */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Finance Operations Command Center</h1>
          <p className="text-sm text-slate-400 mt-1">
            Deterministic Reconciliation Baseline &bull; Pure Rules &bull; Zero LLM Hallucinations
          </p>
        </div>

        <div className="flex items-center space-x-3 bg-slate-900/90 border border-slate-800 p-2 rounded-xl">
          <div className="flex items-center space-x-2 text-xs text-slate-400 font-mono">
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

          <div className="flex items-center space-x-2 text-xs text-slate-400 font-mono">
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
              "px-4 py-2 rounded-lg font-medium text-xs tracking-wider uppercase transition flex items-center space-x-2 shadow-lg",
              loading
                ? "bg-slate-800 text-slate-500 cursor-not-allowed"
                : "bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold shadow-emerald-500/20"
            )}
          >
            {loading ? (
              <>
                <span className="w-3 h-3 border-2 border-slate-950 border-t-transparent rounded-full animate-spin"></span>
                <span>Reconciling...</span>
              </>
            ) : (
              <span>Process Batch</span>
            )}
          </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Ingested */}
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-5 relative overflow-hidden">
          <div className="text-xs font-mono uppercase text-slate-400 tracking-wider">Total Ingested</div>
          <div className="text-3xl font-bold text-white mt-2 font-mono">
            {metrics ? metrics.record_count.toLocaleString() : "0"}
          </div>
          <div className="text-xs text-slate-500 mt-1 font-mono">Multi-source records</div>
          <div className="absolute right-3 top-3 w-10 h-10 bg-slate-800/40 rounded-lg flex items-center justify-center text-slate-500 font-mono text-sm">
            #
          </div>
        </div>

        {/* Baseline Match Rate */}
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-5 relative overflow-hidden">
          <div className="text-xs font-mono uppercase text-slate-400 tracking-wider">Deterministic Match Rate</div>
          <div className="text-3xl font-bold text-emerald-400 mt-2 font-mono">
            {metrics ? `${metrics.match_rate.toFixed(1)}%` : "0.0%"}
          </div>
          <div className="text-xs text-slate-500 mt-1 font-mono">
            {metrics ? `${metrics.matched_count.toLocaleString()} matched exactly` : "Awaiting batch"}
          </div>
          <div className="absolute right-3 top-3 w-10 h-10 bg-emerald-500/10 border border-emerald-500/20 rounded-lg flex items-center justify-center text-emerald-400 font-mono text-sm">
            ✓
          </div>
        </div>

        {/* Unmatched Exceptions */}
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-5 relative overflow-hidden">
          <div className="text-xs font-mono uppercase text-slate-400 tracking-wider">Unmatched Exceptions</div>
          <div className="text-3xl font-bold text-amber-400 mt-2 font-mono">
            {metrics ? metrics.exception_count.toLocaleString() : "0"}
          </div>
          <div className="text-xs text-slate-500 mt-1 font-mono">
            Candidate latent event cases
          </div>
          <div className="absolute right-3 top-3 w-10 h-10 bg-amber-500/10 border border-amber-500/20 rounded-lg flex items-center justify-center text-amber-400 font-mono text-sm">
            !
          </div>
        </div>

        {/* Engine Throughput */}
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-5 relative overflow-hidden">
          <div className="text-xs font-mono uppercase text-slate-400 tracking-wider">Processing Throughput</div>
          <div className="text-3xl font-bold text-blue-400 mt-2 font-mono">
            {metrics ? `${metrics.throughput_records_per_sec.toLocaleString()}` : "0"}
          </div>
          <div className="text-xs text-slate-500 mt-1 font-mono">records / second</div>
          <div className="absolute right-3 top-3 w-10 h-10 bg-blue-500/10 border border-blue-500/20 rounded-lg flex items-center justify-center text-blue-400 font-mono text-sm">
            ⚡
          </div>
        </div>
      </div>

      {/* Financial Value Flow Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-slate-900/60 border border-slate-800/80 rounded-xl p-6">
          <div className="flex items-center justify-between border-b border-slate-800/60 pb-4">
            <div>
              <h2 className="text-base font-semibold text-white">Value Conservation Overview</h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Official Volume vs Explained Economic Value vs Unresolved Residuals
              </p>
            </div>
            {metrics && (
              <span className="text-xs font-mono text-slate-500 bg-slate-800 px-2 py-1 rounded">
                Batch: {metrics.batch_id}
              </span>
            )}
          </div>

          <div className="mt-6 space-y-6">
            {/* Total Volume */}
            <div>
              <div className="flex justify-between text-xs font-mono mb-2">
                <span className="text-slate-400">Total Ingested Volume</span>
                <span className="text-white font-bold">{metrics ? formatINR(metrics.total_volume_inr) : "₹0.00"}</span>
              </div>
              <div className="w-full h-3 bg-slate-800 rounded-full overflow-hidden">
                <div className="h-full bg-slate-400" style={{ width: "100%" }}></div>
              </div>
            </div>

            {/* Explained Volume */}
            <div>
              <div className="flex justify-between text-xs font-mono mb-2">
                <span className="text-emerald-400 flex items-center space-x-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                  <span>Explained Volume (Proven Matches)</span>
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
                      ? `${(metrics.explained_volume_inr / metrics.total_volume_inr) * 100}%`
                      : "0%",
                  }}
                ></div>
              </div>
            </div>

            {/* Unexplained Residual */}
            <div>
              <div className="flex justify-between text-xs font-mono mb-2">
                <span className="text-amber-400 flex items-center space-x-1.5">
                  <span className="w-2 h-2 rounded-full bg-amber-400"></span>
                  <span>Unexplained Value at Risk (Exceptions)</span>
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
                      ? `${(metrics.unexplained_volume_inr / metrics.total_volume_inr) * 100}%`
                      : "0%",
                  }}
                ></div>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Scenario & Exception Actions */}
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-6 flex flex-col justify-between">
          <div>
            <h2 className="text-base font-semibold text-white">Deterministic Baseline Status</h2>
            <p className="text-xs text-slate-400 mt-1">
              Deterministic rules strictly match provable transactions. Unmatched exceptions are passed to the downstream value-flow engine.
            </p>

            <div className="mt-6 space-y-3 font-mono text-xs">
              <div className="flex items-center justify-between p-3 rounded bg-slate-800/40 border border-slate-800">
                <span className="text-slate-400">Engine Core:</span>
                <span className="text-emerald-400">Deterministic Pure Rules</span>
              </div>
              <div className="flex items-center justify-between p-3 rounded bg-slate-800/40 border border-slate-800">
                <span className="text-slate-400">LLM Truth Path:</span>
                <span className="text-slate-300">Disconnected (Zero LLM)</span>
              </div>
              <div className="flex items-center justify-between p-3 rounded bg-slate-800/40 border border-slate-800">
                <span className="text-slate-400">Unsafe Auto-Resolutions:</span>
                <span className="text-emerald-400 font-bold">0 (100% Precision)</span>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-slate-800">
            <Link
              href="/exceptions"
              className="w-full py-2.5 bg-slate-800 hover:bg-slate-700 text-white rounded-lg font-medium text-xs text-center block transition border border-slate-700"
            >
              Investigate Exception Queue &rarr;
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
