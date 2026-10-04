import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import { LanguageProvider } from "@/components/LanguageContext";
import { ThemeProvider } from "@/components/ThemeContext";
import { SettingsProvider } from "@/components/SettingsContext";
import { AnalysisProvider } from "@/components/AnalysisContext";
import TopBar from "@/components/TopBar";
import AIChatWidget from "@/components/AIChatWidget";
import { AuthProvider } from "@/components/AuthContext";

export const metadata: Metadata = {
  title: "Vitki AI",
  description: "AI-driven verktyg för Runologer",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="sv">
      <body className="flex h-screen overflow-hidden antialiased selection:bg-black/10 selection:text-black">
        <AuthProvider>
          <SettingsProvider>
            <ThemeProvider>
              <LanguageProvider>
                <AnalysisProvider>
                  {/* Floating Left Dock / Navigation */}
                  <Sidebar />

                  {/* Floating Main Content Pane (Liquid Glass Island) */}
                  <main className="flex-1 flex flex-col h-[calc(100vh-2rem)] m-4 rounded-[32px] liquid-glass relative z-10 overflow-hidden shadow-2xl transition-all duration-300">
                    <TopBar />
                    <div className="flex-1 overflow-y-auto p-6 md:p-8">
                      {children}
                    </div>
                  </main>

                  {/* Global AI Chat Overlay */}
                  <AIChatWidget />
                </AnalysisProvider>
              </LanguageProvider>
            </ThemeProvider>
          </SettingsProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
