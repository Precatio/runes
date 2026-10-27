import { DocsNote } from "@/components/KnownLimitations";
import { Details, Tip, asList } from "@/components/Explain";
import { GLOSSARY } from "@/lib/glossary";
import ExportTable from "@/components/ExportTable";
import PlotlyGraph from "@/components/PlotlyGraph";
import type { Corpus } from "./typer";
import { Fig, Method, SHAPE, SectionIntro, Spark, Th, d2, pc, qText } from "./gemensamt";
import { sectionOf } from "./oversikt";

export function Clusters({ data }: { data: Corpus }) {
  const c = data.clusters, f = data.figure_urls.clusters || {};
  return (
    <>
      <SectionIntro section={sectionOf(data, "clusters")} patterns={data.patterns} />
      <p className="text-sm text-slate-600">
        {c.n_stones} stenar med tillräckligt många drag ingår. Strukturen är {c.structure} (<Tip text={GLOSSARY["silhuettbredd"]}>silhuettbredd</Tip>{" "}
        {d2(c.best_silhouette)}), och grupperna sammanfaller inte med ristarna (<Tip text={GLOSSARY["justerat Rand-index"]}>justerat Rand-index</Tip> {d2(c.carvers.ari)}).
      </p>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Fig src={f.mca} alt="MCA" /><Fig src={f.variables} alt="Kategorier i MCA" />
        <Fig src={f.silhouette} alt="Silhuettbredd" /><Fig src={f.carvers} alt="Ristare per grupp" />
      </div>
      <Details title="Grupperna och vad som utmärker dem" open>
        <div className="overflow-x-auto">
          <ExportTable><table className="w-full text-sm">
            <thead><tr><Th>Grupp</Th><Th>Stenar</Th><Th>Stabilitet</Th><Th>Utmärks av</Th><Th>Stilgrupper</Th><Th>Landskap</Th></tr></thead>
            <tbody>{c.clusters.map(k => (
              <tr key={k.cluster} className="border-t border-slate-900/5 align-top">
                <td className="p-2 font-semibold">{k.cluster}</td><td className="p-2">{k.n}</td><td className="p-2">{d2(k.stability)}</td>
                <td className="p-2 text-xs">{k.features.slice(0, 4).map(x => `${x.level} (${pc(x.share_in_cluster)} mot ${pc(x.share_overall)})`).join("; ")}</td>
                <td className="p-2 text-xs">{k.styles.map(x => `${x.style} ${x.n}`).join(", ")}</td>
                <td className="p-2 text-xs">{k.provinces.map(x => `${x.province} ${x.n}`).join(", ")}</td>
              </tr>))}</tbody>
          </table></ExportTable>
        </div>
      </Details>
      <Method text={c.method} />
    </>
  );
}

export function TextTab({ data }: { data: Corpus }) {
  const t = data.text, dl = data.dialect, ft = data.figure_urls.text || {}, fd = data.figure_urls.dialect || {};
  return (
    <>
      <SectionIntro section={sectionOf(data, "text")} patterns={data.patterns} />
      <h4 className="font-semibold text-slate-900">Ristarnas stavning och formler</h4>
      <p className="text-sm text-slate-600">
        Hur tydligt formlerna skiljer ristarna åt (<Tip text={GLOSSARY["Cramérs V"]}>Cramérs V</Tip>, 0–1):{" "}
        {t.formulas.tests.map(x => `${x.label.toLowerCase()} ${d2(x.cramers_v)}`).join(", ")}.
      </p>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4"><Fig src={ft.formulas} alt="Formler per ristare" /><Fig src={ft.lemmas} alt="Stavning per ord" /></div>
      <h4 className="font-semibold text-slate-900 pt-2">Stavning och dialekter</h4>
      <p className="text-sm text-slate-600">
        Stavningsavstånd mot geografiskt avstånd mellan {dl.n_districts} härader: <Tip text={GLOSSARY["Mantel r"]}>Mantel r</Tip>{" "}
        {d2(dl.mantel.r)}, <Tip text={GLOSSARY["p"]}>p</Tip> {d2(dl.mantel.p, 3)}.
      </p>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Fig src={fd.distance} alt="Stavning mot avstånd" /><Fig src={fd.groups} alt="Härader med likartad stavning" />
        <Fig src={fd.efter} alt="Stavning av efter" /><Fig src={fd.sten} alt="Diftongen i sten" />
      </div>
      <Details title="Typiska stavningar i häradsgrupperna">
        <ul className="text-sm space-y-1">
          {dl.group_forms.map(g => (
            <li key={g.group}><strong>Grupp {g.group}</strong> ({dl.groups.find(x => x.group === g.group)?.provinces}):{" "}
              {g.forms.map(x => `${x.lemma} = ${x.form} (${pc(x.share_in_group)} mot ${pc(x.share_all)})`).join("; ")}</li>
          ))}
        </ul>
      </Details>
      <Method text={t.method} />
      <Method text={dl.method} caveat={dl.caveat} />
    </>
  );
}

export function Chronology({ data }: { data: Corpus }) {
  const ch = data.chronology, f = data.figure_urls.chronology || {}, v = ch.validation;
  return (
    <>
      <SectionIntro section={sectionOf(data, "chronology")} patterns={data.patterns} />
      <p className="text-sm text-slate-600">
        Seriationen ordnar stenarna efter vilka språkdrag, formler och innehåll de delar (<Tip text={GLOSSARY["rho"]}>rho</Tip> mot stilgrupperna{" "}
        {d2(v.rho)}; {d2(v.partial_rho)} när hänsyn tas till hur nordligt stenarna står). Medelfel för ett årtal {v.mae_loo_years} år, mot {v.mae_naive_years} år utan modell.
      </p>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Fig src={f.validation} alt="Seriation mot Gräslund" /><Fig src={f.diagram} alt="Seriationsdiagram" /><Fig src={f.estimates} alt="Skattad tid" />
      </div>
      <Details title="Vad skiljer stenarna åt i hela landet?">
        <p className="text-sm text-slate-600">
          Korrespondensanalysens tre huvudriktningar för hela korpusen och vad var och en följer – tid, geografi eller ristare. Gult är ett mönster
          som inget av dem förklarar.
        </p>
        <div className="overflow-x-auto">
          <ExportTable><table className="w-full text-sm">
            <thead><tr><Th>Dimension</Th><Th>Inerti</Th><Th>Tid (rho)</Th><Th>Latitud (rho)</Th>
              <Th>Landskap (eta²)</Th><Th>Ristare (eta²)</Th><Th>Förklaras av</Th><Th>Skiljer</Th></tr></thead>
            <tbody>{ch.corpus_dimensions.map(x => (
              <tr key={x.dim} className={`border-t border-slate-900/5 align-top ${x.unexplained ? "bg-amber-50" : ""}`}>
                <td className="p-2 font-semibold">{x.dim}</td><td className="p-2">{d2(x.inertia_pct, 1)} %</td><td className="p-2">{d2(x.rho_time)}</td>
                <td className="p-2">{d2(x.rho_lat)}</td><td className="p-2">{d2(x.eta2_province)}</td><td className="p-2">{d2(x.eta2_carver)}</td>
                <td className="p-2 text-xs font-semibold">{x.unexplained ? "oförklarat mönster" : asList(x.explained_by).join(", ")}</td>
                <td className="p-2 text-xs">{asList(x.positive).slice(0, 3).join(", ")} ↔ {asList(x.negative).slice(0, 3).join(", ")}</td>
              </tr>))}</tbody>
          </table></ExportTable>
        </div>
      </Details>
      <Method text={ch.method} />
    </>
  );
}

export function Network({ data }: { data: Corpus }) {
  const n = data.network, f = data.figure_urls.network || {};
  return (
    <>
      <SectionIntro section={sectionOf(data, "network")} patterns={data.patterns} />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4"><Fig src={f.network} alt="Formelnätverk" /><Fig src={f.kinship} alt="Släktrelationer" /></div>
      <Details title="Orden i varje formelgrupp" open>
        <ul className="text-sm space-y-1">
          {n.communities.map(c => <li key={c.community}><strong>Grupp {c.community}</strong> ({c.size} ord): <span translate="no">{c.words.map(w => w.word).join(", ")}</span></li>)}
        </ul>
      </Details>
      <Details title="Släktrelationer över tid och i kristna inskrifter">
        <div className="overflow-x-auto">
          <ExportTable><table className="w-full text-sm">
            <thead><tr><Th>Relation</Th><Th>Inskrifter</Th><Th>Före ca 1050</Th><Th>Efter ca 1050</Th>
              <Th>q (tid)</Th><Th>Kristna</Th><Th>Övriga</Th><Th>q (kristen)</Th></tr></thead>
            <tbody>{n.kinship.map(k => (
              <tr key={k.relation} className={`border-t border-slate-900/5 ${k.q_period < 0.05 || k.q_christian < 0.05 ? "bg-amber-50" : ""}`}>
                <td className="p-2 font-semibold">{k.relation}</td><td className="p-2">{k.n}</td><td className="p-2">{pc(k.early)}</td><td className="p-2">{pc(k.late)}</td>
                <td className="p-2">{d2(k.q_period, 3)}</td><td className="p-2">{pc(k.share_christian)}</td><td className="p-2">{pc(k.share_other)}</td><td className="p-2">{d2(k.q_christian, 3)}</td>
              </tr>))}</tbody>
          </table></ExportTable>
        </div>
        <p className="text-xs text-slate-500">Gult: signifikant skillnad (q under 0,05) över tid eller mellan kristna och övriga inskrifter.</p>
      </Details>
      <Method text={n.method} />
    </>
  );
}

export function Words({ data }: { data: Corpus }) {
  const w = data.words;
  if (!w) return <p className="text-sm text-slate-600">Ordförrådsanalysen saknas i den här beräkningen; beräkna korpusanalyserna på nytt.</p>;
  const epochs = w.time[0]?.shares.map(s => s.epoch) ?? [];
  const holds = w.region.filter(r => r.holds);
  return (
    <>
      <SectionIntro section={sectionOf(data, "words")} patterns={data.patterns} />
      <p className="text-sm text-slate-600 max-w-3xl">
        De vanligaste orden på de vikingatida runstenarna (Rundatas normalisering, namnen borträknade), här prövade: är ordet vanligare i ett landskap än i resten av landet när tiden och textlängden räknats
        bort, och ändras det över tid? Ristaren räknas som slumpeffekt, så en flitig ristares vanor inte blir
        landskapets.
      </p>
      <Details title={`Orden som skiljer landskapen åt (${holds.length} håller i båda sockenhalvorna)`} open>
        <div className="overflow-x-auto">
          <ExportTable><table className="w-full text-sm">
            <thead><tr><Th>Ord</Th><Th>Landskap</Th><Th>Andel där</Th><Th>Andel i övriga</Th><Th>q</Th><Th>Håller i halvorna</Th></tr></thead>
            <tbody>{w.region.map(r => (
              <tr key={`${r.word}|${r.province}`} className={`border-t border-slate-900/5 ${r.holds ? "bg-amber-50" : ""}`}>
                <td className="p-2 font-semibold" translate="no">{r.word}</td>
                <td className="p-2">{r.province}</td>
                <td className="p-2">{pc(r.rate_in)} ({r.k_in} av {r.n_in})</td>
                <td className="p-2">{pc(r.rate_out)}</td>
                <td className="p-2">{qText(r.q)}</td>
                <td className="p-2">{r.holds ? "✓" : "–"}</td>
              </tr>))}</tbody>
          </table></ExportTable>
        </div>
        <p className="text-xs text-slate-500 mt-1">
          Gult: signalen har samma riktning och p under 0,05 i båda sockenhalvorna. Riktningen (vanligare eller
          ovanligare än riket) syns i andelarna; q är det tidsjusterade testets justerade p-värde över alla {w.n_region_tests} prov.
        </p>
      </Details>
      <Details title={`Orden som ändras över tid (${w.time.length} av ${w.n_time_tests})`}>
        <div className="overflow-x-auto">
          <ExportTable><table className="w-full text-sm">
            <thead><tr><Th>Ord</Th><Th>Riktning</Th><Th>q</Th>{epochs.map(e => <Th key={e}>{e}</Th>)}</tr></thead>
            <tbody>{w.time.map(t => (
              <tr key={t.word} className="border-t border-slate-900/5">
                <td className="p-2 font-semibold" translate="no">{t.word}</td>
                <td className="p-2">{t.slope > 0 ? "ökar" : "minskar"}</td>
                <td className="p-2">{qText(t.q)}</td>
                {t.shares.map(s => <td key={s.epoch} className="p-2">{s.n ? pc(s.k / s.n) : "–"}</td>)}
              </tr>))}</tbody>
          </table></ExportTable>
        </div>
        <p className="text-xs text-slate-500 mt-1">
          Andelen stenar med ordet per epok (tiden ur stilgrupperna, därför ungefär 980–1130). Riktningen kommer ur
          modellens tidslutning, justerad för landskap och textlängd.
        </p>
      </Details>
      <Details title="Vilka landskap väljer ord mest lika? (korrespondensanalys)" open>
        <div className="h-[420px]">
          <PlotlyGraph
            data={[
              { type: "scatter", mode: "text", x: w.ca.words.map(x => x.x), y: w.ca.words.map(x => x.y),
                text: w.ca.words.map(x => x.w), name: "Ord", textfont: { size: 10, color: "#94a3b8" },
                hovertemplate: "%{text}<extra>ord</extra>" },
              { type: "scatter", mode: "markers+text", x: w.ca.provinces.map(x => x.x), y: w.ca.provinces.map(x => x.y),
                text: w.ca.provinces.map(x => x.code), name: "Landskap", textposition: "top center",
                marker: { color: "#b7410e", size: 10, line: { color: "#ffffff", width: 1 } },
                textfont: { size: 12, color: "#1f2937" },
                hovertemplate: "%{text}: %{customdata} stenar<extra>landskap</extra>",
                customdata: w.ca.provinces.map(x => x.n) },
            ]}
            layout={{
              autosize: true, margin: { l: 40, r: 10, t: 10, b: 40 },
              xaxis: { title: `Dimension 1 (${Math.round(100 * (w.ca.inertia[0] ?? 0))} % av variationen)`, zeroline: true, zerolinecolor: "rgba(15,23,42,0.1)" },
              yaxis: { title: `Dimension 2 (${Math.round(100 * (w.ca.inertia[1] ?? 0))} %)`, zeroline: true, zerolinecolor: "rgba(15,23,42,0.1)" },
              legend: { orientation: "h" }, paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
            }}
          />
        </div>
        <p className="text-xs text-slate-500">
          Landskap som står nära varandra har liknande ordprofiler; orden (grå) drar mot de landskap där de är
          vanligast. Mest lika ordval: {w.neighbors.map(n => `${n.a}–${n.b}`).join(", ")}.
        </p>
      </Details>
      <Method text={w.method} />
    </>
  );
}

export function Change({ data }: { data: Corpus }) {
  const c = data.change, f = data.figure_urls.change || {};
  if (!c) return <p className="text-sm text-slate-600">Förändringsanalysen saknas i den här beräkningen; beräkna korpusanalyserna på nytt.</p>;
  const crossing = c.features.filter(x => (x.provinces?.rows || []).filter(r => r.cross_year).length >= 2);
  return (
    <>
      <SectionIntro section={sectionOf(data, "change")} patterns={data.patterns} />
      <div className="rounded-2xl bg-white border border-slate-200 p-4">
        <h4 className="font-semibold text-slate-900">Varje drag över tid</h4>
        <p className="text-xs text-slate-500 mb-3">
          Linjen är andelen stenar med draget från omkring år 1000 till 1115, med plats och ristare konstanta (samma skala 0–100 % på varje rad).
          Gulmarkerade rader är signifikanta (<Tip text={GLOSSARY["q"]}>q</Tip> under 0,05). Tiden kommer från stilgrupperna ({c.n_dated} daterade stenar),
          och varje resultat är omräknat {c.draws} gånger med årtal inom stilgruppens intervall.
        </p>
        <div className="overflow-x-auto">
          <ExportTable><table className="w-full text-sm">
            <thead><tr><Th>Drag</Th><Th>Förlopp</Th><Th>Justerad andel</Th><Th>q</Th><Th>Omräkningar signifikanta</Th>
              <Th>Vanligast i</Th><Th>Ovanligast i</Th><Th>Daterade stenar</Th></tr></thead>
            <tbody>{c.features.map(x => {
              const t = x.time, sig = t.q != null && t.q < 0.05;
              return (
                <tr key={x.key} className={`border-t border-slate-900/5 ${sig ? "bg-amber-50" : ""}`}>
                  <td className="p-2 font-semibold">{x.label}</td>
                  <td className="p-2 text-xs">
                    <div className="flex items-center gap-2">
                      <Spark curve={t.curve} />
                      <span>{t.tested ? `${SHAPE[t.shape ?? ""] ?? ""}${t.peak_year ? ` ${t.peak_year}` : ""}` : "för få daterade stenar"}</span>
                    </div>
                  </td>
                  <td className="p-2 text-xs whitespace-nowrap">{t.tested ? `${pc(t.first)} → ${pc(t.last)}` : "–"}</td>
                  <td className="p-2">{qText(t.q)}</td>
                  <td className="p-2 text-xs">{t.draws?.n ? pc(t.draws.share_sig) : "–"}</td>
                  <td className="p-2 text-xs">{x.space && x.space.p < 0.05 ? asList(x.space.high).join(", ") : "–"}</td>
                  <td className="p-2 text-xs">{x.space && x.space.p < 0.05 ? asList(x.space.low).join(", ") : "–"}</td>
                  <td className="p-2 text-xs">{t.n}</td>
                </tr>
              );
            })}</tbody>
          </table></ExportTable>
        </div>
      </div>
      <Fig src={f.time} alt="Dragen över tid" />
      <Fig src={f.map} alt="Var dragen är vanligast" />
      <Fig src={f.provinces} alt="Landskapen omkring 1050" />
      {crossing.length > 0 && (
        <Details title="När draget blir vanligt i olika landskap" open>
          <p className="text-sm text-slate-600">Året då draget finns på hälften av stenarna, med 95 % intervall. Ett tidigare år kan betyda att förändringen började där.</p>
          <ul className="text-sm space-y-1">
            {crossing.map(x => (
              <li key={x.key}><strong>{x.label}</strong>{" "}
                (skillnad mellan landskapen i mittperioden <Tip text={GLOSSARY["q"] ?? GLOSSARY["p"]}>q</Tip> {qText(x.provinces!.q_differ ?? x.provinces!.p_differ)}, justerat för alla drag):{" "}
                {x.provinces!.rows.filter(r => r.cross_year).sort((a, b) => a.cross_year! - b.cross_year!)
                  .map(r => `${r.province} omkring ${r.cross_year} (${r.cross_lo}–${r.cross_hi})`).join(", ")}
              </li>
            ))}
          </ul>
        </Details>
      )}
      <Details title="Bro- och vägstenar och kristna drag">
        <p className="text-sm text-slate-600">Prövar tolkningen av brobyggen som kristna själagåvor: har bro- och vägstenar oftare kristna drag än andra stenar?</p>
        <div className="overflow-x-auto">
          <ExportTable><table className="w-full text-sm">
            <thead><tr><Th>Drag</Th><Th>Brostenar</Th><Th>Andra stenar</Th>
              <Th>Oddskvot (95 % KI)</Th><Th>q</Th><Th>Daterade, med tid</Th></tr></thead>
            <tbody>{c.assoc.map(a => (
              <tr key={a.key} className={`border-t border-slate-900/5 ${a.all?.q != null && a.all.q < 0.05 ? "bg-amber-50" : ""}`}>
                <td className="p-2 font-semibold">{a.label}</td><td className="p-2">{pc(a.share_x)} av {a.n_x}</td>
                <td className="p-2">{pc(a.share_other)}</td>
                <td className="p-2">{a.all ? `${d2(a.all.or)} (${d2(a.all.lo)}–${d2(a.all.hi)})` : "–"}</td>
                <td className="p-2">{qText(a.all?.q)}</td>
                <td className="p-2 text-xs">{a.dated?.or != null ? `${d2(a.dated.or)} (${d2(a.dated.lo)}–${d2(a.dated.hi)}), p ${qText(a.dated.p)}` : "–"}</td>
              </tr>))}</tbody>
          </table></ExportTable>
        </div>
      </Details>
      <DocsNote anchor="1h-förändring-i-tid-och-rum">Hur förändringsanalysen ska läsas och vilka reservationer som gäller står i avsnitt 1h.</DocsNote>
      <Method text={c.method} />
    </>
  );
}
