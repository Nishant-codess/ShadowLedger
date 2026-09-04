"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { formatINR } from "../../lib/utils";
import { useViewMode } from "../../lib/ViewModeContext";
import { fetchCases, CaseDetail } from "../../lib/api";

const SCENARIO_LABELS: Record<string, string> = {
  SCN_01: "Exact Reconciliation",
  SCN_02: "Partial Refund",
  SCN_03: "MDR Fee Deduction (2.0%)",
  SCN_04: "Kirana Inventory Settlement",
  SCN_05: "Store Credit Carry-Forward",
  SCN_06: "Settlement Timing Offset (T+1)",
  SCN_07: "Duplicate Webhook Broadcast",
  SCN_08: "Mobility QR Digital Trace",
  SCN_09: "Mobility Cash-Only Deviation",
  SCN_10: "Recurring Entity Deviation",
  SCN_11: "Batch Surcharge Adjustment",
  SCN_12: "Adversarial Near-Match Safety",
};

export default function ExceptionsPage() {
  const { isExplain } = useViewMode();
  const [cases, setCases] = useState<CaseDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");

  useEffect(() => {
    loadCases();
  }, []);

  async function loadCases() {
    setLoading(true);
    try {
      const data = await fetchCases();
      setCases(data);
    } finally {
      setLoading(false);
    }
  }

  const filteredCases = useMemo(() => {
    return cases.filter((c) => {
      const dec = c.decision?.decision || "unresolved";
      if (filterStatus === "human_review" && dec !== "human_review") return false;
      if (filterStatus === "unresolved" && dec !== "unresolved") return false;
      if (filterStatus === "auto_resolve" && dec !== "auto_resolve") return false;

      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        const matchesId = c.case_id.toLowerCase().includes(q);
        const matchesScn = (c.scenario_id || "").toLowerCase().includes(q);
        const matchesObs = c.observation_ids.some((oid) => oid.toLowerCase().includes(q));
        if (!matchesId && !matchesScn && !matchesObs) return false;
      }
      return true;
    });
  }, [cases, filterStatus, searchQuery]);

  return (
    <div className="space-y-6">
      {/* Header and Summary */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#e7e2d9] pb-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-stone-900 tracking-tight font-sans">
            Financial Exception Workbench
          </h1>
          <p className="text-xs sm:text-sm text-stone-500 mt-1">
            Cases requiring latent economic event reconstruction, evidence scoring, and decision gating.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-stone-700 bg-white border border-[#e7e2d9] px-3.5 py-1.5 rounded-xl font-bold text-xs shadow-2xs font-sans">
            {filteredCases.length} of {cases.length} Cases
          </span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-white border border-[#e7e2d9] p-3 rounded-2xl shadow-xs">
        {/* Status Filter Buttons */}
        <div className="flex flex-wrap items-center gap-1.5">
          <button
            onClick={() => setFilterStatus("all")}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition ${
              filterStatus === "all"
                ? "bg-stone-900 text-white"
                : "text-stone-600 hover:bg-stone-100"
            }`}
          >
            All Cases ({cases.length})
          </button>
          <button
            onClick={() => setFilterStatus("human_review")}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition ${
              filterStatus === "human_review"
                ? "bg-[#fefce8] text-[#713f12] border border-[#fde047]"
                : "text-stone-600 hover:bg-stone-100"
            }`}
          >
            Human Review ({cases.filter((c) => c.decision?.decision === "human_review").length})
          </button>
          <button
            onClick={() => setFilterStatus("unresolved")}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition ${
              filterStatus === "unresolved"
                ? "bg-[#fff7ed] text-[#7c2d12] border border-[#fdba74]"
                : "text-stone-600 hover:bg-stone-100"
            }`}
          >
            Unresolved ({cases.filter((c) => (c.decision?.decision || "unresolved") === "unresolved").length})
          </button>
          <button
            onClick={() => setFilterStatus("auto_resolve")}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition ${
              filterStatus === "auto_resolve"
                ? "bg-[#f0fdf4] text-[#14532d] border border-[#86efac]"
                : "text-stone-600 hover:bg-stone-100"
            }`}
          >
            Auto-Resolved ({cases.filter((c) => c.decision?.decision === "auto_resolve").length})
          </button>
        </div>

        {/* Search Input */}
        <div className="w-full sm:w-64">
          <input
            type="text"
            placeholder="Search case, scenario, or ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-[#faf8f5] border border-[#e2ddd5] rounded-xl px-3.5 py-1.5 text-xs text-stone-900 placeholder-stone-400 focus:outline-none focus:ring-1 focus:ring-emerald-500 font-sans"
          />
        </div>
      </div>

      {loading ? (
        <div className="py-20 text-center text-stone-500 text-sm">
          Loading exception cases...
        </div>
      ) : filteredCases.length === 0 ? (
        <div className="bg-white border border-[#e7e2d9] rounded-2xl p-12 text-center space-y-3 shadow-xs">
          <div className="text-stone-800 font-bold text-base">No matching cases found</div>
          <p className="text-stone-500 text-xs max-w-sm mx-auto">
            Launch a Hero Showcase from the Command Center to populate cases.
          </p>
          <Link
            href="/"
            className="inline-block px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl text-xs uppercase tracking-wider transition shadow-sm"
          >
            Go to Command Center
          </Link>
        </div>
      ) : (
        <div className="bg-white border border-[#e7e2d9] rounded-2xl overflow-hidden shadow-xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#faf8f5] border-b border-[#e7e2d9] text-stone-500 uppercase tracking-wider font-semibold font-sans">
                <tr>
                  <th className="px-6 py-4">Case Identifier</th>
                  <th className="px-6 py-4">Scenario Context</th>
                  <th className="px-6 py-4">Evidence Strength</th>
                  <th className="px-6 py-4">Residual at Risk</th>
                  <th className="px-6 py-4">Decision Outcome</th>
                  <th className="px-6 py-4 text-right">Investigation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#e7e2d9] text-stone-700">
                {filteredCases.map((c) => {
                  const dec = c.decision?.decision || "unresolved";
                  const conf = c.decision?.evidence_confidence || 0;
                  const isAuto = dec === "auto_resolve";
                  const isHuman = dec === "human_review";
                  const scnLabel = SCENARIO_LABELS[c.scenario_id || ""] || c.scenario_id || "Standard Exception";

                  return (
                    <tr key={c.case_id} className="hover:bg-[#faf8f5] transition">
                      <td className="px-6 py-4 font-bold text-stone-900 font-mono">
                        <div className="flex items-center space-x-2">
                          <span>{isExplain ? c.case_id.slice(0, 14) + "..." : c.case_id}</span>
                          {c.pattern_cluster_id && (
                            <span className="w-2 h-2 rounded-full bg-purple-500" title="Part of recurring fleet pattern"></span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-stone-700 font-sans">
                        <span className="px-2.5 py-1 rounded-md bg-[#faf8f5] border border-[#e2ddd5] font-semibold text-xs text-stone-800 inline-block">
                          {scnLabel}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center space-x-2">
                          <span className="font-bold text-emerald-700 font-mono">{(conf * 100).toFixed(0)}%</span>
                          <div className="w-16 h-1.5 bg-stone-100 rounded-full overflow-hidden border border-stone-200">
                            <div
                              className="h-full bg-emerald-500"
                              style={{ width: `${Math.round(conf * 100)}%` }}
                            ></div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 font-bold text-amber-800 font-mono text-sm">
                        {formatINR(c.residual_amount)}
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`px-2.5 py-1 rounded-full uppercase font-bold text-[10px] tracking-wider ${
                            isAuto
                              ? "badge-resolved"
                              : isHuman
                              ? "badge-review"
                              : "badge-unresolved"
                          }`}
                        >
                          {dec.replace("_", " ")}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <Link
                          href={`/cases/${c.case_id}`}
                          className="px-3.5 py-1.5 rounded-xl bg-white hover:bg-stone-100 text-stone-900 font-bold transition border border-[#e2ddd5] shadow-2xs inline-block"
                        >
                          Inspect &rarr;
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
