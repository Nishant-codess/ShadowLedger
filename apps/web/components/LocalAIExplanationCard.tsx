"use client";

import React, { useState } from "react";
import { fetchAIExplanation, AIExplainResponse } from "../lib/api";

interface LocalAIExplanationCardProps {
  caseId: string;
  className?: string;
}

export function LocalAIExplanationCard({ caseId, className }: LocalAIExplanationCardProps) {
  const [explanation, setExplanation] = useState<AIExplainResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  async function handleGenerate() {
    setLoading(true);
    try {
      const data = await fetchAIExplanation(caseId);
      setExplanation(data);
    } finally {
      setLoading(false);
    }
  }

  function handleCopy() {
    if (explanation) {
      navigator.clipboard.writeText(explanation.narrative);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }

  return (
    <div className={`bg-slate-900/70 border border-slate-800/80 rounded-xl p-5 space-y-4 font-mono text-xs ${className || ""}`}>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800/80 pb-3 gap-2">
        <div className="flex items-center space-x-2">
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
          <span className="text-xs font-bold text-white uppercase tracking-wider">
            Evidence-Grounded AI Investigation Assistant
          </span>
        </div>

        {explanation && (
          <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
            Provider: {explanation.provider.replace("_", " ")}
          </span>
        )}
      </div>

      {!explanation ? (
        <div className="p-6 text-center bg-slate-950/50 rounded-lg border border-slate-800/60 space-y-3">
          <p className="text-slate-400 text-xs">
            Generate an evidence-grounded audit narrative explaining this discrepancy, candidate economic hypothesis, and decision rationale.
          </p>
          <button
            onClick={handleGenerate}
            disabled={loading}
            className="px-4 py-2 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs rounded-lg uppercase tracking-wider transition shadow-lg shadow-cyan-500/20"
          >
            {loading ? "Generating Evidence Briefing..." : "✨ Generate AI Investigation Narrative"}
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {/* Headline */}
          <div className="p-3 bg-cyan-950/20 border border-cyan-800/40 rounded-lg text-cyan-200 font-bold">
            {explanation.headline}
          </div>

          {/* Detailed Narrative */}
          <div className="p-4 bg-slate-950/80 rounded-lg border border-slate-800 text-slate-300 leading-relaxed whitespace-pre-line text-[11px]">
            {explanation.narrative}
          </div>

          {/* Action Bar */}
          <div className="flex items-center justify-between pt-2">
            <span className="text-[10px] text-slate-500">
              Zero hallucination risk &bull; Strictly bounded by structured facts
            </span>
            <div className="flex items-center space-x-2">
              <button
                onClick={handleCopy}
                className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-[10px] border border-slate-700 transition"
              >
                {copied ? "✓ Copied" : "Copy Briefing"}
              </button>
              <button
                onClick={handleGenerate}
                disabled={loading}
                className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-cyan-300 rounded text-[10px] border border-slate-700 transition"
              >
                {loading ? "Regenerating..." : "Regenerate"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
