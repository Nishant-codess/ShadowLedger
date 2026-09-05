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
  hypothesis_type?: string;
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

  // Check if this case is an off-ledger / multi-trace scenario (Hero B: Cab Ride)
  const hasExternalTrace = visibleNodes.some((n) => n.source_system === "external_trace");
  const isOffLedgerCase =
    hasExternalTrace ||
    visibleNodes.some(
      (n) =>
        (n.hypothesis_type && String(n.hypothesis_type).includes("off_ledger")) ||
        n.node_type === "unobserved_deviation" ||
        n.label.toLowerCase().includes("ride_platform") ||
        n.label.toLowerCase().includes("cab")
    );

  // Reconstructed latent nodes
  const reconstructedNodes = visibleNodes.filter((n) => n.node_type !== "observed");
  const winningNodes = reconstructedNodes.filter((n) => n.is_winner === true);
  const candidateNodes = reconstructedNodes.filter((n) => n.is_winner !== true);

  const primaryReconstructedNodes =
    winningNodes.length > 0
      ? winningNodes
      : reconstructedNodes.length > 0
      ? [reconstructedNodes[0]]
      : [];
  const alternativeNodes =
    winningNodes.length > 0 ? candidateNodes : reconstructedNodes.slice(1);

  const displayedReconstructedNodes =
    isExplain ? primaryReconstructedNodes : reconstructedNodes;

  // Nodes for Off-Ledger topology (Hero B)
  const platformNode = visibleNodes.find(
    (n) =>
      n.source_system === "ride_platform" ||
      n.label.toLowerCase().includes("ride") ||
      n.label.toLowerCase().includes("cab") ||
      (n.node_type === "observed" && n.source_system !== "external_trace")
  );
  const traceNode = visibleNodes.find(
    (n) =>
      n.source_system === "external_trace" ||
      n.label.toLowerCase().includes("external_trace")
  );

  // Nodes for Standard Inflow Split topology (Hero A)
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

  // Math for Off-Ledger topology (Hero B)
  const platformAmount = platformNode ? Number(platformNode.amount) || 0 : 0;
  const traceAmount = traceNode
    ? Number(traceNode.amount) || 0
    : primaryReconstructedNodes[0]
    ? Number(primaryReconstructedNodes[0].amount) || 0
    : 0;
  const totalEconomicValue = platformAmount + traceAmount;

  // Math for Standard Split topology (Hero A)
  const totalInflow = sourceNodes.reduce((sum, n) => sum + (Number(n.amount) || 0), 0);
  const totalSettlement = settlementNodes.reduce((sum, n) => sum + (Number(n.amount) || 0), 0);
  const totalReconstructed = primaryReconstructedNodes.reduce(
    (sum, n) => sum + (Number(n.amount) || 0),
    0
  );
  const totalAccounted = totalSettlement + totalReconstructed;
  const remainingResidual = Math.max(0, totalInflow - totalAccounted);

  // Displayed nodes for links filtering
  const displayedNodeIds = new Set([
    ...(platformNode ? [platformNode.id] : []),
    ...(traceNode ? [traceNode.id] : []),
    ...sourceNodes.map((n) => n.id),
    ...settlementNodes.map((n) => n.id),
    ...displayedReconstructedNodes.map((n) => n.id),
  ]);

  const visibleLinks = graphData.links.filter(
    (l) => displayedNodeIds.has(l.source) && displayedNodeIds.has(l.target)
  );

  function handleCopy(id: string) {
    navigator.clipboard.writeText(id);
    setCopiedId(true);
    setTimeout(() => setCopiedId(false), 2000);
  }

  // Friendly human-readable node labels for Explain mode
  function getFriendlyNodeLabel(node: GraphNode | undefined, explainMode: boolean) {
    if (!node) return "";
    if (!explainMode) return node.label;
    const lbl = (node.label || "").toLowerCase();
    if (lbl.includes("kirana") || (lbl.includes("pos") && node.amount === 100)) {
      return "POS Purchase (₹100.00)";
    }
    if (node.source_system === "bank" || lbl.includes("bank") || lbl.includes("neft")) {
      return `Bank Cash Settlement (${formatINR(node.amount)})`;
    }
    if (
      node.node_type === "inventory_asset" ||
      lbl.includes("cadbury") ||
      lbl.includes("candy") ||
      lbl.includes("eclairs")
    ) {
      return "Cadbury Eclairs Candy (₹2.00)";
    }
    if (node.source_system === "ride_platform" || lbl.includes("ride_platform") || lbl.includes("cab")) {
      return `Ride Platform Fare (${formatINR(node.amount)})`;
    }
    if (node.source_system === "external_trace" || lbl.includes("external_trace") || lbl.includes("upi")) {
      return `Driver Personal UPI Trace (${formatINR(node.amount)})`;
    }
    if (node.hypothesis_type === "off_ledger_deviation" || node.node_type === "unobserved_deviation") {
      return `Off-Ledger Payment Deviation (${formatINR(node.amount)})`;
    }
    if (node.hypothesis_type === "inventory_settlement") {
      return `Cadbury Eclairs Candy Change (${formatINR(node.amount)})`;
    }
    if (node.hypothesis_type === "fee_adjustment") {
      return `Platform Processing Fee (${formatINR(node.amount)})`;
    }
    return node.label;
  }

  // Translate edge value type to conversational English
  function getExplainEdgeLabel(
    valueType: string,
    amount: number,
    sourceNode?: GraphNode,
    targetNode?: GraphNode
  ) {
    const vt = (valueType || "").toLowerCase();
    if (
      sourceNode?.source_system === "external_trace" ||
      vt.includes("trace") ||
      vt.includes("indirect")
    ) {
      return `corroborates deviation (${formatINR(amount)})`;
    }
    if (
      sourceNode?.source_system === "ride_platform" &&
      (targetNode?.hypothesis_type === "off_ledger_deviation" ||
        targetNode?.node_type === "unobserved_deviation")
    ) {
      return `links trip to surcharge (${formatINR(amount)})`;
    }
    if (vt.includes("settle") || vt.includes("cash")) return `settles cash (${formatINR(amount)})`;
    if (vt.includes("inventory") || vt.includes("item"))
      return `supplemented by inventory (${formatINR(amount)})`;
    if (vt.includes("fee") || vt.includes("mdr")) return `fee deduction (${formatINR(amount)})`;
    if (vt.includes("refund")) return `partial return (${formatINR(amount)})`;
    return `accounts for ${formatINR(amount)}`;
  }

  return (
    <div
      className={`flex flex-col bg-white border border-[#e7e2d9] rounded-2xl overflow-hidden shadow-xs ${
        className || ""
      }`}
    >
      {/* Graph Header */}
      <div className="px-5 py-4 bg-[#faf8f5] border-b border-[#e7e2d9] flex flex-wrap items-center justify-between gap-3">
        <div className="space-y-0.5">
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-purple-500"></span>
            <h2 className="text-sm font-bold text-stone-900 font-sans">
              {isExplain ? "WHERE THE VALUE WENT" : "VALUE-FLOW GRAPH NETWORK"}
            </h2>
            <span className="text-[11px] font-mono text-stone-500 bg-white border border-[#e2ddd5] px-2 py-0.5 rounded-md">
              {visibleNodes.length} Nodes &bull; {visibleLinks.length} Value Edges
            </span>
          </div>
          {isExplain ? (
            <p className="text-xs text-stone-500">
              {isOffLedgerCase
                ? "Visual directed value flow connecting platform fare, external UPI trace, and reconstructed surcharge."
                : "Visual directed value flow connecting source purchase, bank cash, and reconstructed settlement."}
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
      <div className={`grid ${isExplain ? "grid-cols-1" : "grid-cols-1 lg:grid-cols-3"} min-h-[360px]`}>
        {/* Graph Visual Area */}
        <div
          className={`${
            isExplain ? "col-span-1" : "lg:col-span-2"
          } p-6 sm:p-8 flex flex-col justify-between space-y-6 relative bg-[#faf8f5]/50 overflow-hidden`}
        >
          {viewFilter === "official_only" && (
            <div className="p-3 rounded-xl bg-[#fff7ed] border border-[#fdba74] text-[#7c2d12] text-xs flex items-center space-x-2">
              <span className="font-bold">⚠️ Ledger Disconnect:</span>
              <span>
                {isOffLedgerCase
                  ? "Inferred latent events hidden. Notice the official platform ledger only records ₹150.00, missing the ₹50.00 off-ledger driver surcharge."
                  : "Inferred latent events hidden. Notice the disconnected value-flow and unclosed residual shortfall."}
              </span>
            </div>
          )}

          {/* Connected Flow Diagram */}
          <div className="space-y-6 my-auto">
            {isOffLedgerCase ? (
              /* ============================================================
                 TOPOLOGY B: OFF-LEDGER / MULTI-TRACE SCENARIO (HERO B: CAB RIDE)
                 ============================================================ */
              <div className="flex flex-col items-center space-y-4 max-w-xl mx-auto w-full">
                {/* Tier 1: Dual Observed Transactions / Traces */}
                <div className="w-full">
                  <div className="text-center mb-2">
                    <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-blue-700 bg-blue-50 border border-blue-200 px-2.5 py-0.5 rounded-full">
                      {isExplain ? "Observed Transactions & Digital Traces" : "Level 1: OBSERVED MULTI-SOURCE INPUTS"}
                    </span>
                  </div>

                  <div className={`grid ${traceNode ? "grid-cols-1 sm:grid-cols-2" : "grid-cols-1 max-w-sm mx-auto"} gap-4 w-full`}>
                    {/* Card 1: Official Platform Fare */}
                    {platformNode && (
                      <div
                        onClick={() => setSelectedNode(platformNode)}
                        className={`cursor-pointer p-4 rounded-xl border-2 transition-all shadow-xs bg-[#f0f9ff] border-[#7dd3fc] text-[#0369a1] ${
                          selectedNode?.id === platformNode.id
                            ? "ring-2 ring-stone-900 scale-102"
                            : "hover:scale-101"
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] font-bold uppercase tracking-wider text-blue-700 bg-white/80 border border-blue-200 px-2 py-0.5 rounded-full">
                            {isExplain ? "Official In-App Record" : "PRIMARY OBSERVED"}
                          </span>
                          <span className="text-[10px] font-mono text-stone-500 font-bold">Trip Fare</span>
                        </div>
                        <div className="font-bold text-stone-900 text-sm mt-1.5">
                          {isExplain ? "Ride Platform Official Fare" : platformNode.label}
                        </div>
                        <div className="text-xl font-extrabold text-stone-900 font-mono mt-2">
                          {formatINR(platformNode.amount)}
                        </div>
                        {platformNode.description && (
                          <div className="text-[11px] text-stone-500 mt-1 font-sans truncate" title={platformNode.description}>
                            {platformNode.description}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Card 2: Secondary Digital Trace (Driver Personal UPI) */}
                    {traceNode ? (
                      <div
                        onClick={() => setSelectedNode(traceNode)}
                        className={`cursor-pointer p-4 rounded-xl border-2 transition-all shadow-xs bg-[#f0fdfa] border-[#5eead4] text-[#0f766e] ${
                          selectedNode?.id === traceNode.id
                            ? "ring-2 ring-stone-900 scale-102"
                            : "hover:scale-101"
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] font-bold uppercase tracking-wider text-teal-800 bg-white/80 border border-teal-200 px-2 py-0.5 rounded-full">
                            {isExplain ? "⚡ Secondary Digital Trace" : "EXTERNAL TRACE"}
                          </span>
                          <span className="text-[10px] font-mono text-stone-500 font-bold">Same Timestamp</span>
                        </div>
                        <div className="font-bold text-stone-900 text-sm mt-1.5">
                          {isExplain ? "Driver Personal UPI Trace" : traceNode.label}
                        </div>
                        <div className="text-xl font-extrabold text-stone-900 font-mono mt-2">
                          {formatINR(traceNode.amount)}
                        </div>
                        {traceNode.description && (
                          <div className="text-[11px] text-stone-500 mt-1 font-sans truncate" title={traceNode.description}>
                            {traceNode.description}
                          </div>
                        )}
                      </div>
                    ) : (
                      /* Cash-only off-ledger scenario (SCN_09) */
                      <div className="p-4 rounded-xl border-2 border-dashed border-stone-300 bg-stone-50/50 text-stone-500 text-center flex flex-col justify-center">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-stone-400">Off-Ledger Cash Demand</span>
                        <div className="font-bold text-stone-700 text-xs mt-1">Direct Cash Demand</div>
                        <div className="text-stone-400 text-[11px] mt-0.5">No secondary digital trace detected</div>
                      </div>
                    )}
                  </div>

                  {/* Directed Flow Connector: Converging into Reconstructed Deviation */}
                  <div className="w-full flex flex-col items-center my-3 relative">
                    <div className="w-3/4 max-w-md h-5 border-b-2 border-l-2 border-r-2 border-stone-300 rounded-b-xl relative">
                      <div className="absolute -top-2 -left-1 text-blue-500 font-bold text-xs leading-none">
                        ▲
                      </div>
                      <div className="absolute -top-2 -right-1 text-teal-500 font-bold text-xs leading-none">
                        ▲
                      </div>
                      <div className="absolute -bottom-3 left-1/2 -translate-x-1/2 bg-white px-3 py-0.5 rounded-full border border-stone-200 text-[9px] font-mono font-bold text-stone-600 uppercase tracking-wider shadow-2xs whitespace-nowrap">
                        {isExplain ? "Off-Ledger Surcharge Corroboration" : "Multi-Source Trace Corroboration"}
                      </div>
                    </div>
                    <div className="w-0.5 h-6 bg-gradient-to-b from-stone-300 to-purple-500"></div>
                    <div className="text-purple-600 font-bold text-xs leading-none -mt-1">
                      ▼
                    </div>
                  </div>
                </div>

                {/* Tier 2: Selected Latent Explanation (Off-Ledger Payment Deviation) */}
                {primaryReconstructedNodes.map((node) => {
                  return (
                    <div
                      key={node.id}
                      onClick={() => setSelectedNode(node)}
                      className={`cursor-pointer p-4 sm:p-5 rounded-xl border-2 transition-all w-full max-w-lg shadow-xs bg-[#faf5ff] border-[#a855f7] ring-2 ring-[#a855f7]/30 text-[#581c87] ${
                        selectedNode?.id === node.id ? "ring-2 ring-stone-900 scale-102" : "hover:scale-101"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-[#f3e8ff] text-[#581c87] border border-[#d8b4fe]">
                          🟣 {isExplain ? "SELECTED EXPLANATION" : "LEVEL 2: INFERRED LATENT EVENT"}
                        </span>
                        <span className="text-[10px] font-mono font-bold text-purple-900 bg-purple-100 px-2 py-0.5 rounded-md">
                          {(node.confidence * 100).toFixed(0)}% Evidence Confidence
                        </span>
                      </div>

                      <div className="flex items-center justify-between mt-2">
                        <div>
                          <div className="font-bold text-stone-900 text-base">
                            {isExplain ? "Off-Ledger Payment Deviation" : node.label}
                          </div>
                          <p className="text-xs text-stone-600 mt-0.5">
                            {isExplain
                              ? "Driver collected ₹50.00 off-ledger surcharge (toll/AC) outside the official platform."
                              : "Unobserved off-ledger deviation corroborated by external digital trace."}
                          </p>
                        </div>
                        <div className="text-2xl font-black text-stone-900 font-mono ml-4 shrink-0">
                          {formatINR(node.amount)}
                        </div>
                      </div>
                    </div>
                  );
                })}

                {/* Directed Flow Connector: To Total Footprint */}
                <div className="w-full flex flex-col items-center my-1 relative">
                  <div className="w-0.5 h-6 bg-gradient-to-b from-purple-500 to-emerald-500"></div>
                  <div className="bg-white px-2.5 py-0.5 rounded-full border border-stone-200 text-[9px] font-mono font-bold text-stone-600 uppercase tracking-wider shadow-2xs -my-2 z-10">
                    {isExplain ? "Total Economic Footprint" : "Conservation State"}
                  </div>
                  <div className="w-0.5 h-6 bg-gradient-to-b from-purple-500 to-emerald-500"></div>
                  <div className="text-emerald-600 font-bold text-xs leading-none -mt-1">
                    ▼
                  </div>
                </div>

                {/* Tier 3: Total Accounting & Governance Decision */}
                <div
                  className={`p-4 rounded-xl border-2 transition-all w-full max-w-lg text-center shadow-xs ${
                    viewFilter === "official_only"
                      ? "bg-[#fff7ed] border-[#fdba74]"
                      : "bg-[#f0fdf4] border-[#86efac]"
                  }`}
                >
                  <div
                    className={`text-[10px] font-bold uppercase tracking-wider ${
                      viewFilter === "official_only" ? "text-orange-800" : "text-emerald-800"
                    }`}
                  >
                    {viewFilter === "official_only"
                      ? isExplain
                        ? "Official Ledger Recorded Value"
                        : "Observed Ledger Only"
                      : isExplain
                      ? "Total Economic Value Reconstructed"
                      : "Total Accounted State"}
                  </div>
                  <div className="font-extrabold text-stone-900 text-lg mt-0.5 font-mono">
                    {formatINR(viewFilter === "official_only" ? platformAmount : totalEconomicValue)}{" "}
                    {viewFilter === "official_only" ? "RECORDED IN LEDGER" : "ACCOUNTED"}
                  </div>
                  <div className="text-xs font-semibold text-stone-600 mt-1">
                    {viewFilter === "official_only"
                      ? `${formatINR(platformAmount)} Official In-App Fare • ${formatINR(
                          traceAmount
                        )} Off-Ledger Surcharge Omitted from Ledger`
                      : `${formatINR(platformAmount)} Platform Fare + ${formatINR(
                          traceAmount
                        )} Off-Ledger Surcharge = ${formatINR(
                          totalEconomicValue
                        )} Total Economic Activity`}
                  </div>
                  <div
                    className={`mt-2.5 pt-2 border-t flex items-center justify-center space-x-1.5 text-xs font-bold py-1.5 px-3 rounded-lg border ${
                      viewFilter === "official_only"
                        ? "border-orange-300 bg-orange-50/80 text-orange-900"
                        : "border-amber-300 bg-amber-50 text-amber-800"
                    }`}
                  >
                    <span>⚠️</span>
                    <span>
                      {viewFilter === "official_only"
                        ? "Ledger Disconnect • Secondary digital trace is unlinked without ShadowLedger reconstruction"
                        : "Escalated to Human Review • Policy Rule: Off-ledger deviations require operator sign-off"}
                    </span>
                  </div>
                </div>

                {/* Discarded candidate hypotheses toggle */}
                {isExplain && alternativeNodes.length > 0 && (
                  <div className="text-center pt-1 space-y-1 w-full max-w-lg">
                    <button
                      type="button"
                      onClick={() => setShowAlternatives(!showAlternatives)}
                      className="text-xs text-purple-700 hover:text-purple-900 font-bold underline cursor-pointer inline-flex items-center space-x-1"
                    >
                      <span>
                        {showAlternatives
                          ? "▲ Hide discarded candidate hypotheses"
                          : `▼ View ${alternativeNodes.length} discarded candidate hypotheses (Refund, Credit Issue)`}
                      </span>
                    </button>
                    {!showAlternatives && (
                      <p className="text-[11px] text-stone-500 italic font-handwriting">
                        ✎ Note: ShadowLedger evaluated alternative hypotheses; off-ledger payment deviation is the verified selection.
                      </p>
                    )}

                    {/* Candidate nodes expanded */}
                    {showAlternatives && (
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 text-left">
                        {alternativeNodes.map((alt) => (
                          <div
                            key={alt.id}
                            onClick={() => setSelectedNode(alt)}
                            className="p-3 rounded-lg border border-dashed border-stone-300 bg-white/80 text-stone-600 opacity-80 hover:opacity-100 cursor-pointer shadow-2xs"
                          >
                            <div className="flex items-center justify-between text-[10px]">
                              <span className="font-bold uppercase text-stone-500">○ Discarded Candidate</span>
                              <span className="font-mono">{(alt.confidence * 100).toFixed(0)}% Conf</span>
                            </div>
                            <div className="text-xs font-semibold text-stone-800 mt-1">{alt.label}</div>
                            <div className="font-mono text-sm font-bold text-stone-900 mt-0.5">{formatINR(alt.amount)}</div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ) : (
              /* ============================================================
                 TOPOLOGY A: STANDARD INFLOW SPLIT (HERO A: KIRANA STORE / POS)
                 ============================================================ */
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
                      <div className="font-bold text-stone-900 text-sm mt-0.5">
                        {isExplain && node.label.toLowerCase().includes("kirana")
                          ? "POS Purchase (₹100.00)"
                          : isExplain && node.label.toLowerCase().includes("cab")
                          ? "Official Cab Fare (₹150.00)"
                          : node.label}
                      </div>
                      <div className="text-lg font-extrabold text-stone-900 font-mono mt-1">
                        {formatINR(node.amount)}
                      </div>
                    </div>

                    {/* Visual Directed Edge Branching Flow */}
                    <div className="w-full flex flex-col items-center my-2 relative">
                      <div className="w-0.5 h-5 bg-gradient-to-b from-blue-400 to-stone-300"></div>
                      <div className="w-3/4 max-w-lg h-5 border-t-2 border-l-2 border-r-2 border-stone-300 rounded-t-xl relative">
                        <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-white px-2.5 py-0.5 rounded-full border border-stone-200 text-[9px] font-mono font-bold text-stone-500 uppercase tracking-wider shadow-2xs">
                          {isExplain ? "Conserved Value Split" : "Directed Flow Edges"}
                        </div>
                        <div className="absolute -bottom-2 -left-1 text-blue-500 font-bold text-xs leading-none">
                          ▼
                        </div>
                        <div className="absolute -bottom-2 -right-1 text-purple-500 font-bold text-xs leading-none">
                          ▼
                        </div>
                      </div>
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
                              : "Official Bank Settlement"
                            : "OBSERVED SETTLEMENT"}
                        </div>
                        <div className="font-bold text-stone-900 text-sm mt-0.5">
                          {isExplain && node.label.toLowerCase().includes("neft")
                            ? "Bank Cash Settlement (₹98.00)"
                            : isExplain && node.label.toLowerCase().includes("upi")
                            ? "Driver Personal UPI Trace (₹50.00)"
                            : node.label}
                        </div>
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
                            {isExplain && isWinner && (node.label.toLowerCase().includes("inventory") || (node.hypothesis_type && node.hypothesis_type.includes("inventory")))
                              ? "Cadbury Eclairs Candy Change (₹2.00)"
                              : isExplain && isWinner && (node.label.toLowerCase().includes("deviation") || (node.hypothesis_type && node.hypothesis_type.includes("off_ledger")))
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

                {/* Convergence Connector Box (Tier 3: Conserved Value Accounting) */}
                <div className="w-full flex flex-col items-center my-2 relative">
                  <div className="w-3/4 max-w-lg h-5 border-b-2 border-l-2 border-r-2 border-stone-300 rounded-b-xl relative">
                    <div className="absolute -top-2 -left-1 text-blue-500 font-bold text-xs leading-none">
                      ▲
                    </div>
                    <div className="absolute -top-2 -right-1 text-purple-500 font-bold text-xs leading-none">
                      ▲
                    </div>
                    <div className="absolute -bottom-3 left-1/2 -translate-x-1/2 bg-white px-2.5 py-0.5 rounded-full border border-stone-200 text-[9px] font-mono font-bold text-stone-500 uppercase tracking-wider shadow-2xs">
                      {isExplain ? "Conservation Closed" : "Sum Value Convergence"}
                    </div>
                  </div>
                  <div className="w-0.5 h-5 bg-gradient-to-b from-stone-300 to-emerald-500"></div>
                  <div className="p-3.5 rounded-xl border-2 transition-all w-full sm:w-80 text-center shadow-xs bg-[#f0fdf4] border-[#86efac]">
                    <div className="text-[10px] font-bold uppercase tracking-wider text-emerald-800">
                      {isExplain ? "Total Conserved Value" : "Accounted State"}
                    </div>
                    <div className="font-extrabold text-stone-900 text-sm mt-0.5">
                      {formatINR(totalAccounted > 0 ? totalAccounted : totalInflow)} ACCOUNTED
                    </div>
                    <div className={`text-xs font-bold font-mono mt-0.5 ${remainingResidual === 0 ? "text-emerald-700" : "text-amber-700"}`}>
                      {remainingResidual === 0 ? "✓ ₹0.00 Remaining Residual" : `${formatINR(remainingResidual)} Unresolved Gap`}
                    </div>
                  </div>
                </div>

                {/* Candidate Explanation Notice & Toggle in Explain Mode */}
                {isExplain && alternativeNodes.length > 0 ? (
                  <div className="text-center pt-2 space-y-2 w-full">
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
                        ✎ Note: ShadowLedger evaluated alternative hypotheses; Cadbury Eclairs candy change is the verified winner (corroborated by physical inventory movement).
                      </p>
                    )}

                    {/* Expanded alternative hypotheses cards with reasons */}
                    {showAlternatives && (
                      <div className="space-y-2 pt-1 text-left w-full">
                        <div className="text-[11px] font-bold text-stone-700 font-sans border-b border-stone-200 pb-1 flex items-center justify-between">
                          <span>Why Candy Change Won Over Competing Hypotheses:</span>
                          <span className="text-[10px] text-purple-700 font-mono">Winner: 90% Evidence Score</span>
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                          {alternativeNodes.map((alt) => {
                            let reason = "Discarded: Evidence confidence lower than physical inventory proof.";
                            const lbl = alt.label.toLowerCase();
                            if (lbl.includes("fee") || alt.hypothesis_type === "fee_adjustment") {
                              reason = "Discarded: No processor MDR fee schedule applies to cash payments.";
                            } else if (lbl.includes("refund") || alt.hypothesis_type === "refund") {
                              reason = "Discarded: Zero customer return requests or receipt cancellations recorded.";
                            } else if (lbl.includes("credit") || alt.hypothesis_type === "store_credit") {
                              reason = "Discarded: No store credit voucher or slip was generated for customer.";
                            }
                            return (
                              <div
                                key={alt.id}
                                onClick={() => setSelectedNode(alt)}
                                className="p-3 rounded-xl border border-dashed border-stone-300 bg-white/90 text-stone-600 opacity-85 hover:opacity-100 cursor-pointer shadow-2xs space-y-1 transition"
                              >
                                <div className="flex items-center justify-between text-[10px]">
                                  <span className="font-bold uppercase text-stone-500">○ Discarded</span>
                                  <span className="font-mono font-bold">{(alt.confidence * 100).toFixed(0)}% Conf</span>
                                </div>
                                <div className="text-xs font-semibold text-stone-900">{alt.label}</div>
                                <p className="text-[10px] text-stone-500 leading-snug">{reason}</p>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  reconstructedNodes.length > 1 && (
                    <div className="text-center font-handwriting text-stone-500 text-sm pt-1">
                      ✎ Note: ShadowLedger evaluated alternative hypotheses; Cadbury Eclairs candy change is the verified selection.
                    </div>
                  )
                )}
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
                const sourceLabel = getFriendlyNodeLabel(sourceNode, isExplain);
                const targetLabel = getFriendlyNodeLabel(targetNode, isExplain);
                return (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-2 rounded-lg bg-white border border-[#e7e2d9] text-stone-700"
                  >
                    <div className="flex items-center space-x-2 truncate">
                      <span className="font-semibold text-stone-900 truncate max-w-[160px]" title={sourceLabel}>
                        {sourceLabel}
                      </span>
                      <span className="text-purple-600 font-bold">&rarr;</span>
                      <span className="font-semibold text-stone-900 truncate max-w-[160px]" title={targetLabel}>
                        {targetLabel}
                      </span>
                    </div>
                    <div className="flex items-center space-x-2 shrink-0">
                      <span className="text-[11px] text-stone-500 italic">
                        {isExplain
                          ? getExplainEdgeLabel(link.value_type, link.amount, sourceNode, targetNode)
                          : link.value_type}
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

        {/* Node Inspector Panel (Only in Investigate Mode) */}
        {!isExplain && (
          <div className="border-t lg:border-t-0 lg:border-l border-[#e7e2d9] p-5 bg-[#ffffff] text-xs flex flex-col justify-between">
            <div>
              <div className="border-b border-[#e7e2d9] pb-3 mb-4 flex items-center justify-between">
                <span className="font-bold text-stone-900 uppercase tracking-wider text-xs font-sans">
                  Node Inspector (Auditor)
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
                <div className="space-y-3.5 font-mono">
                  {/* Identifier */}
                  <div>
                    <div className="text-[10px] uppercase font-bold text-stone-400">Node Identifier</div>
                    <div className="flex items-center justify-between mt-0.5">
                      <div className="font-bold text-stone-900 truncate text-sm">
                        {selectedNode.id}
                      </div>
                      <button
                        onClick={() => handleCopy(selectedNode.id)}
                        className="text-[10px] bg-stone-100 hover:bg-stone-200 px-2 py-0.5 rounded text-stone-700 font-mono transition"
                      >
                        {copiedId ? "✓ Copied" : "Copy ID"}
                      </button>
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
                      <div className="text-stone-700 text-xs mt-0.5 bg-stone-50 p-2 rounded-lg border border-stone-200 font-sans">
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
        )}
      </div>
    </div>
  );
}
