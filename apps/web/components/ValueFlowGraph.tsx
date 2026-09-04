"use client";

import React, { useState } from "react";
import { formatINR } from "../lib/utils";
import { useViewMode } from "../lib/ViewModeContext";

interface GraphNode {
  id: string;
  label: string;
  node_type: string;
  amount: number;
  confidence: number;
  is_source_truth: boolean;
  is_winner?: boolean;
  source_system?: string;
  event_type?: string;
  description?: string;
  timestamp?: string;
  [key: string]: unknown;
}

interface GraphLink {
  source: string;
  target: string;
  amount: number;
  value_type: string;
  direction: string;
  confidence: number;
  [key: string]: unknown;
}

interface ValueFlowGraphProps {
  graphData: {
    nodes: GraphNode[];
    links: GraphLink[];
    node_count: number;
    link_count: number;
  };
  className?: string;
}

export function ValueFlowGraph({ graphData, className }: ValueFlowGraphProps) {
  const { isExplain } = useViewMode();
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [viewFilter, setViewFilter] = useState<"all" | "official_only">("all");
  const [showAlternatives, setShowAlternatives] = useState(false);
  const [copiedId, setCopiedId] = useState(false);

  if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
    return (
      <div className="p-8 text-center text-xs font-mono text-stone-500 bg-white rounded-2xl border border-[#e7e2d9]">
        No value-flow graph representation available for this case.
      </div>
    );
  }

  // Filter nodes if user toggles official facts only
  const visibleNodes =
    viewFilter === "official_only"
      ? graphData.nodes.filter((n) => n.is_source_truth || n.node_type === "observed")
      : graphData.nodes;

  const nodeMap = new Map(graphData.nodes.map((n) => [n.id, n]));

  // Group nodes by tier for structured flow layout
  const sourceNodes = visibleNodes.filter(
    (n) =>
      n.node_type === "observed" &&
      n.source_system !== "external_trace" &&
      (n.event_type === "payment" ||
        n.label.toLowerCase().includes("pos") ||
        n.label.toLowerCase().includes("purchase") ||
        n.label.toLowerCase().includes("fare"))
  );
  const settlementNodes = visibleNodes.filter(
    (n) => n.node_type === "observed" && !sourceNodes.some((sn) => sn.id === n.id)
  );
  const reconstructedNodes = visibleNodes.filter((n) => n.node_type !== "observed");

  const winningNodes = reconstructedNodes.filter((n) => n.is_winner === true);
  const candidateNodes = reconstructedNodes.filter((n) => n.is_winner !== true);

  const primaryReconstructedNodes = winningNodes.length > 0
    ? winningNodes
    : (reconstructedNodes.length > 0 ? [reconstructedNodes[0]] : []);
  const alternativeNodes = winningNodes.length > 0
    ? candidateNodes
    : reconstructedNodes.slice(1);

  const displayedReconstructedNodes = isExplain && !showAlternatives
    ? primaryReconstructedNodes
    : reconstructedNodes;

  const displayedNodeIds = new Set([
    ...sourceNodes.map((n) => n.id),
    ...settlementNodes.map((n) => n.id),
    ...displayedReconstructedNodes.map((n) => n.id),
  ]);

  const visibleLinks = graphData.links.filter(
    (l) => displayedNodeIds.has(l.source) && displayedNodeIds.has(l.target)
  );

  // Fallback if categorisation is ambiguous
  const hasStructuredGroups = sourceNodes.length > 0 || settlementNodes.length > 0;

  function handleCopy(id: string) {
    navigator.clipboard.writeText(id);
    setCopiedId(true);
    setTimeout(() => setCopiedId(false), 2000);
  }

  // Translate edge value type to conversational English
  function getExplainEdgeLabel(valueType: string, amount: number) {
    const vt = valueType.toLowerCase();
    if (vt.includes("settle") || vt.includes("cash")) return `settles cash (${formatINR(amount)})`;
    if (vt.includes("inventory") || vt.includes("item")) return `supplemented by inventory (${formatINR(amount)})`;
    if (vt.includes("fee") || vt.includes("mdr")) return `fee deduction (${formatINR(amount)})`;
    if (vt.includes("refund")) return `partial return (${formatINR(amount)})`;
    if (vt.includes("indirect") || vt.includes("trace")) return `corroborates deviation (${formatINR(amount)})`;
    return `accounts for ${formatINR(amount)}`;
  }

  return (
    <div className={`flex flex-col bg-white border border-[#e7e2d9] rounded-2xl overflow-hidden shadow-xs ${className || ""}`}>
      {/* Graph Header */}
      <div className="px-5 py-4 bg-[#faf8f5] border-b border-[#e7e2d9] flex flex-wrap items-center justify-between gap-3">
        <div className="space-y-0.5">
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-purple-500"></span>
            <h2 className="text-sm font-bold text-stone-900 font-sans">
              {isExplain ? "WHERE THE VALUE WENT" : "Value-Flow Graph Network"}
            </h2>
            <span className="text-[11px] font-mono text-stone-500 bg-white border border-[#e2ddd5] px-2 py-0.5 rounded-md">
              {visibleNodes.length} Nodes &bull; {visibleLinks.length} Value Edges
            </span>
          </div>
          {isExplain ? (
            <p className="text-xs text-stone-500">
              Visual directed value flow connecting source purchase, bank cash, and reconstructed settlement.
            </p>
          ) : (
            <p className="text-xs text-stone-500 font-mono">
              Directed NetworkX topological state &bull; Conservation of financial value
            </p>
          )}
        </div>

        {/* View Filter Toggle */}
        <div className="flex items-center space-x-1 bg-white p-1 rounded-xl border border-[#e2ddd5] text-xs">
          <button
            onClick={() => setViewFilter("all")}
            className={`px-3 py-1 rounded-lg font-semibold transition ${
              viewFilter === "all"
                ? "bg-[#f3e8ff] text-[#581c87] border border-[#d8b4fe] font-bold"
                : "text-stone-500 hover:text-stone-800"
            }`}
          >
            {isExplain ? "Complete Value Story" : "All Hypotheses & Facts"}
          </button>
          <button
            onClick={() => setViewFilter("official_only")}
            className={`px-3 py-1 rounded-lg font-semibold transition ${
              viewFilter === "official_only"
                ? "bg-[#e0f2fe] text-[#0369a1] border border-[#7dd3fc] font-bold"
                : "text-stone-500 hover:text-stone-800"
            }`}
          >
            {isExplain ? "Official Ledger Only" : "Observed Facts Only"}
          </button>
        </div>
      </div>

      {/* Main Graph Canvas Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 min-h-[360px]">
        {/* Graph Visual Area */}
        <div className="lg:col-span-2 p-6 sm:p-8 flex flex-col justify-between space-y-6 relative bg-[#faf8f5]/50 overflow-hidden">
          {viewFilter === "official_only" && (
            <div className="p-3 rounded-xl bg-[#fff7ed] border border-[#fdba74] text-[#7c2d12] text-xs flex items-center space-x-2">
              <span className="font-bold">⚠️ Ledger Disconnect:</span>
              <span>Inferred latent events hidden. Notice the disconnected value-flow and unclosed residual shortfall.</span>
            </div>
          )}

          {/* Connected Flow Diagram */}
          <div className="space-y-6 my-auto">
            {/* Structured 3-Tier Layout if applicable */}
            {hasStructuredGroups ? (
              <div className="flex flex-col items-center space-y-4 max-w-xl mx-auto w-full">
                {/* Tier 1: Source Purchase / Gross Inflow */}
                {sourceNodes.map((node) => (
                  <div key={node.id} className="w-full flex flex-col items-center">
                    <div
                      onClick={() => setSelectedNode(node)}
                      className={`cursor-pointer p-4 rounded-xl border-2 transition-all w-full sm:w-80 text-center shadow-xs bg-[#f0f9ff] border-[#7dd3fc] text-[#0369a1] ${
                        selectedNode?.id === node.id ? "ring-2 ring-stone-900 scale-102" : "hover:scale-101"
                      }`}
                    >
                      <div className="text-[10px] font-bold uppercase tracking-wider text-blue-700">
                        {isExplain ? "Observed Inflow" : "Level 1: OBSERVED"}
                      </div>
                      <div className="font-bold text-stone-900 text-sm mt-0.5">{node.label}</div>
                      <div className="text-lg font-extrabold text-stone-900 font-mono mt-1">
                        {formatINR(node.amount)}
                      </div>
                    </div>

                    {/* Visual Directed Edge Arrow Downward */}
                    <div className="flex items-center justify-center my-1 text-stone-400 font-bold text-lg">
                      ↓
                    </div>
                  </div>
                ))}

                {/* Tier 2: Settlements & Reconstructed Explanations */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full">
                  {/* Settlement Node(s) */}
                  {settlementNodes.map((node) => (
                    <div
                      key={node.id}
                      onClick={() => setSelectedNode(node)}
                      className={`cursor-pointer p-4 rounded-xl border-2 transition-all flex flex-col justify-between shadow-xs bg-[#f0f9ff] border-[#7dd3fc] text-[#0369a1] ${
                        selectedNode?.id === node.id ? "ring-2 ring-stone-900 scale-102" : "hover:scale-101"
                      }`}
                    >
                      <div>
                        <div className="text-[10px] font-bold uppercase tracking-wider text-blue-700">
                          {isExplain
                            ? node.source_system === "external_trace"
                              ? "Secondary Digital Trace"
                              : "Official Cash Settlement"
                            : "OBSERVED SETTLEMENT"}
                        </div>
                        <div className="font-bold text-stone-900 text-sm mt-0.5">{node.label}</div>
                      </div>
                      <div className="text-lg font-extrabold text-stone-900 font-mono mt-2">
                        {formatINR(node.amount)}
                      </div>
                    </div>
                  ))}

                  {/* Reconstructed Latent Node(s) */}
                  {displayedReconstructedNodes.map((node) => {
                    const isWinner = node.is_winner === true;
                    return (
                      <div
                        key={node.id}
                        onClick={() => setSelectedNode(node)}
                        className={`cursor-pointer p-4 rounded-xl border-2 transition-all flex flex-col justify-between shadow-xs ${
                          isWinner
                            ? "bg-[#faf5ff] border-[#a855f7] ring-2 ring-[#a855f7]/30 text-[#581c87]"
                            : "bg-white border-dashed border-stone-300 opacity-70 text-stone-600 hover:opacity-100"
                        } ${selectedNode?.id === node.id ? "ring-2 ring-stone-900 scale-102" : "hover:scale-101"}`}
                      >
                        <div>
                          <div className="flex items-center justify-between">
                            <span
                              className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${
                                isWinner
                                  ? "bg-[#f3e8ff] text-[#581c87] border border-[#d8b4fe]"
                                  : "bg-stone-100 text-stone-500"
                              }`}
                            >
                              {isWinner ? "🟣 SELECTED EXPLANATION" : "○ DISCARDED ALTERNATIVE"}
                            </span>
                            <span className="text-[10px] font-mono font-bold text-stone-500">
                              {(node.confidence * 100).toFixed(0)}% Conf
                            </span>
                          </div>

                          <div className="font-bold text-stone-900 text-sm mt-1.5">
                            {isExplain && isWinner && node.label.toLowerCase().includes("inventory")
                              ? "Dairy Milk Chocolate Change (₹2.00)"
                              : isExplain && isWinner && (node.label.toLowerCase().includes("deviation") || node.label.toLowerCase().includes("off_ledger"))
                              ? `Off-Ledger Payment Deviation (${formatINR(node.amount)})`
                              : node.label}
                          </div>
                        </div>

                        <div className="text-lg font-extrabold text-stone-900 font-mono mt-2">
                          {formatINR(node.amount)}
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Candidate Explanation Notice & Toggle in Explain Mode */}
                {isExplain && alternativeNodes.length > 0 ? (
                  <div className="text-center pt-2 space-y-1">
                    <button
                      type="button"
                      onClick={() => setShowAlternatives(!showAlternatives)}
                      className="text-xs text-purple-700 hover:text-purple-900 font-bold underline cursor-pointer inline-flex items-center space-x-1"
                    >
                      <span>
                        {showAlternatives
                          ? "▲ Hide discarded candidate hypotheses"
                          : `▼ View ${alternativeNodes.length} discarded candidate hypotheses (Fee, Refund, Credit)`}
                      </span>
                    </button>
                    {!showAlternatives && (
                      <p className="text-[11px] text-stone-500 italic font-handwriting">
                        ✎ Note: ShadowLedger evaluated alternative hypotheses; the purple card is the verified selection.
                      </p>
                    )}
                  </div>
                ) : (
                  reconstructedNodes.length > 1 && (
                    <div className="text-center font-handwriting text-stone-500 text-sm pt-1">
                      ✎ Note: ShadowLedger evaluated alternative hypotheses; the purple card is the verified selection.
                    </div>
                  )
                )}
              </div>
            ) : (
              /* Generic Node Flow Grid if unstructured */
              <div className="flex flex-wrap items-center justify-center gap-4 py-4">
                {visibleNodes.map((node) => {
                  const isLatent = node.node_type === "inferred_latent";
                  const isWinner = node.is_winner === true;
                  return (
                    <div
                      key={node.id}
                      onClick={() => setSelectedNode(node)}
                      className={`cursor-pointer p-4 rounded-xl border transition-all min-w-[160px] max-w-[220px] shadow-xs ${
                        isLatent
                          ? isWinner
                            ? "bg-[#faf5ff] border-2 border-[#a855f7] text-[#581c87]"
                            : "bg-white border-dashed border-stone-300 opacity-60 text-stone-500"
                          : "bg-[#f0f9ff] border-2 border-[#7dd3fc] text-[#0369a1]"
                      } ${selectedNode?.id === node.id ? "ring-2 ring-stone-900 scale-105" : "hover:scale-102"}`}
                    >
                      <div className="text-[10px] font-bold uppercase tracking-wider mb-1">
                        {isLatent ? (isWinner ? "🟣 Selected" : "○ Alternative") : "Observed"}
                      </div>
                      <div className="text-xs font-bold text-stone-900 truncate font-sans">
                        {node.label}
                      </div>
                      <div className="text-sm font-extrabold mt-2 font-mono text-stone-900">
                        {formatINR(node.amount)}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Direct Graph Links Display (Derived from graphData.links) */}
          <div className="pt-4 border-t border-[#e7e2d9] space-y-2">
            <div className="flex items-center justify-between text-[10px] uppercase font-bold text-stone-500 tracking-wider">
              <span>{isExplain ? "Verified Value Connections" : "NetworkX Topological Edges"}</span>
              <span className="font-normal lowercase font-sans">derived from data contract</span>
            </div>

            <div className="space-y-1.5 max-h-24 overflow-y-auto pr-1 text-xs">
              {visibleLinks.map((link, idx) => {
                const sourceNode = nodeMap.get(link.source);
                const targetNode = nodeMap.get(link.target);
                const sourceLabel = isExplain && sourceNode ? sourceNode.label : link.source;
                const targetLabel = isExplain && targetNode ? targetNode.label : link.target;
                return (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-2 rounded-lg bg-white border border-[#e7e2d9] text-stone-700"
                  >
                    <div className="flex items-center space-x-2 truncate">
                      <span className="font-semibold text-stone-900 truncate max-w-[140px]" title={sourceLabel}>
                        {sourceLabel}
                      </span>
                      <span className="text-purple-600 font-bold">&rarr;</span>
                      <span className="font-semibold text-stone-900 truncate max-w-[140px]" title={targetLabel}>
                        {targetLabel}
                      </span>
                    </div>
                    <div className="flex items-center space-x-2 shrink-0">
                      <span className="text-[11px] text-stone-500 italic">
                        {isExplain ? getExplainEdgeLabel(link.value_type, link.amount) : link.value_type}
                      </span>
                      <span className="font-mono font-bold text-stone-900">
                        {formatINR(link.amount)}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Node Inspector Panel (Explain vs Investigate) */}
        <div className="border-t lg:border-t-0 lg:border-l border-[#e7e2d9] p-5 bg-[#ffffff] text-xs flex flex-col justify-between">
          <div>
            <div className="border-b border-[#e7e2d9] pb-3 mb-4 flex items-center justify-between">
              <span className="font-bold text-stone-900 uppercase tracking-wider text-xs font-sans">
                {isExplain ? "Fact & Hypothesis Inspector" : "Node Inspector (Auditor)"}
              </span>
              {selectedNode && (
                <button
                  onClick={() => setSelectedNode(null)}
                  className="text-[11px] text-stone-400 hover:text-stone-800"
                >
                  Clear Selection
                </button>
              )}
            </div>

            {selectedNode ? (
              <div className="space-y-3.5">
                {/* Identifier */}
                <div>
                  <div className="text-[10px] uppercase font-bold text-stone-400">
                    {isExplain ? "Entity / Node" : "Node Identifier"}
                  </div>
                  <div className="flex items-center justify-between mt-0.5">
                    <div className="font-bold text-stone-900 truncate text-sm">
                      {isExplain ? selectedNode.label : selectedNode.id}
                    </div>
                    {!isExplain && (
                      <button
                        onClick={() => handleCopy(selectedNode.id)}
                        className="text-[10px] bg-stone-100 hover:bg-stone-200 px-2 py-0.5 rounded text-stone-700 font-mono transition"
                      >
                        {copiedId ? "✓ Copied" : "Copy ID"}
                      </button>
                    )}
                  </div>
                </div>

                {/* Classification */}
                <div>
                  <div className="text-[10px] uppercase font-bold text-stone-400">Classification</div>
                  <div className="mt-0.5">
                    {selectedNode.is_source_truth ? (
                      <span className="badge-observed text-[11px] font-bold px-2 py-0.5 rounded-full inline-block">
                        Observed Official Ledger Fact
                      </span>
                    ) : (
                      <span className="badge-reconstructed text-[11px] font-bold px-2 py-0.5 rounded-full inline-block">
                        Reconstructed Latent Event
                      </span>
                    )}
                  </div>
                </div>

                {/* Amount */}
                <div>
                  <div className="text-[10px] uppercase font-bold text-stone-400">Economic Value</div>
                  <div className="text-xl font-extrabold text-stone-900 font-mono mt-0.5">
                    {formatINR(selectedNode.amount)}
                  </div>
                </div>

                {/* Evidence Confidence */}
                <div>
                  <div className="text-[10px] uppercase font-bold text-stone-400">Evidence Confidence</div>
                  <div className="font-bold text-emerald-700 font-mono text-sm mt-0.5">
                    {(selectedNode.confidence * 100).toFixed(1)}% Multi-Dimensional Score
                  </div>
                </div>

                {/* Description if present */}
                {selectedNode.description && (
                  <div>
                    <div className="text-[10px] uppercase font-bold text-stone-400">Details</div>
                    <div className="text-stone-700 text-xs mt-0.5 bg-stone-50 p-2 rounded-lg border border-stone-200">
                      {selectedNode.description}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="py-12 text-center text-stone-400 text-xs space-y-2">
                <span className="text-2xl block">🔍</span>
                <p>Click any node in the value-flow graph to inspect its provenance, source facts, and evidence linkage.</p>
              </div>
            )}
          </div>

          <div className="pt-4 border-t border-[#e7e2d9] text-[11px] text-stone-500 font-sans">
            Directed NetworkX Graph &bull; Value Conservation Invariant
          </div>
        </div>
      </div>
    </div>
  );
}
