"use client";

// Delning av en artikel: kopiera länken, enhetens egen delning när den finns, och de vanliga kanalerna.
// Adressen tas vid klicket ur fönstret, så samma komponent fungerar på svenska och engelska sidor. Den delade adressen
// märks med kanalen (?via=x), så att besöksstatistiken kan visa vilken delning som gav besök; märket läses vid
// ankomsten och tas bort ur adressfältet (components/SiteTracker.tsx). Själva klicket räknas också (lib/track.ts).
import { useState, useSyncExternalStore } from "react";
import { trackClick, type ShareChannel } from "@/lib/track";

const BTN = "inline-flex items-center gap-1.5 rounded-full border border-slate-300 bg-white px-3.5 py-1.5 text-xs font-bold text-slate-600 hover:border-[#b7410e] hover:text-[#b7410e] transition-colors";

export default function ShareArticle({ title, lang = "sv" }: { title: string; lang?: "sv" | "en" }) {
  const [copied, setCopied] = useState(false);
  // navigator finns bara i webbläsaren: servern renderar utan knappen, klienten läser av den efter monteringen
  const canShare = useSyncExternalStore(() => () => {}, () => typeof navigator !== "undefined" && "share" in navigator, () => false);
  const en = lang === "en";
  // Adressen utan fragment, märkt med kanalen
  const url = (via: ShareChannel) => {
    const u = new URL(window.location.href);
    u.hash = "";
    u.searchParams.set("via", via);
    return u.toString();
  };
  const open = (channel: ShareChannel, href: string) => {
    trackClick(`dela:${channel}`);
    window.open(href, "_blank", "noopener,noreferrer,width=600,height=500");
  };

  const copy = async () => {
    trackClick("dela:lank");
    try {
      await navigator.clipboard.writeText(url("lank"));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch { /* utan clipboard-rättighet: adressfältet finns alltid */ }
  };
  const native = async () => {
    trackClick("dela:enhet");
    try { await navigator.share({ title, url: url("enhet") }); } catch { /* avbruten delning är inget fel */ }
  };

  return (
    <div className="mt-10 pt-6 border-t border-slate-200">
      <div className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2.5">{en ? "Share this article" : "Dela artikeln"}</div>
      <div className="flex flex-wrap gap-2">
        <button type="button" onClick={copy} className={BTN}>
          {copied ? (en ? "Copied!" : "Kopierad!") : (en ? "Copy link" : "Kopiera länk")}
        </button>
        {canShare && (
          <button type="button" onClick={native} className={BTN}>{en ? "Share …" : "Dela …"}</button>
        )}
        <button type="button" className={BTN}
          onClick={() => open("x", `https://twitter.com/intent/tweet?text=${encodeURIComponent(title)}&url=${encodeURIComponent(url("x"))}`)}>
          X
        </button>
        <button type="button" className={BTN}
          onClick={() => open("facebook", `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url("facebook"))}`)}>
          Facebook
        </button>
        <button type="button" className={BTN}
          onClick={() => open("linkedin", `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url("linkedin"))}`)}>
          LinkedIn
        </button>
        <a className={BTN} href={`mailto:?subject=${encodeURIComponent(title)}&body=${encodeURIComponent((en ? "Worth a read: " : "Värd att läsa: ") + title)}%0A%0A`}
          onClick={e => {
            trackClick("dela:epost");
            (e.currentTarget as HTMLAnchorElement).href = `mailto:?subject=${encodeURIComponent(title)}&body=${encodeURIComponent((en ? "Worth a read: " : "Värd att läsa: ") + title + "\n\n" + url("epost"))}`;
          }}>
          {en ? "Email" : "E-post"}
        </a>
      </div>
    </div>
  );
}
