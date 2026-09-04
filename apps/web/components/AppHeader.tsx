"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useViewMode } from "../lib/ViewModeContext";

export function AppHeader() {
  const pathname = usePathname();
  const { isExplain, setViewMode } = useViewMode();

  return (
    <header className="border-b border-[#e7e2d9] bg-[#ffffff]/90 backdrop-blur sticky top-0 z-50 px-6 py-3.5 flex flex-col md:flex-row md:items-center justify-between gap-3 shadow-xs">
      <div className="flex items-center justify-between md:justify-start md:space-x-8">
        {/* Brand & Logo */}
        <Link href="/" className="flex items-center space-x-2.5 group">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 flex items-center justify-center font-bold text-white text-base shadow-sm group-hover:scale-105 transition-transform">
            S
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-extrabold text-base tracking-tight text-stone-900 font-sans">
                ShadowLedger
              </span>
              <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                Track 04
              </span>
            </div>
            <p className="text-[10px] text-stone-500 hidden sm:block">
              &ldquo;Show me what the ledger cannot explain.&rdquo;
            </p>
          </div>
        </Link>

        {/* Navigation Links */}
        <nav className="hidden lg:flex items-center space-x-1 text-xs font-semibold text-stone-600 font-sans">
          <Link
            href="/"
            className={`px-3 py-1.5 rounded-lg transition ${
              pathname === "/"
                ? "text-stone-900 bg-[#f5f0e6] font-bold"
                : "hover:text-stone-900 hover:bg-stone-100"
            }`}
          >
            Command Center
          </Link>
          <Link
            href="/exceptions"
            className={`px-3 py-1.5 rounded-lg transition ${
              pathname.startsWith("/exceptions")
                ? "text-stone-900 bg-[#f5f0e6] font-bold"
                : "hover:text-stone-900 hover:bg-stone-100"
            }`}
          >
            Exception Workbench
          </Link>
          <Link
            href="/patterns"
            className={`px-3 py-1.5 rounded-lg transition flex items-center space-x-1.5 ${
              pathname.startsWith("/patterns")
                ? "text-stone-900 bg-[#f5f0e6] font-bold"
                : "hover:text-stone-900 hover:bg-stone-100"
            }`}
          >
            <span className="w-2 h-2 rounded-full bg-purple-500"></span>
            <span>Fleet Patterns (P0)</span>
          </Link>
          <Link
            href="/benchmark"
            className={`px-3 py-1.5 rounded-lg transition ${
              pathname.startsWith("/benchmark")
                ? "text-stone-900 bg-[#f5f0e6] font-bold"
                : "hover:text-stone-900 hover:bg-stone-100"
            }`}
          >
            Defensibility Benchmark
          </Link>
        </nav>
      </div>

      {/* Right Controls: Prominent Dual Mode Toggle & Engine Pill */}
      <div className="flex items-center justify-between md:justify-end space-x-3">
        {/* Prominent Lens Toggle */}
        <div className="flex items-center bg-[#f5f0e6] p-1 rounded-xl border border-[#e2ddd5] shadow-inner">
          <button
            onClick={() => setViewMode("explain")}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              isExplain
                ? "bg-white text-stone-900 shadow-sm border border-[#e2ddd5]"
                : "text-stone-500 hover:text-stone-800"
            }`}
            title="Explain Mode: Conversational plain English, visual storytelling, hide internal IDs"
          >
            <span>✨</span>
            <span>EXPLAIN</span>
            <span className="text-[10px] font-normal text-stone-400 hidden sm:inline">
              (Story)
            </span>
          </button>

          <button
            onClick={() => setViewMode("investigate")}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              !isExplain
                ? "bg-[#1c1917] text-white shadow-sm border border-[#1c1917]"
                : "text-stone-500 hover:text-stone-800"
            }`}
            title="Investigate Mode: 4-level taxonomy, 7-dimension scoring, provenance IDs & audit trail"
          >
            <span>🔍</span>
            <span>INVESTIGATE</span>
            <span className="text-[10px] font-normal text-stone-400 hidden sm:inline">
              (Auditor)
            </span>
          </button>
        </div>

        {/* Engine Status Pill */}
        <div className="hidden sm:flex items-center space-x-2 bg-white border border-[#e7e2d9] px-2.5 py-1.5 rounded-full text-[11px] font-mono text-stone-600 shadow-2xs">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>FastAPI</span>
          <span className="text-stone-300">|</span>
          <span>DuckDB</span>
        </div>
      </div>
    </header>
  );
}
