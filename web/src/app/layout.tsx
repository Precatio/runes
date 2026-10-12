import type { Metadata } from "next";
import Script from "next/script";
import "./globals.css";
import { LanguageProvider } from "@/components/LanguageContext";
import { ThemeProvider } from "@/components/ThemeContext";
import { SettingsProvider } from "@/components/SettingsContext";
import { AnalysisProvider } from "@/components/AnalysisContext";
import { AuthProvider } from "@/components/AuthContext";

export const metadata: Metadata = {
  title: "Vitki – öppen forskningsplattform för runinskrifter",
  description: "3D-huggspårsanalys, Rundata, ortografisk stilometri, delad mätkorpus och RTI i en öppen plattform för runologisk forskning.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="sv" suppressHydrationWarning>
      <head>
        {/* English chosen earlier: keep the page hidden until it is translated (public/lang-init.js) */}
        <Script id="vitki-lang" src="/lang-init.js" strategy="beforeInteractive" />
      </head>
      <body className="antialiased selection:bg-black/10 selection:text-black">
        <AuthProvider>
          <SettingsProvider>
            <ThemeProvider>
              <LanguageProvider>
                <AnalysisProvider>
                  {children}
                </AnalysisProvider>
              </LanguageProvider>
            </ThemeProvider>
          </SettingsProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
