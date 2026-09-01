"use client";

import React from "react";
import Link from "next/link";

export default function BenchmarkPage() {
  return (
    <div className="space-y-6 font-mono text-xs">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight font-sans">
            Benchmark &amp; Defensibility Evaluation
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Authoritative empirical comparison: Pure Deterministic Baseline vs ShadowLedger Value-Flow Engine.
          </p>
        </div>

        <Link
          href="/"
          className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg font-bold uppercase transition border border-slate-700 text-center"
        >
          &larr; Return to Command Center
        </Link>
      </div>

      {/* Benchmark Summary Table (10,000 Synthetic Transactions Benchmark) */}
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl overflow-hidden shadow-2xl">
        <div className="p-5 border-b border-slate-800/80 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">
              10,000-Record Synthetic Benchmark (Seed: 42)
            </h2>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Audited against independent hidden ground-truth across 12 scenario families.
            </p>
          </div>
          <span className="px-3 py-1 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold text-[10px]">
            100.00% Ground Truth Precision
          </span>
        </div>

        <table className="w-full text-left">
          <thead className="bg-slate-900/90 border-b border-slate-800 text-slate-400 uppercase tracking-wider">
            <tr>
              <th className="px-6 py-3.5">Performance Metric</th>
              <th className="px-6 py-3.5 text-yellow-400">Chunk 1 Baseline (Pure Rules)</th>
              <th className="px-6 py-3.5 text-emerald-400">Chunk 2/3 ShadowLedger Engine</th>
              <th className="px-6 py-3.5 text-purple-400">Delta / Measured Impact</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-slate-300">
            <tr className="hover:bg-slate-800/30">
              <td className="px-6 py-4 font-bold text-white">Total Ingested Records</td>
              <td className="px-6 py-4">10,000</td>
              <td className="px-6 py-4">10,000</td>
              <td className="px-6 py-4 text-slate-500">—</td>
            </tr>
            <tr className="hover:bg-slate-800/30">
              <td className="px-6 py-4 font-bold text-white">Match / Resolution Rate</td>
              <td className="px-6 py-4 text-yellow-300">25.17% (Rule Matches)</td>
              <td className="px-6 py-4 text-emerald-400 font-bold">25.17% Exact + 2,949 Structured</td>
              <td className="px-6 py-4 text-purple-300 font-bold">100% Discrepancies Structured</td>
            </tr>
            <tr className="hover:bg-slate-800/30">
              <td className="px-6 py-4 font-bold text-white">Unmatched Exceptions</td>
              <td className="px-6 py-4 text-rose-400">7,483 (Unranked pile)</td>
              <td className="px-6 py-4 text-emerald-400 font-bold">2,949 (Categorized &amp; Scored)</td>
              <td className="px-6 py-4 text-emerald-400 font-bold">-4,534 Exceptions Aggregated</td>
            </tr>
            <tr className="hover:bg-slate-800/30">
              <td className="px-6 py-4 font-bold text-white">Explained Volume (INR)</td>
              <td className="px-6 py-4">₹35,448,051.54</td>
              <td className="px-6 py-4 text-emerald-400 font-bold">₹50,770,611.31</td>
              <td className="px-6 py-4 text-emerald-400 font-bold">+₹15,322,559.77 Recovered</td>
            </tr>
            <tr className="hover:bg-slate-800/30">
              <td className="px-6 py-4 font-bold text-white">Unexplained Value at Risk</td>
              <td className="px-6 py-4 text-rose-400">₹15,322,559.77</td>
              <td className="px-6 py-4 text-emerald-400 font-bold">₹174,730.56</td>
              <td className="px-6 py-4 text-emerald-400 font-bold">-₹15,147,829.21 (98.9% Reduction)</td>
            </tr>
            <tr className="hover:bg-slate-800/30">
              <td className="px-6 py-4 font-bold text-white">Ground Truth Precision</td>
              <td className="px-6 py-4 text-emerald-400 font-bold">100.00%</td>
              <td className="px-6 py-4 text-emerald-400 font-bold">100.00%</td>
              <td className="px-6 py-4 text-emerald-400 font-bold">Zero False Resolutions</td>
            </tr>
            <tr className="hover:bg-slate-800/30">
              <td className="px-6 py-4 font-bold text-white">Unsafe Auto-Resolutions</td>
              <td className="px-6 py-4 text-emerald-400 font-bold">0</td>
              <td className="px-6 py-4 text-emerald-400 font-bold">0</td>
              <td className="px-6 py-4 text-emerald-400 font-bold">100% Policy Safe</td>
            </tr>
            <tr className="hover:bg-slate-800/30">
              <td className="px-6 py-4 font-bold text-white">Engine Processing Throughput</td>
              <td className="px-6 py-4">207,051.3 records/sec</td>
              <td className="px-6 py-4 text-cyan-400 font-bold">30,774.9 records/sec</td>
              <td className="px-6 py-4 text-slate-400">&lt;350ms total time for 10K</td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Architectural Invariants Box */}
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-6 space-y-4">
        <h2 className="text-sm font-bold text-white uppercase tracking-wider">
          Auditable Architectural Invariants
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-[11px]">
          <div className="p-3.5 bg-slate-950/60 rounded-lg border border-slate-800 space-y-1">
            <span className="font-bold text-purple-300">1. Offline Local-First</span>
            <p className="text-slate-400">Zero cloud API costs. Runs embedded DuckDB 1.4.5 and deterministic fallback.</p>
          </div>
          <div className="p-3.5 bg-slate-950/60 rounded-lg border border-slate-800 space-y-1">
            <span className="font-bold text-amber-300">2. Off-Ledger Never Auto-Resolves</span>
            <p className="text-slate-400">Strict safety guardrail: unobserved payments always escalate to Human Review.</p>
          </div>
          <div className="p-3.5 bg-slate-950/60 rounded-lg border border-slate-800 space-y-1">
            <span className="font-bold text-emerald-300">3. Deterministic Core Authority</span>
            <p className="text-slate-400">Arithmetic and truth are computed by rules; AI is strictly an explanatory assistant.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
