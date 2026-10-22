"use client";

import type { ReactNode } from "react";
import { AuthProvider } from "@/components/AuthContext";
import { SettingsProvider } from "@/components/SettingsContext";
import { AnalysisProvider } from "@/components/AnalysisContext";

// Sign-in, settings and the analysis state belong to the app. The public website has none of them, and the condition is
// written out (not PUBLIC_SITE from lib/site) so that the build drops the providers' code from the website's bundle
export default function AppProviders({ children }: { children: ReactNode }) {
  if (process.env.NEXT_PUBLIC_SITE_MODE === "public") return <>{children}</>;
  return (
    <AuthProvider>
      <SettingsProvider>
        {children}
      </SettingsProvider>
    </AuthProvider>
  );
}

export function AnalysisState({ children }: { children: ReactNode }) {
  if (process.env.NEXT_PUBLIC_SITE_MODE === "public") return <>{children}</>;
  return <AnalysisProvider>{children}</AnalysisProvider>;
}
