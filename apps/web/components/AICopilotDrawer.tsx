"use client";

import React, { useState, useEffect, useRef } from "react";
import { usePathname } from "next/navigation";
import { chatCopilot, ChatCopilotResponse } from "../lib/api";
import { useTheme } from "../lib/ThemeContext";

interface Message {
  role: "user" | "assistant";
  content: string;
  provider?: string;
}

export function AICopilotDrawer({ caseId }: { caseId?: string }) {
  const pathname = usePathname();
  const { theme, setTheme } = useTheme();
  const [isOpen, setIsOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const pathCaseId = pathname.startsWith("/cases/") ? pathname.split("/")[2] : undefined;
  const activeCaseId = caseId || pathCaseId;

  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Hello! Ask me anything about how cases are resolved, why certain payments require human review, or what patterns exist across the fleet.",
      provider: "system",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  // Dynamic suggested questions based on route & case context
  let suggestedQuestions = [
    "Why did this case resolve?",
    "What is the missing ₹2 in Kirana?",
    "What is the ride fare discrepancy?",
    "What are Fleet Patterns?",
  ];

  if (activeCaseId) {
    suggestedQuestions = [
      "What is this case about?",
      "Why did this case resolve or get held?",
      "Show factual evidence breakdown",
      "What was the policy gate decision?",
    ];
  } else if (pathname.startsWith("/exceptions")) {
    suggestedQuestions = [
      "Why do off-ledger deviations require human review?",
      "What is the auto-resolution policy gate?",
      "How is evidence confidence scored?",
      "What cases are currently held in queue?",
    ];
  } else if (pathname.startsWith("/patterns")) {
    suggestedQuestions = [
      "What are the recurring fleet patterns?",
      "How is total value at risk calculated?",
      "What causes the cab UPI QR surcharge pattern?",
      "How do patterns compress 1,000 exceptions?",
    ];
  }

  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isOpen]);

  async function handleSend(textToSend?: string) {
    const query = textToSend || input;
    if (!query.trim() || loading) return;

    const userMsg: Message = { role: "user", content: query };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res: ChatCopilotResponse | null = await chatCopilot(query, activeCaseId);
      if (res) {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: res.response,
            provider: res.provider,
          },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: "I am having trouble reaching the local AI service. The deterministic reconciliation engine remains fully operational.",
            provider: "offline_fallback",
          },
        ]);
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Encountered an error communicating with the copilot. Please try again.",
          provider: "error",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      {/* Floating Theme Switcher Pill (Placed directly above the AI Copilot Launcher) */}
      <div className="fixed bottom-[68px] right-5 z-40 flex items-center bg-white/95 backdrop-blur border border-[#e7e2d9] rounded-2xl p-1 shadow-lg text-xs space-x-1 font-sans">
        <span className="text-xs pl-1.5 pr-0.5 text-stone-400" title="Theme Selector">🎨</span>
        <button
          onClick={() => setTheme("pastel")}
          className={`px-2.5 py-1 rounded-xl text-[11px] font-semibold transition ${
            theme === "pastel"
              ? "bg-amber-100 text-amber-900 font-bold border border-amber-300 shadow-2xs"
              : "text-stone-600 hover:text-stone-900 hover:bg-stone-100"
          }`}
          title="Pastel Financial Investigation Notebook"
        >
          Pastel
        </button>
        <button
          onClick={() => setTheme("midnight")}
          className={`px-2.5 py-1 rounded-xl text-[11px] font-semibold transition ${
            theme === "midnight"
              ? "bg-stone-900 text-white font-bold border border-stone-700 shadow-2xs"
              : "text-stone-600 hover:text-stone-900 hover:bg-stone-100"
          }`}
          title="Midnight Fintech Dark Theme"
        >
          Dark
        </button>
        <button
          onClick={() => setTheme("nordic")}
          className={`px-2.5 py-1 rounded-xl text-[11px] font-semibold transition ${
            theme === "nordic"
              ? "bg-slate-200 text-slate-900 font-bold border border-slate-300 shadow-2xs"
              : "text-stone-600 hover:text-stone-900 hover:bg-stone-100"
          }`}
          title="Nordic Clean Theme"
        >
          Nordic
        </button>
      </div>

      {/* Floating Launcher Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-5 right-5 z-40 px-4 py-3 bg-stone-900 hover:bg-stone-800 text-white rounded-2xl shadow-xl flex items-center space-x-2 border border-stone-700 transition hover:scale-105"
      >
        <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
        <span className="text-xs font-bold font-sans tracking-wide">
          {isOpen ? "✕ Close Copilot" : "✨ Ask ShadowLedger AI Copilot"}
        </span>
      </button>

      {/* Non-Blocking Floating Chat Window */}
      {isOpen && (
        <div
          className="fixed bottom-[118px] right-5 z-50 w-96 max-w-[calc(100vw-2.5rem)] h-[530px] max-h-[calc(100vh-8.5rem)] bg-white border border-[#e7e2d9] rounded-2xl shadow-2xl flex flex-col justify-between overflow-hidden animate-in slide-in-from-bottom-4 duration-200"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="p-3.5 bg-[#faf8f5] border-b border-[#e7e2d9] flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-7 h-7 rounded-xl bg-purple-100 border border-purple-200 flex items-center justify-center text-sm">
                ✨
              </div>
              <div>
                <div className="flex items-center space-x-1.5">
                  <h3 className="text-xs font-bold text-stone-900 font-sans">
                    ShadowLedger AI Copilot
                  </h3>
                  {activeCaseId && (
                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-purple-100 text-purple-800 font-mono">
                      {activeCaseId.slice(0, 10)}
                    </span>
                  )}
                </div>
                <p className="text-[10px] text-stone-500 font-mono">
                  Ollama (llama3.2) &bull; Grounded Facts
                </p>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="w-7 h-7 rounded-lg hover:bg-stone-200 text-stone-500 font-mono text-xs flex items-center justify-center"
              title="Close chat box"
            >
              ✕
            </button>
          </div>

          {/* Non-authoritative notice */}
          <div className="px-3.5 py-1.5 bg-[#f0fdf4] border-b border-[#bbf7d0] text-[10px] text-[#14532d] flex items-center space-x-1.5 font-sans">
            <span>🛡️</span>
            <span>
              <strong>Non-Authoritative:</strong> Explains evidence; does not post financial outcomes.
            </span>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-3.5 space-y-3">
            {messages.map((m, idx) => (
              <div
                key={idx}
                className={`flex flex-col ${
                  m.role === "user" ? "items-end" : "items-start"
                }`}
              >
                <div
                  className={`p-3 rounded-2xl text-xs max-w-[88%] leading-relaxed whitespace-pre-line ${
                    m.role === "user"
                      ? "bg-stone-900 text-white rounded-br-xs"
                      : "bg-[#faf8f5] text-stone-800 border border-[#e7e2d9] rounded-bl-xs"
                  }`}
                >
                  {m.content}
                </div>
                {m.provider && m.provider !== "system" && (
                  <span className="text-[9px] text-stone-400 font-mono mt-1 px-1">
                    {m.provider === "local_llm_ollama"
                      ? "🦙 Ollama Local LLM"
                      : "⚡ Deterministic Core"}
                  </span>
                )}
              </div>
            ))}

            {loading && (
              <div className="flex items-start">
                <div className="p-3 rounded-2xl bg-[#faf8f5] border border-[#e7e2d9] text-xs text-stone-500 rounded-bl-xs flex items-center space-x-2">
                  <span className="w-2 h-2 rounded-full bg-purple-500 animate-bounce"></span>
                  <span>Querying local LLM...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Suggested Prompt Chips */}
          <div className="px-3 py-2 bg-stone-50 border-t border-[#e7e2d9] flex flex-wrap gap-1">
            <span className="text-[9px] font-bold text-stone-400 uppercase block w-full">
              Suggested Prompts:
            </span>
            {suggestedQuestions.map((q, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(q)}
                disabled={loading}
                className="px-2 py-0.5 bg-white hover:bg-stone-100 text-stone-700 text-[10px] rounded-md border border-[#e2ddd5] transition shadow-2xs text-left"
              >
                {q}
              </button>
            ))}
          </div>

          {/* Input Footer */}
          <div className="p-2.5 bg-white border-t border-[#e7e2d9]">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
              className="flex items-center space-x-1.5"
            >
              <input
                type="text"
                placeholder="Ask about this case or reconciliation..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={loading}
                className="flex-1 bg-[#faf8f5] border border-[#e2ddd5] rounded-xl px-3 py-1.5 text-xs text-stone-900 placeholder-stone-400 focus:outline-none focus:ring-1 focus:ring-purple-500 font-sans"
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="px-3.5 py-1.5 bg-purple-600 hover:bg-purple-700 disabled:bg-stone-300 text-white rounded-xl text-xs font-bold transition shadow-xs"
              >
                Send
              </button>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
