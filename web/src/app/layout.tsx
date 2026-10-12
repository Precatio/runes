import type { Metadata } from "next";
import { KEYWORDS, SITE_DESCRIPTION, SITE_NAME, SITE_URL } from "@/lib/site";
import Script from "next/script";
import "./globals.css";
import { LanguageProvider } from "@/components/LanguageContext";
import { ThemeProvider } from "@/components/ThemeContext";
import { SettingsProvider } from "@/components/SettingsContext";
import { AnalysisProvider } from "@/components/AnalysisContext";
import { AuthProvider } from "@/components/AuthContext";
import LoadingBar from "@/components/LoadingBar";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: { default: "Vitki – runstenar och runinskrifter: öppen forskningsplattform", template: "%s | Vitki" },
  description: SITE_DESCRIPTION,
  keywords: KEYWORDS,
  applicationName: SITE_NAME,
  authors: [{ name: "Viktor Kvant" }],
  creator: "Viktor Kvant",
  category: "research",
  openGraph: { type: "website", locale: "sv_SE", siteName: SITE_NAME, url: "/", title: "Vitki – runstenar och runinskrifter",
               description: SITE_DESCRIPTION },
  twitter: { card: "summary_large_image", title: "Vitki – runstenar och runinskrifter", description: SITE_DESCRIPTION },
  robots: { index: true, follow: true },
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
        <LoadingBar />
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
