"use client";

import React, { useState } from "react";
import { formatINR } from "../lib/utils";

interface GraphNode {
  id: string;
  label: string;
  node_type: string;
  amount: number;
  confidence: number;
  is_source_truth: boolean;
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
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [viewMode, setViewMode] = useState<"shadow" | "official">("shadow");

  if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
    return (
      <div className="p-8 text-center text-xs font-mono text-slate-500 bg-slate-950/40 rounded-xl border border-slate-800/80">
        No graph representation available for this case.
      </div>
    );
  }

  // Filter nodes for Official vs Shadow view
  const visibleNodes = viewMode === "official"
    ? graphData.nodes.filter((n) => n.is_source_truth || n.node_type === "observed")
    : graphData.nodes;

  const visibleNodeIds = new Set(visibleNodes.map((n) => n.id));
  const visibleLinks = graphData.links.filter(
    (l) => visibleNodeIds.has(l.source) && visibleNodeIds.has(l.target)
  );

  return (
    <div className={`flex flex-col bg-slate-950/80 border border-slate-800/80 rounded-xl overflow-hidden ${className || ""}`}>
      {/* Graph Toolbar */}
      <div className="px-4 py-3 bg-slate-900/90 border-b border-slate-800/80 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center space-x-2">
          <span className="w-2.5 h-2.5 rounded-full bg-purple-400"></span>
          <span className="text-xs font-bold text-white uppercase tracking-wider font-mono">
            Value-Flow Graph Network
          </span>
          <span className="text-[10px] font-mono text-slate-400 bg-slate-800 px-2 py-0.5 rounded">
            {visibleNodes.length} Nodes &bull; {visibleLinks.length} Edges
          </span>
        </div>

        {/* View Toggle */}
        <div className="flex items-center space-x-1 bg-slate-950 p-1 rounded-lg border border-slate-800 text-[11px] font-mono">
          <button
            onClick={() => setViewMode("shadow")}
            className={`px-3 py-1 rounded transition ${
              viewMode === "shadow"
                ? "bg-purple-600/90 text-white font-bold shadow-md shadow-purple-900/40"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Reconstructed Shadow View
          </button>
          <button
            onClick={() => setViewMode("official")}
            className={`px-3 py-1 rounded transition ${
              viewMode === "official"
                ? "bg-blue-600/90 text-white font-bold shadow-md shadow-blue-900/40"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Official Facts Only
          </button>
        </div>
      </div>

      {/* Main Graph Canvas Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 min-h-[340px]">
        {/* Node Layout View */}
        <div className="lg:col-span-2 p-6 flex flex-col justify-center space-y-6 relative overflow-hidden bg-gradient-to-b from-slate-950 to-slate-900/40">
          {viewMode === "official" && (
            <div className="mb-2 p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-300 text-[11px] font-mono flex items-center space-x-2">
              <span className="font-bold">⚠️ Ledger Fact View:</span>
              <span>Inferred latent nodes hidden. Notice the disconnected value-flow and unclosed residual shortfall.</span>
            </div>
          )}

          {/* Render Nodes in Directed Flow Sequence */}
          <div className="flex flex-wrap items-center justify-center gap-4 py-4">
            {visibleNodes.map((node) => {
              const isSelected = selectedNode?.id === node.id;
              const isLatent = node.node_type === "inferred_latent";
              const isDeviation = node.node_type === "unobserved_deviation";
              const isInventory = node.node_type === "inventory_asset";
              const isDerived = node.node_type === "derived";

              let badgeStyle = "bg-blue-950/40 border-blue-600/50 text-blue-300";
              if (isLatent) badgeStyle = "bg-purple-950/50 border-purple-500 text-purple-200 border-dashed animate-pulse";
              if (isDeviation) badgeStyle = "bg-amber-950/50 border-amber-500 text-amber-200 border-dashed";
              if (isInventory) badgeStyle = "bg-emerald-950/50 border-emerald-500 text-emerald-200";
              if (isDerived) badgeStyle = "bg-cyan-950/50 border-cyan-500 text-cyan-200";

              return (
                <div
                  key={node.id}
                  onClick={() => setSelectedNode(node)}
                  className={`cursor-pointer p-4 rounded-xl border transition-all transform duration-200 min-w-[160px] max-w-[220px] shadow-lg ${badgeStyle} ${
                    isSelected ? "ring-2 ring-white scale-105" : "hover:scale-102"
                  }`}
                >
                  <div className="flex items-center justify-between text-[10px] font-mono uppercase mb-1">
                    <span className="font-bold tracking-wider">{node.node_type.replace("_", " ")}</span>
                    <span className="opacity-80">{(node.confidence * 100).toFixed(0)}%</span>
                  </div>
                  <div className="text-xs font-bold text-white truncate font-mono mt-1">
                    {node.label.split(":")[0]}
                  </div>
                  <div className="text-sm font-extrabold mt-2 font-mono text-emerald-400">
                    {formatINR(node.amount)}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Links / Value Conservation Edges */}
          <div className="mt-4 pt-4 border-t border-slate-800/60">
            <div className="text-[10px] font-mono uppercase text-slate-500 tracking-wider mb-2">
              Value Conservation Flow Edges
            </div>
            <div className="space-y-1.5 max-h-28 overflow-y-auto pr-2">
              {visibleLinks.map((link, idx) => (
                <div key={idx} className="flex items-center justify-between text-xs font-mono text-slate-300 bg-slate-900/60 px-3 py-1.5 rounded border border-slate-800/60">
                  <div className="flex items-center space-x-2 truncate">
                    <span className="text-slate-400 truncate max-w-[100px]">{link.source}</span>
                    <span className="text-purple-400">&rarr;</span>
                    <span className="text-slate-400 truncate max-w-[100px]">{link.target}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-[10px] text-slate-500 uppercase">{link.value_type}</span>
                    <span className="text-emerald-400 font-bold">{formatINR(link.amount)}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Node Inspector Panel */}
        <div className="border-t lg:border-t-0 lg:border-l border-slate-800/80 p-5 bg-slate-950/90 font-mono text-xs flex flex-col justify-between">
          <div>
            <div className="text-xs font-bold text-white uppercase tracking-wider border-b border-slate-800/80 pb-2 mb-3 flex items-center justify-between">
              <span>Node Inspector</span>
              {selectedNode && (
                <button
                  onClick={() => setSelectedNode(null)}
                  className="text-[10px] text-slate-500 hover:text-white"
                >
                  Clear
                </button>
              )}
            </div>

            {selectedNode ? (
              <div className="space-y-3">
                <div>
                  <div className="text-[10px] uppercase text-slate-500">Node Identifier</div>
                  <div className="text-white font-bold truncate mt-0.5">{selectedNode.id}</div>
                </div>
                <div>
                  <div className="text-[10px] uppercase text-slate-500">Taxonomy Tier</div>
                  <div className="text-purple-300 uppercase font-bold mt-0.5">{selectedNode.node_type}</div>
                </div>
                <div>
                  <div className="text-[10px] uppercase text-slate-500">Economic Value</div>
                  <div className="text-emerald-400 font-bold text-sm mt-0.5">{formatINR(selectedNode.amount)}</div>
                </div>
                <div>
                  <div className="text-[10px] uppercase text-slate-500">Evidence Confidence</div>
                  <div className="text-white mt-0.5">{(selectedNode.confidence * 100).toFixed(1)}%</div>
                </div>
                <div>
                  <div className="text-[10px] uppercase text-slate-500">Source Truth Status</div>
                  <div className="mt-0.5">
                    {selectedNode.is_source_truth ? (
                      <span className="text-blue-400">Observed Official Source Record</span>
                    ) : (
                      <span className="text-purple-400">Inferred Latent Economic Event</span>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="py-12 text-center text-slate-500 text-[11px]">
                Click any node in the value-flow graph above to inspect its provenance, source facts, and evidence linkage.
              </div>
            )}
          </div>

          <div className="pt-4 border-t border-slate-800/80 text-[10px] text-slate-500">
            Directed NetworkX Graph &bull; Case-Local Conservation
          </div>
        </div>
      </div>
    </div>
  );
}
