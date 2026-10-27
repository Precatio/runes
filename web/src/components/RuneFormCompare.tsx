/* eslint-disable @next/next/no-img-element */
"use client";

// The rune crops of two stones side by side on "Jämför två stenar": for every rune both stones have, how alike the forms
// are between the stones against how alike they are within each stone. Crops come from the user's projects (by signum)
// and, for a stone from the shared corpus, from the forms shared with it.
import { useEffect, useState } from "react";
import Link from "next/link";
import { corpus, type CorpusEntry } from "@/lib/corpus";
import type { PaleographicCrop } from "@/lib/db";
import { loadAllCrops, meanLikeness } from "@/lib/runeForms";

export interface FormSide { label: string; signum: string; entry?: CorpusEntry }

const fold = (s: string) => s.toLowerCase().replace(/\s+/g, "");
const fmt = (v: number) => (Number.isFinite(v) ? v.toFixed(2).replace(".", ",") : "–");

async function cropsFor(side: FormSide): Promise<PaleographicCrop[]> {
  const own = (await loadAllCrops()).filter(c => side.signum && fold(c.signum) === fold(side.signum)).map(c => c.crop);
  if (!side.entry) return own;
  const shared = await corpus.runeForms(side.entry).catch(() => []);
  return [...own, ...shared.map(f => ({
    id: f.id, tag: f.tag, imageBase64: f.formPng ?? "", coordinates: [], featureVector: f.featureVector,
    featureVersion: f.featureVersion, formPng: f.formPng, grooveSummary: f.grooveSummary, createdAt: "",
  }))];
}

export default function RuneFormCompare({ a, b }: { a: FormSide; b: FormSide }) {
  const [crops, setCrops] = useState<{ a: PaleographicCrop[]; b: PaleographicCrop[] } | null>(null);
  useEffect(() => {
    let cancelled = false;
    Promise.all([cropsFor(a), cropsFor(b)]).then(([ca, cb]) => { if (!cancelled) setCrops({ a: ca, b: cb }); });
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- the sides are new objects on every render; their stones are what count
  }, [a.signum, a.entry?.id, b.signum, b.entry?.id]);
  if (!crops) return <p className="text-sm text-slate-500">Hämtar runutsnitten …</p>;

  const tags = [...new Set(crops.a.map(c => c.tag))].filter(t => crops.b.some(c => c.tag === t));
  const rows = tags.map(tag => {
    const A = crops.a.filter(c => c.tag === tag), B = crops.b.filter(c => c.tag === tag);
    const between = meanLikeness(A, B), inA = meanLikeness(A), inB = meanLikeness(B);
    const within = [inA, inB].filter(x => x.n > 0);
    // the stones' own variation: the mean likeness within them (pairs on the same stone)
    const ref = within.length ? within.reduce((a, x) => a + x.mean, 0) / within.length : NaN;
    const loose = within.some(x => x.mean < 0.5);
    return { tag, A, B, between, inA, inB, loose, asAlike: Number.isFinite(ref) ? between.mean >= ref - 0.02 : null };
  }).filter(r => r.between.n > 0);
  const judged = rows.filter(r => r.asAlike !== null);
  const alike = judged.filter(r => r.asAlike).length;

  if (!crops.a.length || !crops.b.length) {
    return (
      <p className="text-sm text-slate-600">
        {`Runutsnitt saknas för sten ${!crops.a.length ? a.label : b.label}.`}{" "}
        Spara runutsnitt för stenen i ett projekt med dess signum, så kan formerna jämföras här.{" "}
        <Link href="/3d?verktyg=2d" className="underline">Öppna Bilder och runformer</Link>
      </p>
    );
  }
  if (!rows.length) {
    return <p className="text-sm text-slate-600">Stenarna har inga jämförbara utsnitt av samma runa ännu.</p>;
  }
  return (
    <div className="space-y-3">
      <p className="text-sm text-slate-800">
        {judged.length
          ? `I ${alike} av ${judged.length} runor är formerna lika lika mellan stenarna som runorna på samma sten.`
          : `${rows.length} runor finns på båda stenarna, men ingen av dem har två utsnitt på samma sten att jämföra med.`}
      </p>
      <div className="divide-y divide-slate-100 bg-white rounded-xl border border-slate-200">
        {rows.map(r => (
          <div key={r.tag} className="p-3 grid grid-cols-1 md:grid-cols-[1fr_1fr_14rem] gap-3 items-center">
            {[r.A, r.B].map((cs, i) => (
              <div key={i} className="flex gap-1.5 overflow-x-auto">
                <span className={`text-[10px] font-bold mr-1 ${i ? "text-[#eb6834]" : "text-[#2a78d6]"}`}>{i ? "B" : "A"}</span>
                {cs.slice(0, 5).map(c => (
                  <div key={c.id} className="w-12 h-12 flex-shrink-0 bg-slate-50 border border-slate-200 rounded flex items-center justify-center overflow-hidden">
                    {c.imageBase64 && <img src={c.imageBase64} alt={c.tag} className="max-w-full max-h-full object-contain" />}
                  </div>
                ))}
              </div>
            ))}
            <div className="text-xs text-slate-600">
              <div className="font-bold text-slate-800">{r.tag}</div>
              <div>{`Mellan stenarna ${fmt(r.between.mean)}`}</div>
              <div>{`Inom A ${r.inA.n ? fmt(r.inA.mean) : "–"} · inom B ${r.inB.n ? fmt(r.inB.mean) : "–"}`}</div>
              {r.asAlike !== null && <div className={r.asAlike ? "text-emerald-700" : "text-slate-500"}>
                {r.asAlike ? "lika lika som på samma sten" : "mindre lika än på samma sten"}</div>}
              {r.loose && <div className="text-amber-700">Runorna på samma sten liknar inte varandra. Kontrollera att utsnitten är vridna lika.</div>}
            </div>
          </div>
        ))}
      </div>
      <p className="text-[11px] text-slate-500">
        Talen är formlikhet i medel över alla par (1 = samma form). Runorna på samma sten visar ristarens egen variation.
        Är formerna mellan stenarna lika lika som så, skiljer formen inte stenarna åt. Få utsnitt ger stor osäkerhet, och
        formlikheten är ett underlag för jämförelse, inte ett bevis för samma ristare. Vrid utsnitt ur lutande slingor så
        att runan står upprätt innan du jämför.
      </p>
    </div>
  );
}
