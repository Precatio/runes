"use client";

// Ristarna, en i taget: varje känd ristares fingeravtryck mot samtida grannstenar, stenarna från kärna till ytterkant,
// och de stenar utan ristare som attribueringsmodellen tror är ristarens. Samma komponent i appen (/ristare, datan från
// GET /api/r/ristare) och på webbplatsen (/ristarna/, web/public/ristarna/ristare.json ur webbplatsens export). Datan
// byggs av korpusjobbet (src/carver_pages.py), ritningen av lib/ristare/draw.js. Ristaren står i adressen (#balle …).
// Stilarna: app/ristarna/ristare.css, som sidorna importerar.
import { useCallback, useEffect, useRef, useState } from "react";
import { preparePage, renderCarver, slug } from "@/lib/ristare/draw";

type Variant = { n: Record<string, number>; profil: string };
type Carver = { name: string; variants: Record<string, Variant> };
type Page = { carvers: Carver[]; audit: unknown };

export default function Ristare({ src }: { src: string }) {
  const [page, setPage] = useState<Page | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [c, setC] = useState(0);
  const [v, setV] = useState("med");
  const root = useRef<HTMLDivElement>(null);
  const state = useRef<{ allSuggestions?: boolean }>({});

  useEffect(() => {
    fetch(src)
      .then(r => { if (!r.ok) throw new Error(String(r.status)); return r.json(); })
      .then((p: Page) => {
        preparePage(p);
        const i = p.carvers.findIndex(x => "#" + slug(x.name) === window.location.hash);
        setC(i >= 0 ? i : 0);
        setPage(p);
      })
      .catch(e => setError(`Ristarsidan kunde inte läsas (${e.message}). I appen byggs den av korpusanalyserna under Statistik.`));
  }, [src]);

  const go = useCallback((i: number) => {
    if (!page) return;
    const n = page.carvers.length, k = (i + n) % n;
    state.current = {};
    setC(k); setV("med");
    window.history.replaceState(null, "", "#" + slug(page.carvers[k].name));
  }, [page]);

  useEffect(() => {
    const onHash = () => {
      if (!page) return;
      const i = page.carvers.findIndex(x => "#" + slug(x.name) === window.location.hash);
      if (i >= 0) { state.current = {}; setC(i); setV("med"); }
    };
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, [page]);

  // Ritar om vid byte av ristare/variant och när fönstret ändrar bredd (figurerna tar bredden från sina paneler)
  useEffect(() => {
    if (!page || !root.current) return;
    const draw = () => root.current && renderCarver(root.current, page, page.audit, c, v, setV, state.current);
    draw();
    let t: ReturnType<typeof setTimeout> | undefined;
    const onResize = () => { clearTimeout(t); t = setTimeout(draw, 150); };
    window.addEventListener("resize", onResize);
    return () => { window.removeEventListener("resize", onResize); clearTimeout(t); };
  }, [page, c, v]);

  const panel = "liquid-glass-island rounded-[32px] p-6 md:p-7 min-w-0";
  const h2 = "text-2xl font-serif font-bold tracking-tight text-slate-900 mb-2";

  return (
    <div ref={root} className="rp-root max-w-6xl mx-auto px-4 md:px-6 pt-8 pb-24">
      <div className="liquid-glass-pill rounded-[24px] px-4 py-3 flex flex-wrap items-center gap-3 sticky top-2 z-30">
        <label htmlFor="rp-pick" className="text-xs font-bold uppercase tracking-[0.2em] text-[#b7410e]">Ristare</label>
        <select id="rp-pick" className="rp-pick liquid-glass-input-wrapper" value={c} onChange={e => go(+e.target.value)} disabled={!page}>
          {(page?.carvers ?? []).map((x, i) => {
            const m = x.variants.med, n = (m.n["signerad"] || 0) + (m.n["attribuerad"] || 0);
            return <option key={x.name} value={i}>{x.name} · {n} stenar{m.profil === "signerade" ? "" : " · profil av attribuerade"}</option>;
          })}
        </select>
        <button type="button" className="rp-btn glass-btn-3d" onClick={() => go(c - 1)} disabled={!page}>← Föregående</button>
        <button type="button" className="rp-btn glass-btn-3d" onClick={() => go(c + 1)} disabled={!page}>Nästa →</button>
        {page && <span className="text-sm text-slate-500 tabular-nums">{c + 1} av {page.carvers.length}</span>}
      </div>

      <div className="mt-8">
        <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#b7410e]">Ristarna, en i taget</div>
        <h1 id="rp-h1" className="mt-3 text-4xl md:text-5xl font-serif font-bold tracking-tight text-slate-900">{page ? "" : "Ristarna"}</h1>
        <p id="rp-lede" className="mt-4 text-lg text-slate-600 leading-relaxed max-w-[72ch]">{error ?? (page ? "" : "Läser in …")}</p>
        <div id="rp-warn" />
        <div id="rp-facts" className="rp-facts" />
        <div id="rp-variants" className="rp-variants" role="group" aria-label="Vilka stenar profilen byggs av" />
      </div>

      <div className="grid gap-6 mt-8">
        <section className={panel} style={{ borderColor: "rgba(183,65,14,0.25)" }}>
          <h2 id="rp-sg-h" className={h2} />
          <p id="rp-sg-note" className="rp-note" />
          <div id="rp-sg" />
          <div id="rp-bygd" className="rp-bygd" hidden />
        </section>

        <section className={panel}>
          <h2 className={h2}>Fingeravtrycket</h2>
          <p id="rp-fp-note" className="rp-note" />
          <div className="rp-scroll"><svg id="rp-fp" role="img" aria-label="Andel per drag hos ristaren och hos grannarna" /></div>
        </section>

        <section className={panel}>
          <h2 className={h2}>Sten för sten</h2>
          <p className="rp-note">Varje rad är en sten, varje kolumn ett av fingeravtryckets drag. <b>Rost</b> betyder att stenen gör som
            ristaren, <b>grått</b> att den gör som grannarna, <b>tomt</b> att draget inte går att avläsa (kort eller skadad text).
            Stenarna står i ordning efter hur väl de följer profilen; stapeln längst till höger visar värdet och klassen.</p>
          <div id="rp-hm-legend" className="rp-legend" />
          <div className="rp-scroll"><svg id="rp-hm" role="img" aria-label="Heatmap: stenar mot drag" /></div>
        </section>

        <section className={panel}>
          <h2 className={h2}>Kärna, spann och ytterkant</h2>
          <p className="rp-note">Varje prick är en sten, placerad efter hur väl den följer profilen. Gränserna sätts av stenarna själva:
            <b> kärnan</b> börjar vid den mittersta stenen i profilen; <b>inom spannet</b> är en sten som liknar ristaren mer än nio av
            tio grannstenar gör; <b>ytterkanten</b> ligger inom profilstenarnas spridning men går inte att skilja från grannarna;
            <b> som grannarna</b> är en sten som följer profilen sämre än nio av tio profilstenar. Stenarna i profilen mäts med sig
            själva utelämnade.</p>
          <div className="rp-scroll"><svg id="rp-dots" role="img" aria-label="Värde per sten i grupper" /></div>
        </section>

        <div className="rp-two">
          <section className={panel}>
            <h2 className={h2}>Var stenarna står</h2>
            <p id="rp-map-note" className="rp-note" />
            <div className="rp-scroll"><svg id="rp-map" role="img" aria-label="Karta över ristarens stenar" /></div>
            <p className="mt-2 text-xs text-slate-500">Karta: Vitki, efter Rundata och Vitkis gränser för de gamla landen.</p>
          </section>
          <section className={panel}>
            <h2 className={h2}>Profilen mot attribueringsmodellen</h2>
            <p className="rp-note">Vågrätt: hur väl stenen följer profilen här. Lodrätt: hur sannolikt Vitkis attribueringsmodell tycker
              att stenen är ristarens när den inte fått se stenen (korsvaliderad). Modellen väger också in plats, stil och runpar, så
              de två mätningarna är inte oberoende.</p>
            <p id="rp-audit" className="rp-note mt-2" />
            <div className="rp-scroll"><svg id="rp-sc" role="img" aria-label="Profilvärde mot modellens sannolikhet" /></div>
          </section>
        </div>

        <section className={panel}>
          <h2 className={h2}>Vilka stenar liknar varandra?</h2>
          <p className="rp-note">Andelen av fingeravtryckets drag där två av ristarens stenar gör samma sak (bland dragen som går att
            avläsa på båda). Stenarna är ordnade så att de som liknar varandra hamnar bredvid varandra; mörka block är grupper av
            stenar som skrevs på samma sätt.</p>
          <div id="rp-sim-legend" className="rp-legend" />
          <div className="rp-scroll"><svg id="rp-sim" role="img" aria-label="Likhet mellan ristarens stenar" /></div>
        </section>

        <div className="rp-two">
          <section className={panel}>
            <h2 className={h2}>Ytterkanten och utanför</h2>
            <div id="rp-edge" />
          </section>
          <section className={panel}>
            <h2 id="rp-nb-h" className={h2} />
            <p className="rp-note">Stenar inom 30 km som inte tillskrivs ristaren men följer profilen bäst. Inget förslag om att han
              ristade dem – bara de stenar som borde granskas först.</p>
            <div id="rp-nb" />
          </section>
        </div>

        <section className={panel}>
          <h2 className={h2}>Så är det gjort, och vad det inte säger</h2>
          <ul id="rp-method" className="rp-method" />
          <p className="mt-3 text-xs text-slate-500">Diagram: Vitki, efter Rundata. Kod: r/carver_profile.R, r/attribution_audit.R,
            r/attribution_candidates.R, utdata/ristare/sida_data.py.</p>
        </section>
      </div>
      <div className="rp-tip" hidden />
    </div>
  );
}
