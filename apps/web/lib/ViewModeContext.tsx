"use client";

import React, { createContext, useContext, useEffect, useState } from "react";

export type ViewMode = "explain" | "investigate";

interface ViewModeContextType {
  viewMode: ViewMode;
  setViewMode: (mode: ViewMode) => void;
  toggleViewMode: () => void;
  isExplain: boolean;
  isInvestigate: boolean;
}

const ViewModeContext = createContext<ViewModeContextType | undefined>(undefined);

export function ViewModeProvider({ children }: { children: React.ReactNode }) {
  const [viewMode, setViewModeState] = useState<ViewMode>("explain");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const saved = sessionStorage.getItem("shadowledger_view_mode");
    if (saved === "explain" || saved === "investigate") {
      setViewModeState(saved);
    }
  }, []);

  const setViewMode = (mode: ViewMode) => {
    setViewModeState(mode);
    if (typeof window !== "undefined") {
      sessionStorage.setItem("shadowledger_view_mode", mode);
    }
  };

  const toggleViewMode = () => {
    const next = viewMode === "explain" ? "investigate" : "explain";
    setViewMode(next);
  };

  return (
    <ViewModeContext.Provider
      value={{
        viewMode: mounted ? viewMode : "explain",
        setViewMode,
        toggleViewMode,
        isExplain: (mounted ? viewMode : "explain") === "explain",
        isInvestigate: (mounted ? viewMode : "explain") === "investigate",
      }}
    >
      {children}
    </ViewModeContext.Provider>
  );
}

export function useViewMode() {
  const context = useContext(ViewModeContext);
  if (!context) {
    throw new Error("useViewMode must be used within a ViewModeProvider");
  }
  return context;
}
