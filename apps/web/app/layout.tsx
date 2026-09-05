import type { Metadata } from "next";
import { Plus_Jakarta_Sans, Caveat, JetBrains_Mono } from "next/font/google";
import "../styles/globals.css";
import { ViewModeProvider } from "../lib/ViewModeContext";
import { ThemeProvider } from "../lib/ThemeContext";
import { AppHeader } from "../components/AppHeader";
import { AICopilotDrawer } from "../components/AICopilotDrawer";

const sansFont = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const handwritingFont = Caveat({
  subsets: ["latin"],
  variable: "--font-handwriting",
  display: "swap",
});

const monoFont = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "ShadowLedger — Intelligent Financial Investigation Notebook",
  description: "Uncertainty-aware value-flow reconstruction engine for finance operations",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${sansFont.variable} ${handwritingFont.variable} ${monoFont.variable}`}
    >
      <body className="bg-[#faf8f5] text-stone-900 min-h-screen flex flex-col antialiased selection:bg-emerald-200 selection:text-emerald-950 font-sans notebook-grid">
        <ThemeProvider>
          <ViewModeProvider>
            {/* Top Navigation Bar */}
            <AppHeader />

            {/* Main Content Area */}
            <main className="flex-1 max-w-7xl w-full mx-auto p-5 sm:p-7 md:p-8">
              {children}
            </main>

            {/* Floating AI Copilot Drawer */}
            <AICopilotDrawer />

            {/* Notebook Style Footer */}
            <footer className="border-t border-[#e7e2d9] bg-[#ffffff]/80 backdrop-blur px-6 py-4 text-center text-xs text-stone-500 font-sans flex flex-col sm:flex-row items-center justify-between gap-2 max-w-7xl w-full mx-auto">
              <div className="flex items-center space-x-2">
                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                <span className="font-semibold text-stone-700">ShadowLedger Notebook</span>
                <span className="text-stone-300">&bull;</span>
                <span>Deterministic Core &amp; Value-Flow Reconstruction</span>
              </div>
              <div className="text-[11px] text-stone-400 font-mono">
                Razorpay AI Buildathon Track 04 &bull; Offline Local-First
              </div>
            </footer>
          </ViewModeProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
