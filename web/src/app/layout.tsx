import type { Metadata } from "next";
import { KEYWORDS, SITE_DESCRIPTION, SITE_NAME, SITE_URL } from "@/lib/site";
import Script from "next/script";
import { Noto_Sans_Runic } from "next/font/google";
import "./globals.css";
import { LanguageProvider } from "@/components/LanguageContext";
import { ThemeProvider } from "@/components/ThemeContext";
import { SettingsProvider } from "@/components/SettingsContext";
import { AnalysisProvider } from "@/components/AnalysisContext";
import { AuthProvider } from "@/components/AuthContext";
import LoadingBar from "@/components/LoadingBar";
import SiteTracker from "@/components/SiteTracker";

// The runes themselves (ᛦ, ᚦ …) in one typeface on every device: last in the text's and the headings' font lists
// (globals.css), so that it is used only for the runic characters; bundled with the site when it is built
const runic = Noto_Sans_Runic({ weight: "400", subsets: ["runic"], display: "swap", variable: "--font-runic" });

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
               images: [{ url: "/delningsbild.png", width: 1200, height: 630, alt: "Vitki – öppen forskningsplattform för runstenar och runinskrifter" }],
               description: SITE_DESCRIPTION },
  twitter: { card: "summary_large_image", title: "Vitki – runstenar och runinskrifter", description: SITE_DESCRIPTION, images: ["/delningsbild.png"] },
  robots: { index: true, follow: true },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="sv" suppressHydrationWarning className={runic.variable}>
      <head>
        {/* English chosen earlier: keep the page hidden until it is translated (public/lang-init.js) */}
        <Script id="vitki-lang" src="/lang-init.js" strategy="beforeInteractive" />
      </head>
      <body className="antialiased selection:bg-black/10 selection:text-black">
        <LoadingBar />
        <SiteTracker />
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
