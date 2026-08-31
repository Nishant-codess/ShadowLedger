import type { Metadata } from "next";
import Link from "next/link";
import "../styles/globals.css";

export const metadata: Metadata = {
  title: "ShadowLedger — AI Finance Controller",
  description: "Uncertainty-aware value-flow reconstruction engine for finance operations",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#090d16] text-slate-100 min-h-screen flex flex-col antialiased selection:bg-emerald-500 selection:text-black">
        {/* Top Navigation Bar */}
        <header className="border-b border-slate-800/80 bg-[#0f172a]/90 backdrop-blur sticky top-0 z-50 px-6 py-3.5 flex items-center justify-between">
          <div className="flex items-center space-x-6">
            <Link href="/" className="flex items-center space-x-2.5">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center font-bold text-black text-lg shadow-lg shadow-emerald-500/20">
                S
              </div>
              <div>
                <span className="font-bold text-base tracking-tight text-white">ShadowLedger</span>
                <span className="ml-2 text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  Track 04
                </span>
              </div>
            </Link>

            <nav className="hidden md:flex items-center space-x-1 text-sm font-medium text-slate-400">
              <Link href="/" className="px-3 py-1.5 rounded-md hover:text-white hover:bg-slate-800/60 transition">
                Command Center
              </Link>
              <Link href="/exceptions" className="px-3 py-1.5 rounded-md hover:text-white hover:bg-slate-800/60 transition">
                Exception Queue
              </Link>
            </nav>
          </div>

          <div className="flex items-center space-x-4 text-xs font-mono">
            <div className="flex items-center space-x-2 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-full text-slate-400">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span>FastAPI :8000</span>
              <span className="text-slate-600">|</span>
              <span>DuckDB Embedded</span>
            </div>
          </div>
        </header>

        {/* Main Content Area */}
        <main className="flex-1 max-w-7xl w-full mx-auto p-6 md:p-8">
          {children}
        </main>

        {/* Footer */}
        <footer className="border-t border-slate-800/60 bg-[#090d16] px-6 py-4 text-center text-xs text-slate-500 font-mono">
          ShadowLedger &bull; Razorpay AI Buildathon Track 04 &bull; Deterministic Core &amp; Value-Flow Reconstruction
        </footer>
      </body>
    </html>
  );
}
