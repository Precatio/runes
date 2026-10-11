import AppShell from "@/components/AppShell";
import AIChatWidget from "@/components/AIChatWidget";
import RouteLimitations from "@/components/KnownLimitations";

// Layout for the application itself (everything except the public landing page)
export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <AppShell>
        {children}
        <RouteLimitations />
      </AppShell>

      {/* Global AI Chat Overlay */}
      <AIChatWidget />
    </>
  );
}
