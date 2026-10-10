import Sidebar from "@/components/Sidebar";
import TopBar from "@/components/TopBar";
import AIChatWidget from "@/components/AIChatWidget";
import RouteLimitations from "@/components/KnownLimitations";

// Layout for the application itself (everything except the public landing page)
export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen overflow-hidden">
      {/* Floating Left Dock / Navigation */}
      <Sidebar />

      {/* Floating Main Content Pane (Liquid Glass Island) */}
      <main className="flex-1 flex flex-col h-[calc(100vh-2rem)] m-4 rounded-[32px] liquid-glass relative z-10 overflow-hidden shadow-2xl transition-all duration-300">
        <TopBar />
        <div className="flex-1 overflow-y-auto p-6 md:p-8">
          {children}
          <RouteLimitations />
        </div>
      </main>

      {/* Global AI Chat Overlay */}
      <AIChatWidget />
    </div>
  );
}
