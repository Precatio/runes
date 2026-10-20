"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { PUBLIC_SITE, SITE_PROJECT, STATS_OFF_KEY } from "@/lib/site";
import { counting, entryVia, normal, send, str, trackClick } from "@/lib/track";

// Visitor statistics for the public website, seen only by the founder in Admin (components/SiteStats.tsx): one count
// per page viewed, which of the start page's sections were scrolled to, the page a visitor came from inside the site,
// the share channel named in a shared link, and clicks on outbound and language links. Written straight to Firestore
// (lib/track.ts; the rules in firestore.rules allow exactly these fields and nothing else), with no cookie, no
// identifier and no IP address: the page, the site the visitor came from, the time zone and language (an approximate
// country) and the kind of device. A browser that has opened the site once with ?inte-rakna is left out from then on;
// ?rakna counts it again.

// The first page of a visit: the referring site is known only then (later pages are opened inside the site)
let firstPage = true;
// The page viewed before this one in the same visit, kept in memory only (a reload or a new tab starts over)
let lastPath: string | null = null;

export default function SiteTracker() {
  const pathname = usePathname();
  const [notice, setNotice] = useState<string | null>(null);
  const active = PUBLIC_SITE && !!SITE_PROJECT;

  // ?inte-rakna / ?rakna: the founder's switch, remembered in this browser; removed from the address afterwards.
  // ?via= (the share channel of a shared link) is read once at load (lib/track.ts) and removed too, so that a copied
  // address is not mistaken for the original share.
  useEffect(() => {
    if (!active) return;
    const q = new URLSearchParams(window.location.search);
    const off = q.has("inte-rakna"), on = q.has("rakna");
    if (!off && !on && !q.has("via")) return;
    q.delete("inte-rakna"); q.delete("rakna"); q.delete("via");
    window.history.replaceState(null, "", window.location.pathname + (q.size ? `?${q}` : "") + window.location.hash);
    if (!off && !on) return;
    try {
      if (off) localStorage.setItem(STATS_OFF_KEY, "1"); else localStorage.removeItem(STATS_OFF_KEY);
    } catch { /* storage blocked: nothing to remember */ }
    // A message about the switch the founder just used, shown once
    setNotice(off ? "Den här webbläsaren räknas inte längre i besöksstatistiken." : "Den här webbläsaren räknas igen i besöksstatistiken."); // eslint-disable-line react-hooks/set-state-in-effect
    const t = setTimeout(() => setNotice(null), 6000);
    return () => clearTimeout(t);
  }, [active]);

  // One count per page, and the sections of the page that pass the middle of the screen (once each)
  useEffect(() => {
    if (!active || !counting()) return;
    const host = window.location.hostname;
    const path = normal(pathname || "/");
    let ref = "";
    let entry = false;
    const prev = firstPage || lastPath === path ? null : lastPath;
    let via: string | null = null;
    if (firstPage) {
      firstPage = false;
      try { ref = document.referrer ? new URL(document.referrer).hostname : ""; } catch { ref = ""; }
      entry = ref !== host;
      if (ref === host) ref = "";
      via = entry ? entryVia : null;
    }
    lastPath = path;
    send("view", path, {
      entry: { booleanValue: entry }, ref: str(ref.replace(/^www\./, ""), 100),
      ...(prev ? { prev: str(prev, 200) } : {}), ...(via ? { via: str(via, 20) } : {}),
    });

    const seen = new Set<string>();
    const watch = new IntersectionObserver(items => {
      for (const it of items) {
        const id = (it.target as HTMLElement).id;
        if (it.isIntersecting && id && !seen.has(id)) {
          seen.add(id);
          send("section", path, { section: str(id, 40) });
        }
      }
    }, { rootMargin: "-45% 0px -45% 0px" });
    document.querySelectorAll("section[id]").forEach(el => watch.observe(el));
    return () => watch.disconnect();
  }, [active, pathname]);

  // Clicks on links that leave the site (ut:webbplats) and on the links between the Swedish and English versions
  // (sprak:en / sprak:sv); only the kind of link is counted, never the visitor or the full address
  useEffect(() => {
    if (!active) return;
    const onClick = (e: MouseEvent) => {
      const a = (e.target as Element | null)?.closest?.("a[href]") as HTMLAnchorElement | null;
      if (!a) return;
      if (a.hreflang === "en" || a.hreflang === "sv") { trackClick(`sprak:${a.hreflang}`); return; }
      if (a.protocol !== "http:" && a.protocol !== "https:") return;
      if (a.host !== window.location.host) trackClick(`ut:${a.hostname.replace(/^www\./, "")}`);
    };
    document.addEventListener("click", onClick);
    return () => document.removeEventListener("click", onClick);
  }, [active]);

  if (!notice) return null;
  return (
    <div role="status" translate="no"
      className="fixed bottom-4 left-1/2 -translate-x-1/2 z-[60] max-w-[calc(100%-2rem)] rounded-xl bg-slate-900 px-4 py-3 text-sm text-white shadow-lg">
      {notice}
    </div>
  );
}
