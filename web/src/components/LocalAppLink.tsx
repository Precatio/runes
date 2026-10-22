import Link from "next/link";
import { SHOW_LOCAL_APP } from "@/lib/site";

// The way into the app from the start page and the articles while it runs on this computer (next dev or next start). The public
// website has no app, and there the link is not rendered at all.
export default function LocalAppLink({ className = "fixed bottom-4 right-4 z-50 inline shadow-lg bg-white" }: { className?: string }) {
  if (!SHOW_LOCAL_APP) return null;
  return (
    <Link href="/start" title="Syns bara när appen körs lokalt, aldrig på den publika webbplatsen"
      className={`${className} px-3 py-1 rounded-full border border-dashed border-slate-400 text-xs font-bold text-slate-600 hover:border-slate-900 hover:text-slate-900`}>
      Appen (lokalt)
    </Link>
  );
}
