"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { PUBLIC_SITE, SITE_PROJECT, STATS_OFF_KEY, siteCollection } from "@/lib/site";

// Visitor statistics for the public website, seen only by the founder in Admin (components/SiteStats.tsx): one count
// per page viewed, and which of the start page's sections were scrolled to. Written straight to Firestore (the rules
// in firestore.rules allow exactly these fields and nothing else), with no cookie, no identifier and no IP address:
// the page, the site the visitor came from, the time zone and language (an approximate country) and the kind of
// device. A browser that has opened the site once with ?inte-rakna is left out from then on; ?rakna counts it again.
const URL_ = siteCollection("site_views");

const str = (v: string, max: number) => ({ stringValue: v.slice(0, max) });

const counted = () => {
  try { return localStorage.getItem(STATS_OFF_KEY) !== "1"; } catch { return true; }
};

// Pages as the visitor sees them, without the trailing slash of the static export (/artiklar/x/ and /artiklar/x are one)
const normal = (path: string) => (path.length > 1 ? path.replace(/\/+$/, "") : path) || "/";

function send(kind: "view" | "section", path: string, extra: Record<string, unknown>) {
  const w = window.innerWidth;
  const fields = {
    kind: str(kind, 10),
    path: str(path, 200),
    day: str(new Date().toISOString().slice(0, 10), 10),
    tz: str(Intl.DateTimeFormat().resolvedOptions().timeZone || "", 60),
    lang: str(navigator.language || "", 12),
    device: str(w < 640 ? "mobil" : w < 1024 ? "surfplatta" : "dator", 12),
    ...extra,
  };
  fetch(URL_, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ fields }), keepalive: true })
    .catch(() => { /* a lost count is not worth an error */ });
}

// The first page of a visit: the referring site is known only then (later pages are opened inside the site)
let firstPage = true;

export default function SiteTracker() {
  const pathname = usePathname();
  const [notice, setNotice] = useState<string | null>(null);
  const active = PUBLIC_SITE && !!SITE_PROJECT;

  // ?inte-rakna / ?rakna: the founder's switch, remembered in this browser; removed from the address afterwards
  useEffect(() => {
    if (!active) return;
    const q = new URLSearchParams(window.location.search);
    const off = q.has("inte-rakna"), on = q.has("rakna");
    if (!off && !on) return;
    try {
      if (off) localStorage.setItem(STATS_OFF_KEY, "1"); else localStorage.removeItem(STATS_OFF_KEY);
    } catch { /* storage blocked: nothing to remember */ }
    q.delete("inte-rakna"); q.delete("rakna");
    window.history.replaceState(null, "", window.location.pathname + (q.size ? `?${q}` : "") + window.location.hash);
    // A message about the switch the founder just used, shown once
    setNotice(off ? "Den här webbläsaren räknas inte längre i besöksstatistiken." : "Den här webbläsaren räknas igen i besöksstatistiken."); // eslint-disable-line react-hooks/set-state-in-effect
    const t = setTimeout(() => setNotice(null), 6000);
    return () => clearTimeout(t);
  }, [active]);

  // One count per page, and the sections of the page that pass the middle of the screen (once each)
  useEffect(() => {
    if (!active) return;
    const host = window.location.hostname;
    if (host === "localhost" || host === "127.0.0.1" || navigator.webdriver || !counted()) return;
    const path = normal(pathname || "/");
    let ref = "";
    let entry = false;
    if (firstPage) {
      firstPage = false;
      try { ref = document.referrer ? new URL(document.referrer).hostname : ""; } catch { ref = ""; }
      entry = ref !== host;
      if (ref === host) ref = "";
    }
    send("view", path, { entry: { booleanValue: entry }, ref: str(ref.replace(/^www\./, ""), 100) });

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

  if (!notice) return null;
  return (
    <div role="status" translate="no"
      className="fixed bottom-4 left-1/2 -translate-x-1/2 z-[60] max-w-[calc(100%-2rem)] rounded-xl bg-slate-900 px-4 py-3 text-sm text-white shadow-lg">
      {notice}
    </div>
  );
}
