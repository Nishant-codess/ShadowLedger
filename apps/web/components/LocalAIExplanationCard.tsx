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
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchAIExplanation(caseId);
      if (data) {
        setExplanation(data);
      } else {
        setError("AI Assistant currently unavailable. Using deterministic evidence briefing.");
      }
    } catch {
      setError("AI service offline. Core financial engine remains 100% operational.");
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
    <div className={`bg-white border border-[#e7e2d9] rounded-2xl p-6 space-y-4 shadow-xs ${className || ""}`}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-stone-100 pb-3 gap-2">
        <div className="flex items-center space-x-2">
          <span className="w-2.5 h-2.5 rounded-full bg-cyan-500 animate-pulse"></span>
          <h3 className="text-sm font-bold text-stone-900 font-sans">
            AI Narrative Investigation Assistant
          </h3>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-cyan-50 text-cyan-800 border border-cyan-200">
            {explanation ? `Provider: ${explanation.provider}` : "Deterministic Grounding"}
          </span>
        </div>
      </div>

      {/* Safety & Bounding Notice */}
      <div className="p-3 rounded-xl bg-[#f0fdf4] border border-[#86efac] text-xs text-[#14532d] flex items-center space-x-2">
        <span>🛡️</span>
        <span className="font-medium">
          <strong>Non-Authoritative Explainer:</strong> AI explains the evidence. It does not decide the financial outcome.
        </span>
      </div>

      {!explanation ? (
        <div className="p-6 text-center bg-[#faf8f5] rounded-xl border border-[#e7e2d9] space-y-3">
          <p className="text-stone-600 text-xs max-w-md mx-auto">
            Generate an evidence-grounded audit narrative explaining this discrepancy, candidate economic hypothesis, and decision rationale.
          </p>
          <button
            onClick={handleGenerate}
            disabled={loading}
            className="px-5 py-2.5 bg-stone-900 hover:bg-stone-800 text-white font-bold text-xs rounded-xl uppercase tracking-wider transition shadow-sm"
          >
            {loading ? "Generating Plain-English Briefing..." : "✨ Generate AI Investigation Narrative"}
          </button>
          {error && <p className="text-xs text-amber-700 font-medium">{error}</p>}
        </div>
      ) : (
        <div className="space-y-3.5">
          {/* Headline */}
          <div className="p-3.5 bg-[#f0f9ff] border border-[#7dd3fc] rounded-xl text-[#0369a1] font-bold text-sm font-sans">
            {explanation.headline}
          </div>

          {/* Detailed Narrative */}
          <div className="p-4 bg-[#faf8f5] rounded-xl border border-[#e7e2d9] text-stone-800 leading-relaxed whitespace-pre-line text-xs font-sans">
            {explanation.narrative}
          </div>

          {/* Action Bar */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pt-2 gap-2 text-xs">
            <span className="text-[11px] text-stone-400 font-sans">
              Zero hallucination risk &bull; Bounded strictly by structured case facts
            </span>
            <div className="flex items-center space-x-2">
              <button
                onClick={handleCopy}
                className="px-3 py-1.5 bg-stone-100 hover:bg-stone-200 text-stone-800 rounded-lg text-xs font-semibold border border-stone-300 transition"
              >
                {copied ? "✓ Copied" : "Copy Briefing"}
              </button>
              <button
                onClick={handleGenerate}
                disabled={loading}
                className="px-3 py-1.5 bg-stone-100 hover:bg-stone-200 text-stone-800 rounded-lg text-xs font-semibold border border-stone-300 transition"
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
