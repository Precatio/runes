"use client";

import React, { useEffect, useMemo, useState, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { API_URL } from "@/lib/api";
import { runologyData, YOUNGER_FUTHARK, type RunologySection } from "@/lib/runologyData";
import ExportTable from "@/components/ExportTable";

interface ArchiveCarver { name: string; signed: number; attributed: number; provinces: Record<string, number>; styles: Record<string, number>; span: [number, number] | null; examples: string[] }
interface Archive {
  carvers: ArchiveCarver[];
  categories: { key: string; label: string; definition: string; base_rate: number; count: number }[];
  famous: { signum: string; name: string; place: string; carver: string | null; style: string; dating: string; translation: string }[];
  proposals: { signum: string; place: string; carver: string; strength: number }[];
  source: string;
}

// Rundata's carver names that are groups or debated identities rather than one person
const CARVER_NOTES: Record<string, string> = {
  Traen: "”Traen” är enligt Gustavson & Snædal Brink (1981) och Bianchi (2010) en felläsning, och stenarna är en grupp snarare än en ristares verk.",
};

const WRITTEN = {
  alfabet: "Runraderna",
  namn: "Runornas namn",
  magi: "Runor och magi",
  kallor: "Källor och vidare läsning",
};

const matches = (q: string, ...texts: (string | undefined | null)[]) => !q || texts.some(t => (t ?? "").toLowerCase().includes(q));

function formatMarkdown(text: string) {
  let f = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  // Only bold: a single asterisk marks reconstructed forms (*fehu), not italics
  f = f.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
  return { __html: f };
}

function Card({ title, children, keywords }: { title: React.ReactNode; children: React.ReactNode; keywords?: string[] }) {
  return (
    <div className="bg-white border border-slate-200 p-6 rounded-[24px] shadow-sm group relative overflow-hidden">
      <div className="absolute top-0 left-0 w-1.5 h-full bg-[#b7410e]/20 group-hover:bg-[#b7410e] transition-colors"></div>
      <h3 className="text-lg font-bold text-slate-900 mb-2">{title}</h3>
      <div className="text-slate-600 leading-relaxed text-sm">{children}</div>
      {keywords && keywords.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-1.5">
          {keywords.slice(0, 8).map(kw => <span key={kw} className="px-2 py-0.5 bg-slate-100 text-slate-500 text-[10px] font-bold uppercase tracking-wider rounded-md border border-slate-200">{kw}</span>)}
        </div>
      )}
    </div>
  );
}

function Section({ title, intro, children }: { title: string; intro?: React.ReactNode; children: React.ReactNode }) {
  return (
    <section className="space-y-4">
      <h2 className="text-2xl font-bold text-slate-800 font-serif border-b border-slate-200 pb-2">{title}</h2>
      {intro && <div className="text-sm text-slate-600 max-w-3xl">{intro}</div>}
      {children}
    </section>
  );
}

function KnowledgeBaseContent() {
  const searchParams = useSearchParams();
  const initialSearch = searchParams.get("search") || "";
  const [searchTerm, setSearchTerm] = useState(initialSearch);
  const [archive, setArchive] = useState<Archive | null>(null);
  const [archiveError, setArchiveError] = useState<string | null>(null);

  // Follow ?search= when the URL changes
  const [prevInitialSearch, setPrevInitialSearch] = useState(initialSearch);
  if (initialSearch !== prevInitialSearch) {
    setPrevInitialSearch(initialSearch);
    if (initialSearch) setSearchTerm(initialSearch);
  }

  useEffect(() => {
    fetch(`${API_URL}/api/research/archive`).then(r => (r.ok ? r.json() : Promise.reject(new Error(`Fel ${r.status}`))))
      .then(setArchive).catch(() => setArchiveError("Ristare, syften och kända stenar hämtas från analysmotorn, som inte svarar."));
  }, []);

  const q = searchTerm.trim().toLowerCase();
  const written = useMemo(() => runologyData.filter(item => matches(q, item.title, item.content, ...item.keywords)), [q]);
  const byCat = (cat: RunologySection["category"]) => written.filter(i => i.category === cat);
  const carvers = (archive?.carvers ?? []).filter(c => matches(q, c.name, Object.keys(c.provinces).join(" "), Object.keys(c.styles).join(" "), "ristare runristare"));
  const categories = (archive?.categories ?? []).filter(c => matches(q, c.label, c.definition, "syfte"));
  const famous = (archive?.famous ?? []).filter(f => matches(q, f.name, f.signum, f.place, f.carver, f.translation));
  const proposals = (archive?.proposals ?? []).filter(p => matches(q, p.signum, p.place, p.carver, "förslag"));
  const runeRows = YOUNGER_FUTHARK.filter(r => matches(q, r.name, r.meaning, r.translit, "runnamn runedikt"));
  const nothing = !written.length && !carvers.length && !categories.length && !famous.length && !proposals.length && !runeRows.length;

  return (
    <div className="w-full min-h-full p-8 max-w-5xl mx-auto space-y-10 animate-fade-in">
      <div className="bg-white border border-slate-200 rounded-[32px] p-8 shadow-sm relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-[#b7410e] opacity-5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/3"></div>
        <div className="relative z-10 flex flex-col items-center text-center max-w-2xl mx-auto space-y-5">
          <div>
            <h1 className="text-4xl font-black text-slate-900 tracking-tight font-serif">Runologiskt Arkiv</h1>
            <p className="text-slate-500 mt-3 text-lg leading-relaxed">
              Runraderna, runornas namn, ristarna, inskrifternas syften och kända stenar. Ristare, syften och stenar hämtas ur
              Samnordisk runtextdatabas och appens analyser, så siffrorna stämmer med resten av appen.
            </p>
          </div>
          <input type="text" value={searchTerm} onChange={e => setSearchTerm(e.target.value)}
            className="block w-full px-5 py-4 bg-slate-50 border border-slate-200 rounded-2xl focus:ring-2 focus:ring-[#b7410e] sm:text-lg shadow-sm focus:bg-white text-slate-900 placeholder:text-slate-400 outline-none"
            placeholder="Sök efter 'kortkvist', 'fé', 'Öpir', 'bro' …" />
        </div>
      </div>

      {nothing && (
        <div className="text-center py-16 bg-white border border-slate-200 border-dashed rounded-[32px]">
          <p className="text-slate-500 font-medium text-lg">Inga träffar för &rdquo;{searchTerm}&rdquo;</p>
        </div>
      )}

      {byCat("alfabet").length > 0 && (
        <Section title={WRITTEN.alfabet}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {byCat("alfabet").map(i => <Card key={i.id} title={i.title} keywords={i.keywords}><p dangerouslySetInnerHTML={formatMarkdown(i.content)} /></Card>)}
          </div>
        </Section>
      )}

      {(byCat("namn").length > 0 || runeRows.length > 0) && (
        <Section title={WRITTEN.namn}>
          {byCat("namn").map(i => <Card key={i.id} title={i.title}><p dangerouslySetInnerHTML={formatMarkdown(i.content)} /></Card>)}
          {runeRows.length > 0 && (
            <div className="overflow-x-auto bg-white border border-slate-200 rounded-[24px] p-4">
              <ExportTable><table className="w-full text-sm">
                <thead><tr className="text-left text-[11px] uppercase tracking-wider text-slate-500">
                  <th className="p-2">Runa</th><th className="p-2">Translitterering</th><th className="p-2">Namn</th><th className="p-2">Betydelse enligt runedikterna</th></tr></thead>
                <tbody>{runeRows.map(r => (
                  <tr key={r.name} className="border-t border-slate-900/5">
                    <td className="p-2 text-2xl leading-none">{r.rune}</td><td className="p-2 font-semibold">{r.translit}</td>
                    <td className="p-2 italic">{r.name}</td><td className="p-2 text-slate-600">{r.meaning}</td>
                  </tr>
                ))}</tbody>
              </table></ExportTable>
            </div>
          )}
        </Section>
      )}

      {archiveError && <p className="text-sm text-amber-800">{archiveError}</p>}

      {carvers.length > 0 && (
        <Section title="Runristarna" intro={<>
          De {archive!.carvers.length} ristare som har minst tio säkra stenar i Rundata (S = signerad, A = attribuerad i
          litteraturen). Perioden följer stilgrupperna på ristarens stenar enligt Gräslunds kronologi. Namnen är Rundatas;
          siffror efter namnet skiljer namne åt, och attribueringarna är forskares bedömningar, i Mälardalen främst
          Axelsons (1993). Hur väl appens metoder stöder dem visas i <Link href="/oversikt" className="text-[#b7410e] hover:underline">Stenöversikt</Link>.
        </>}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {carvers.map(c => (
              <Card key={c.name} title={c.name}>
                <p><strong>{c.signed}</strong> signerade och <strong>{c.attributed}</strong> attribuerade stenar
                  {Object.keys(c.provinces).length > 0 && <> · {Object.entries(c.provinces).map(([p, n]) => `${p} ${n}`).join(", ")}</>}</p>
                {Object.keys(c.styles).length > 0 && (
                  <p className="mt-1">Stilgrupper: {Object.entries(c.styles).map(([s, n]) => `${s} (${n})`).join(", ")}
                    {c.span && <> – ungefär {c.span[0]}–{c.span[1]}</>}.</p>
                )}
                {CARVER_NOTES[c.name] && <p className="mt-1 text-slate-700">{CARVER_NOTES[c.name]}</p>}
                <p className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-xs">
                  <Link href={`/inskrifter?carver=${encodeURIComponent(c.name)}`} className="text-[#b7410e] font-semibold hover:underline">Alla stenarna</Link>
                  {c.examples.slice(0, 4).map(s => <Link key={s} href={`/inskrifter?signum=${encodeURIComponent(s)}`} className="text-slate-500 hover:underline">{s}</Link>)}
                </p>
              </Card>
            ))}
          </div>
        </Section>
      )}

      {categories.length > 0 && (
        <Section title="Inskrifternas syfte" intro={<>
          Vad de {archive!.categories.reduce((n, c) => Math.max(n, Math.round(c.count / Math.max(c.base_rate, 1e-9))), 0)} vikingatida
          runstenarna med text handlar om, katalogiserat med regler på Rundatas normalisering och översättning. En inskrift kan
          höra till flera kategorier. Kategorierna per ristare och stenens storlek per syfte finns i{" "}
          <Link href="/luckor" className="text-[#b7410e] hover:underline">Forskningsluckor</Link>.
        </>}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {categories.map(c => (
              <Card key={c.key} title={<>{c.label} <span className="text-sm font-semibold text-slate-500">· {c.count} stenar ({(c.base_rate * 100).toFixed(c.base_rate < 0.01 ? 1 : 0).replace(".", ",")} %)</span></>}>
                <p>{c.definition}</p>
                <p className="mt-2 text-xs"><Link href={`/inskrifter?category=${encodeURIComponent(c.key)}`} className="text-[#b7410e] font-semibold hover:underline">Visa inskrifterna</Link></p>
              </Card>
            ))}
          </div>
        </Section>
      )}

      {(famous.length > 0 || proposals.length > 0) && (
        <Section title="Kända stenar">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {famous.map(f => (
              <Card key={f.signum} title={<>{f.name} <span className="text-sm font-semibold text-slate-500">({f.signum})</span></>}>
                <p>{f.place}. Ristare i Rundata: <strong>{f.carver ?? "ingen angiven"}</strong>. Stilgrupp {f.style || "–"}, datering {f.dating || "–"}.</p>
                {f.translation && <p className="mt-2 italic text-slate-500"><span translate="no">&rdquo;{f.translation.replace(/§[A-F] ?/g, "").slice(0, 220)}{f.translation.length > 220 ? " …" : ""}&rdquo;</span> (Rundatas översättning)</p>}
                <p className="mt-2 flex gap-3 text-xs">
                  <Link href={`/inskrifter?signum=${encodeURIComponent(f.signum)}`} className="text-[#b7410e] font-semibold hover:underline">Inskriften</Link>
                  <Link href={`/oversikt?signum=${encodeURIComponent(f.signum)}`} className="text-[#b7410e] font-semibold hover:underline">I stenöversikten</Link>
                </p>
              </Card>
            ))}
          </div>
          {proposals.length > 0 && (
            <div className="bg-white border border-slate-200 rounded-[24px] p-5">
              <h3 className="font-bold text-slate-900 mb-1">Stenar utan ristare där appens metoder pekar mot en</h3>
              <p className="text-xs text-slate-500 mb-3">Starkaste nya förslagen i Stenöversikt – hypoteser att pröva, inte attribueringar.</p>
              <ul className="grid grid-cols-1 sm:grid-cols-2 gap-1 text-sm">
                {proposals.map(p => (
                  <li key={p.signum}><Link href={`/oversikt?signum=${encodeURIComponent(p.signum)}`} className="font-semibold text-[#b7410e] hover:underline">{p.signum}</Link>
                    <span className="text-slate-500"> {p.place}</span> → {p.carver} <span className="text-slate-500">({p.strength.toFixed(2).replace(".", ",")})</span></li>
                ))}
              </ul>
            </div>
          )}
        </Section>
      )}

      {byCat("magi").length > 0 && (
        <Section title={WRITTEN.magi}>
          {byCat("magi").map(i => <Card key={i.id} title={i.title} keywords={i.keywords}><p dangerouslySetInnerHTML={formatMarkdown(i.content)} /></Card>)}
        </Section>
      )}

      {byCat("kallor").length > 0 && (
        <Section title={WRITTEN.kallor}>
          {byCat("kallor").map(i => <Card key={i.id} title={i.title}><p dangerouslySetInnerHTML={formatMarkdown(i.content)} /></Card>)}
          {archive && <p className="text-xs text-slate-500">Datadelarna: {archive.source}</p>}
        </Section>
      )}
    </div>
  );
}

export default function KnowledgeBasePage() {
  return (
    <Suspense fallback={<div className="p-8">Laddar arkivet …</div>}>
      <KnowledgeBaseContent />
    </Suspense>
  );
}
