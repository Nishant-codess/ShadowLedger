"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { formatINR } from "../../lib/utils";
import { fetchCases, CaseDetail } from "../../lib/api";

export default function ExceptionsPage() {
  const [cases, setCases] = useState<CaseDetail[]>([]);
  const [loading, setLoading] = useState(true);

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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Unmatched Exception Queue</h1>
          <p className="text-sm text-slate-400 mt-1">
            Cases requiring latent economic event reconstruction and evidence examination.
          </p>
        </div>
        <div className="text-xs font-mono text-slate-400 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg">
          {cases.length} Open Cases
        </div>
      </div>

      {loading ? (
        <div className="py-20 text-center text-slate-500 font-mono text-sm">
          Loading exception cases...
        </div>
      ) : cases.length === 0 ? (
        <div className="bg-slate-900/40 border border-slate-800/80 rounded-xl p-12 text-center">
          <div className="text-slate-400 font-medium">No exceptions found</div>
          <p className="text-xs text-slate-500 mt-1">Run a batch from the Command Center to generate and investigate cases.</p>
          <Link
            href="/"
            className="mt-4 inline-block px-4 py-2 bg-emerald-500 text-slate-950 font-bold text-xs rounded-lg uppercase tracking-wider"
          >
            Go to Command Center
          </Link>
        </div>
      ) : (
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl overflow-hidden shadow-xl">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-900/80 border-b border-slate-800 text-slate-400 uppercase tracking-wider">
              <tr>
                <th className="px-6 py-3.5">Case ID</th>
                <th className="px-6 py-3.5">Reference / Scenario</th>
                <th className="px-6 py-3.5">Records Linked</th>
                <th className="px-6 py-3.5">Residual Shortfall</th>
                <th className="px-6 py-3.5">Decision Status</th>
                <th className="px-6 py-3.5 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {cases.map((c) => (
                <tr key={c.case_id} className="hover:bg-slate-800/30 transition">
                  <td className="px-6 py-4 font-semibold text-white">{c.case_id}</td>
                  <td className="px-6 py-4 text-slate-400">{c.scenario_id || "Unspecified"}</td>
                  <td className="px-6 py-4">{c.observation_ids.length} observations</td>
                  <td className="px-6 py-4 text-amber-400 font-bold">{formatINR(c.residual_amount)}</td>
                  <td className="px-6 py-4">
                    <span className="px-2 py-0.5 rounded text-[10px] uppercase font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                      {c.decision?.decision || "unresolved"}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <Link
                      href={`/cases/${c.case_id}`}
                      className="text-emerald-400 hover:text-emerald-300 font-semibold"
                    >
                      Investigate &rarr;
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
