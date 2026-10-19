"use client";

// Delning av en artikel: kopiera länken, enhetens egen delning när den finns, och de vanliga kanalerna.
// Adressen tas vid klicket ur fönstret, så samma komponent fungerar på svenska och engelska sidor.
import { useEffect, useState } from "react";

const BTN = "inline-flex items-center gap-1.5 rounded-full border border-slate-300 bg-white px-3.5 py-1.5 text-xs font-bold text-slate-600 hover:border-[#b7410e] hover:text-[#b7410e] transition-colors";

export default function ShareArticle({ title, lang = "sv" }: { title: string; lang?: "sv" | "en" }) {
  const [copied, setCopied] = useState(false);
  // navigator finns bara i webbläsaren: knappen tänds efter monteringen, så server och klient renderar lika
  const [canShare, setCanShare] = useState(false);
  useEffect(() => { setCanShare(typeof navigator !== "undefined" && "share" in navigator); }, []);
  const en = lang === "en";
  const url = () => window.location.href.split("#")[0];
  const open = (href: string) => window.open(href, "_blank", "noopener,noreferrer,width=600,height=500");

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(url());
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch { /* utan clipboard-rättighet: adressfältet finns alltid */ }
  };
  const native = async () => {
    try { await navigator.share({ title, url: url() }); } catch { /* avbruten delning är inget fel */ }
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
          onClick={() => open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(title)}&url=${encodeURIComponent(url())}`)}>
          X
        </button>
        <button type="button" className={BTN}
          onClick={() => open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url())}`)}>
          Facebook
        </button>
        <button type="button" className={BTN}
          onClick={() => open(`https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url())}`)}>
          LinkedIn
        </button>
        <a className={BTN} href={`mailto:?subject=${encodeURIComponent(title)}&body=${encodeURIComponent((en ? "Worth a read: " : "Värd att läsa: ") + title)}%0A%0A`}
          onClick={e => { (e.currentTarget as HTMLAnchorElement).href = `mailto:?subject=${encodeURIComponent(title)}&body=${encodeURIComponent((en ? "Worth a read: " : "Värd att läsa: ") + title + "\n\n" + url())}`; }}>
          {en ? "Email" : "E-post"}
        </a>
      </div>
    </div>
  );
}
