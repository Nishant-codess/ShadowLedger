"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { formatINR } from "../../lib/utils";
import { fetchCases, CaseDetail } from "../../lib/api";

export default function ExceptionsPage() {
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
    <div className="space-y-6 font-mono text-xs">
      {/* Header and Filter Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight font-sans">
            Financial Exception Investigation Queue
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Cases requiring latent economic event reconstruction and evidence examination.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-slate-400 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg font-bold">
            {filteredCases.length} / {cases.length} Cases
          </span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-slate-900/60 border border-slate-800/80 p-3 rounded-xl">
        {/* Status Filter Buttons */}
        <div className="flex flex-wrap items-center gap-1.5">
          <button
            onClick={() => setFilterStatus("all")}
            className={`px-3 py-1.5 rounded-lg font-bold uppercase transition ${
              filterStatus === "all"
                ? "bg-slate-800 text-white border border-slate-700"
                : "text-slate-400 hover:text-white"
            }`}
          >
            All Cases ({cases.length})
          </button>
          <button
            onClick={() => setFilterStatus("human_review")}
            className={`px-3 py-1.5 rounded-lg font-bold uppercase transition ${
              filterStatus === "human_review"
                ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                : "text-slate-400 hover:text-amber-300"
            }`}
          >
            Human Review ({cases.filter((c) => c.decision?.decision === "human_review").length})
          </button>
          <button
            onClick={() => setFilterStatus("unresolved")}
            className={`px-3 py-1.5 rounded-lg font-bold uppercase transition ${
              filterStatus === "unresolved"
                ? "bg-rose-500/20 text-rose-300 border border-rose-500/40"
                : "text-slate-400 hover:text-rose-300"
            }`}
          >
            Unresolved ({cases.filter((c) => (c.decision?.decision || "unresolved") === "unresolved").length})
          </button>
          <button
            onClick={() => setFilterStatus("auto_resolve")}
            className={`px-3 py-1.5 rounded-lg font-bold uppercase transition ${
              filterStatus === "auto_resolve"
                ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                : "text-slate-400 hover:text-emerald-300"
            }`}
          >
            Auto-Resolved ({cases.filter((c) => c.decision?.decision === "auto_resolve").length})
          </button>
        </div>

        {/* Search Input */}
        <div className="w-full sm:w-64">
          <input
            type="text"
            placeholder="Search Case / Scenario / ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
          />
        </div>
      </div>

      {loading ? (
        <div className="py-20 text-center text-slate-500">
          Loading exception cases...
        </div>
      ) : filteredCases.length === 0 ? (
        <div className="bg-slate-900/40 border border-slate-800/80 rounded-xl p-12 text-center space-y-3">
          <div className="text-slate-300 font-bold">No matching cases found</div>
          <p className="text-slate-500 max-w-sm mx-auto">
            Launch a Hero Showcase or process a batch from the Command Center to populate cases.
          </p>
          <Link
            href="/"
            className="inline-block px-4 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold rounded-lg uppercase tracking-wider transition"
          >
            Go to Command Center
          </Link>
        </div>
      ) : (
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl overflow-hidden shadow-xl">
          <table className="w-full text-left">
            <thead className="bg-slate-900/90 border-b border-slate-800 text-slate-400 uppercase tracking-wider">
              <tr>
                <th className="px-6 py-3.5">Case Identifier</th>
                <th className="px-6 py-3.5">Scenario / Reference</th>
                <th className="px-6 py-3.5">Evidence Confidence</th>
                <th className="px-6 py-3.5">Residual Value at Risk</th>
                <th className="px-6 py-3.5">Decision Risk Gate</th>
                <th className="px-6 py-3.5 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {filteredCases.map((c) => {
                const dec = c.decision?.decision || "unresolved";
                const conf = c.decision?.evidence_confidence || 0;
                const isAuto = dec === "auto_resolve";
                const isHuman = dec === "human_review";

                return (
                  <tr key={c.case_id} className="hover:bg-slate-800/30 transition">
                    <td className="px-6 py-4 font-bold text-white">
                      <div className="flex items-center space-x-2">
                        <span>{c.case_id}</span>
                        {c.pattern_cluster_id && (
                          <span className="w-2 h-2 rounded-full bg-purple-400" title="Part of recurring cluster"></span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-slate-400">
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                        {c.scenario_id || "SCN_01"}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-emerald-400">{(conf * 100).toFixed(0)}%</span>
                        <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-emerald-500"
                            style={{ width: `${Math.round(conf * 100)}%` }}
                          ></div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 font-bold text-amber-400">
                      {formatINR(c.residual_amount)}
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`px-2.5 py-0.5 rounded uppercase font-bold text-[10px] border ${
                          isAuto
                            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                            : isHuman
                            ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                            : "bg-rose-500/10 text-rose-400 border-rose-500/20"
                        }`}
                      >
                        {dec}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link
                        href={`/cases/${c.case_id}`}
                        className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-purple-600 text-white font-bold transition border border-slate-700"
                      >
                        Workspace &rarr;
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
