"use client";

import React, { createContext, useContext, useState, useEffect } from "react";

type Theme = "blue" | "sage" | "graphite";

interface ThemeContextType {
  theme: Theme;
  setTheme: (theme: Theme) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>("blue");

  useEffect(() => {
    // Read from localStorage on mount
    const saved = localStorage.getItem("theme") as Theme | null;
    if (saved && ["blue", "sage", "graphite"].includes(saved)) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setTheme(saved);
    }
  }, []);

  useEffect(() => {
    // Apply theme to document
    if (theme === "blue") {
      document.documentElement.removeAttribute("data-theme");
    } else {
      document.documentElement.setAttribute("data-theme", theme);
    }
    localStorage.setItem("theme", theme);
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
}
