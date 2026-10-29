import { DocsNote } from "@/components/KnownLimitations";
import { Details, Tip, asList } from "@/components/Explain";
import { GLOSSARY } from "@/lib/glossary";
import Link from "next/link";
import ExportTable from "@/components/ExportTable";
import type { AnonGroup, Corpus } from "./typer";
import { Fig, Method, PROVINCE_NAMES, SectionIntro, Stones, Th, d2, pc } from "./gemensamt";
import { sectionOf } from "./oversikt";

export function Attribution({ data }: { data: Corpus }) {
  const a = data.attribution, f = data.figure_urls.attribution || {};
  const all = a.ablation.find(x => x.features === "Alla");
  return (
    <>
      <SectionIntro section={sectionOf(data, "attribution")} patterns={data.patterns} />
      <div className="rounded-2xl bg-white border border-slate-200 p-5">
        <h4 className="font-semibold text-slate-900 mb-3">Hur ofta modellen väljer rätt ristare</h4>
        <div className="space-y-2">
          {[["Modellen, alla belägg", all?.accuracy], ...a.ablation.filter(x => x.features !== "Alla").map(x => [`Bara ${x.features.toLowerCase()}`, x.accuracy] as [string, number]),
            ["Gissa alltid den vanligaste ristaren", a.majority_baseline]].map(([label, v]) => (
            <div key={label as string} className="grid grid-cols-[minmax(0,220px)_1fr_48px] items-center gap-3 text-sm">
              <span className="text-slate-700 truncate">{label}</span>
              <div className="h-3 rounded-full bg-slate-100 overflow-hidden">
                <div className={`h-full rounded-full ${label === "Gissa alltid den vanligaste ristaren" ? "bg-slate-400" : "bg-[#2a78d6]"}`}
                  style={{ width: `${Math.round((v as number ?? 0) * 100)}%` }} />
              </div>
              <span className="text-right font-semibold text-slate-900">{pc(v as number)}</span>
            </div>
          ))}
        </div>
        <p className="text-xs text-slate-500 mt-3">Andel stenar med känd ristare där modellen, utan att ha sett stenen, gav rätt ristare som förstaval.</p>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Fig src={f.ablation} alt="Delmodeller" /><Fig src={f.calibration} alt="Kalibrering" />
        <Fig src={f.importance} alt="Variabler" /><Fig src={f.confusion} alt="Förväxlingar" />
      </div>
      {a.grouped_cv && (
        <Details title="Fungerar modellen på platser den inte har sett?">
          <p className="text-sm text-slate-600">
            Vid vanlig korsvalidering kan stenar från samma plats finnas både i tränings- och testdata. Här hålls hela socknar
            respektive härader utanför träningen; en ristare som bara finns i det utelämnade området kan då inte föreslås och räknas som fel.
          </p>
          <div className="overflow-x-auto">
            <ExportTable><table className="w-full text-sm">
              <thead><tr><Th>Belägg</Th><Th>Slumpvis</Th>
                {Object.entries(a.grouped_cv).map(([k, g]) => <Th key={k} tip={GLOSSARY["Ny socken/härad"]}>Ny {k.toLowerCase()} ({g.n_groups} grupper)</Th>)}</tr></thead>
              <tbody>{a.ablation.map(x => (
                <tr key={x.features} className="border-t border-slate-900/5"><td className="p-2 font-semibold">{x.features}</td><td className="p-2">{pc(x.accuracy)}</td>
                  {Object.entries(a.grouped_cv!).map(([k, g]) => <td key={k} className="p-2">{pc(g.ablation.find(y => y.features === x.features)?.accuracy ?? undefined)}</td>)}</tr>
              ))}</tbody>
            </table></ExportTable>
          </div>
        </Details>
      )}
      {a.material && a.material.per_family.length > 0 && (
        <Details title="Kommer träffen från bergarten?">
          <p className="text-sm text-slate-600">
            Ristare och bergart hänger ihop. Delmodellen <em>Bergart</em> ovan visar vad bergartsfamiljen ensam ger
            ({pc(a.ablation.find(x => x.features === "Bergart")?.accuracy)} – samma som att gissa den vanligaste ristaren, eftersom nästan alla
            stenar är granit). Här är hela modellens träff per bergartsfamilj; {a.material.n_without_family} träningsstenar saknar bergart i Rundata.
          </p>
          <div className="overflow-x-auto">
            <ExportTable><table className="w-full text-sm">
              <thead><tr><Th>Bergartsfamilj</Th><Th>Stenar</Th><Th>Ristare</Th><Th>Rätt först</Th></tr></thead>
              <tbody>{a.material.per_family.filter(x => x.n >= 5).map(x => (
                <tr key={x.family} className="border-t border-slate-900/5"><td className="p-2 font-semibold">{x.family}</td><td className="p-2">{x.n}</td><td className="p-2">{x.carvers}</td><td className="p-2">{pc(x.accuracy)}</td></tr>
              ))}</tbody>
            </table></ExportTable>
          </div>
        </Details>
      )}
      {a.open_set && <SomeoneElse a={a} />}
      <Details title="Hur säkra sannolikheterna är">
        <ul className="text-sm space-y-1 text-slate-700">
          {a.calibration.reliability.map(r => (
            <li key={r.threshold}>När modellen anger minst {Math.round(r.threshold * 100)} % sannolikhet är förstavalet rätt i <strong>{pc(r.accuracy)}</strong> av fallen ({r.n} stenar).</li>
          ))}
        </ul>
      </Details>
      <Details title="Ristarna en och en">
        <div className="overflow-x-auto">
          <ExportTable><table className="w-full text-sm">
            <thead><tr><Th>Ristare</Th><Th>Säkra stenar</Th><Th>Hittas (recall)</Th><Th>Rätt när föreslagen (precision)</Th></tr></thead>
            <tbody>{a.per_carver.map(r => (
              <tr key={r.carver} className="border-t border-slate-900/5"><td className="p-2 font-semibold">{r.carver}</td><td className="p-2">{r.n}</td>
                <td className="p-2">{pc(r.recall)}</td><td className="p-2">{pc(r.precision)}</td></tr>))}</tbody>
          </table></ExportTable>
        </div>
      </Details>
      <Method text={a.method} caveat={a.caveat} />
    </>
  );
}

// "Någon annan": the model only knows its carvers, and says so when its first choice is too weak (r/attribution.R)
function SomeoneElse({ a }: { a: Corpus["attribution"] }) {
  const o = a.open_set!;
  return (
    <div className="rounded-2xl bg-white border border-slate-200 p-5 space-y-3">
      <h4 className="font-semibold text-slate-900">Kan modellen säga &quot;kanske någon annan&quot;?</h4>
      <p className="text-sm text-slate-700 leading-relaxed">
        Modellen känner bara {a.carvers.length} ristare, och en sten av någon annan får ändå ett av deras namn. Därför säger den
        nu <strong>kanske någon annan</strong> när förstavalet får mindre än <strong>{pc(o.threshold)}</strong>. Gränsen valdes genom att
        gömma en ristare i taget: modellen tränades på de andra och fick gissa på den gömdas stenar. Då sade den &quot;kanske
        någon annan&quot; om <strong>{pc(o.left_out.flagged)}</strong> av de {o.left_out.n} stenarna – men också om {pc(o.known.flagged)} av
        de kända ristarnas stenar, där den egentligen hade svaret. Under gränsen kan modellen alltså inte skilja en ristare
        den aldrig sett från en sten den bara är osäker på.
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="rounded-xl bg-slate-50 border border-slate-200 p-3">
          <div className="text-2xl font-bold text-slate-900">{pc(o.small_carvers.flagged)}</div>
          <div className="text-xs text-slate-600">av {o.small_carvers.n} stenar av {o.small_carvers.carvers} ristare med färre än {a.min_inscriptions ?? 8} stenar
            får &quot;kanske någon annan&quot; – prövat på stenar som inte användes när gränsen valdes</div>
        </div>
        <div className="rounded-xl bg-slate-50 border border-slate-200 p-3">
          <div className="text-2xl font-bold text-slate-900">{pc(o.known.accuracy_kept)}</div>
          <div className="text-xs text-slate-600">rätt förstaval där modellen ger ett namn (mot {pc(o.known.accuracy_all)} för alla kända stenar)</div>
        </div>
        {a.n_predictions != null && a.n_someone_else != null && (
          <div className="rounded-xl bg-slate-50 border border-slate-200 p-3">
            <div className="text-2xl font-bold text-slate-900">{a.n_someone_else}</div>
            <div className="text-xs text-slate-600">av {a.n_predictions} stenar utan säker ristare får &quot;kanske någon annan&quot; i stället för ett namn</div>
          </div>
        )}
      </div>
      <p className="text-xs text-slate-500">
        &quot;Kanske någon annan&quot; betyder att stenen inte liknar någon av modellens ristare tillräckligt – inte att ristaren
        är okänd för forskningen, och inte säkert att det är någon annan. Ett namn betyder inte heller att det inte kan vara
        någon annan, bara att det är mindre troligt. Typiskt förstaval för ristare den inte känner: {pc(o.small_carvers.median_p)} (median), mot {pc(o.small_carvers.median_p_known)} för kända.
      </p>
      <Details title="Den gömda ristaren, en i taget">
        <div className="overflow-x-auto">
          <ExportTable><table className="w-full text-sm">
            <thead><tr><Th>Gömd ristare</Th><Th>Stenar</Th><Th>Får &quot;kanske någon annan&quot;</Th></tr></thead>
            <tbody>{o.left_out.per_carver.map(r => (
              <tr key={r.carver} className="border-t border-slate-900/5"><td className="p-2 font-semibold">{r.carver}</td><td className="p-2">{r.n}</td><td className="p-2">{pc(r.flagged)}</td></tr>))}</tbody>
          </table></ExportTable>
        </div>
      </Details>
    </div>
  );
}

const LIT_STYLE: Record<string, string> = {
  "beskriven": "bg-sky-50 text-sky-900 border-sky-200", "delvis beskriven": "bg-sky-50 text-sky-800 border-sky-200",
  "inget i litteraturen": "bg-emerald-50 text-emerald-900 border-emerald-200", "inte kontrollerad": "bg-slate-100 text-slate-600 border-slate-200",
};

/** What Sveriges runinskrifter says about a candidate group: status, and each attribution with its page. */
function Literature({ lit, n }: { lit?: AnonGroup["literature"]; n: number }) {
  if (!lit) return <>–</>;
  return (
    <div className="space-y-1">
      <span className={`inline-block rounded-full border px-2 py-0.5 font-semibold ${LIT_STYLE[lit.status] ?? ""}`}>
        {lit.status === "beskriven" || lit.status === "delvis beskriven" ? `${lit.status === "beskriven" ? "Beskriven" : "Delvis beskriven"}: ${lit.n_covered} av ${n} stenar`
          : lit.status === "inget i litteraturen" ? `Inget i SRI (${lit.n_read} av ${n} stenar lästa)` : "Inte kontrollerad"}
      </span>
      {lit.attributions.map((a, i) => (
        <div key={i}><span className="font-semibold">{a.carver ? `${a.carver}: ` : ""}</span>{a.text} <span className="text-slate-500">({a.reference})</span></div>
      ))}
      {(lit.nearby_signed ?? []).map(x => (
        <div key={x.stone} className="text-slate-600"><span className="font-semibold">Signerad i bygden, utanför gruppen: </span>
          <Link href={`/inskrifter/${encodeURIComponent(x.stone)}`} className="hover:underline">{x.stone}</Link> – {x.text}</div>
      ))}
    </div>
  );
}

export function Anonymous({ data }: { data: Corpus }) {
  const a = data.anonymous, f = data.figure_urls.anonymous || {};
  if (!a) return <p className="text-sm text-slate-600">Analysen av skrivmiljöer saknas i den här beräkningen; beräkna korpusanalyserna på nytt.</p>;
  const v = a.validation, cal = a.calibration, ho = v.heldout, cov = a.coverage;
  const cands = [...a.groups.filter(g => g.status === "candidate")].sort((x, y) => Number(!!y.robust) - Number(!!x.robust) || y.n - x.n);
  const known = a.groups.filter(g => g.status === "known");
  const nRobust = cands.filter(g => g.robust).length;
  const candProv = cov ? asList(cov.candidate_provinces) : [];
  const prov = (c: string) => PROVINCE_NAMES[c] || c;
  const boxes: [string, string][] = [
    ["Möjliga skrivmiljöer", `${cands.length} grupper`],
    ["Håller utan tidsdragen", `${nRobust} av ${cands.length}`],
    ["Liknar en känd ristare", `${known.length} grupper`],
    ["Prövat på kända ristare", `${pc(v.purity)} mot ${pc(v.purity_geography)} för närhet`],
    ...(ho ? [["Prövat på ristare metoden inte sett", `${pc(ho.purity)} mot ${pc(ho.purity_geography)} för närhet`] as [string, string]] : []),
  ];
  return (
    <>
      <SectionIntro section={sectionOf(data, "anonymous")} patterns={data.patterns} />
      <div className={`grid grid-cols-2 ${boxes.length > 4 ? "md:grid-cols-5" : "md:grid-cols-4"} gap-3`}>
        {boxes.map(([l, val]) => (
          <div key={l} className="rounded-2xl bg-white border border-slate-200 p-4">
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500"><Tip text={GLOSSARY[l]}>{l}</Tip></div>
            <div className="text-xl font-bold text-slate-900">{val}</div>
          </div>
        ))}
      </div>
      {cov && (
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-950">
          <strong>Prövat bara där ristare är kända.</strong> {cov.carvers_by_province.U ?? 0} av de {cov.n_carvers} kända ristarna (med minst tre stenar)
          finns i Uppland och {cov.carvers_by_province["Sö"] ?? 0} i Södermanland, men bara {cov.carvers_in_candidate_provinces} i
          kandidaternas landskap. Där har {candProv.map(c => `${pc(cov.share_attributed[c])} av stenarna i ${prov(c)}`).join(", ")} en ristare i Rundata,
          mot {pc(cov.share_attributed.U)} i Uppland. Om gränsen för vad som räknas som lika gäller i de landskapen är inte prövat, så grupperna där är hypoteser.
          {a.signature_coverage && <> Andelarna mäter databasen, inte forskningen: av {a.signature_coverage.n} runstenar med en ristarsignatur
            i Källströms katalog (2007) saknar {a.signature_coverage.missing} ristare i Rundata – {a.signature_coverage.outside_U_So.missing} av{" "}
            {a.signature_coverage.outside_U_So.n} utanför Uppland och Södermanland. Ristaren enligt litteraturen visas på stenens sida.</>}
        </div>
      )}
      {a.literature_pairs && a.literature_pairs.n_pairs > 0 && (
        <div className="rounded-2xl border border-[#b7410e]/25 bg-[#b7410e]/5 p-4 text-sm text-slate-800">
          <strong>Skrivmiljöer, inte ristare.</strong> Utanför Mälardalen kan grupperna prövas mot det Sveriges runinskrifter och
          Källström (2007) säger. Av {a.literature_pairs.n_pairs} par stenar som litteraturen knyter till samme ristare hamnar{" "}
          {a.literature_pairs.same_group} i samma grupp – men {a.literature_pairs.expected_from_neighbours.toLocaleString("sv-SE")} vore
          väntade bara av att grannstenar grupperas ihop.
          {a.literature_pairs.merged.length > 0 && <> Och {a.literature_pairs.merged.map(m => `grupp ${m.group} rymmer två signerade ristare (${m.carvers.join(" och ")})`).join("; ")}.</>}
          {" "}Grupperna visar alltså en verkstads eller en bygds sätt att skriva, inte en enskild hand. Arbetsnamnen följer typstenens socken.
        </div>
      )}
      <Fig src={f.map} alt="Grupper av stenar utan ristare" narrow />
      <Details title={`Möjliga skrivmiljöer (${cands.length})`} open>
        <div className="overflow-x-auto">
          <ExportTable><table className="w-full text-sm">
            <thead><tr><Th>Nr</Th><Th>Arbetsnamn</Th><Th>Stenar</Th><Th>Socknar</Th>
              <Th>Stilgrupper</Th><Th>Utmärks av (gruppen mot trakten)</Th><Th>Stabilitet</Th><Th tip="Hur stor del av gruppen som återkommer när stilgrupp, kors, stungna runor, böner och signaturer – drag som följer tiden – tas bort, och gränsen räknas om.">Utan tidsdragen</Th>
              <Th>Närmast liknande ristare i Rundata</Th>
              <Th tip="Vad Sveriges runinskrifter (Brate, Kinander, Jungner & Svärdström) och Källström, Mästare och minnesmärken (2007), redan säger om gruppens stenar – attribueringar och signaturer som Rundatas ristarfält saknar.">Litteraturen</Th></tr></thead>
            <tbody>{cands.map(g => {
              const parishes = asList(g.parishes);
              return (
                <tr key={g.id} className="border-t border-slate-900/5 align-top">
                  <td className="p-2">{g.id}</td>
                  <td className="p-2 font-semibold">{g.name}<div className="text-[11px] font-normal text-slate-500">typsten{" "}
                    <Link href={`/inskrifter/${encodeURIComponent(g.type_stone)}`} className="hover:underline">{g.type_stone}</Link></div></td>
                  <td className="p-2 text-xs">{g.n}: <Stones list={asList(g.stones)} /></td>
                  <td className="p-2 text-xs">{parishes.slice(0, 4).join(", ")}{parishes.length > 4 ? " …" : ""}</td>
                  <td className="p-2 text-xs">{(g.styles || []).map(x => `${x.style} ${x.n}`).join(", ") || "–"}</td>
                  <td className="p-2 text-xs">{(g.marks || []).map(m => `${m.feature} (${pc(m.share_group)} mot ${pc(m.share_area)})`).join("; ") || "–"}</td>
                  <td className="p-2">{pc(g.stability)}</td>
                  <td className="p-2">{g.robust_no_time == null ? "–" : (
                    <span className={`inline-block rounded-full border px-2 py-0.5 text-xs font-semibold ${g.robust ? "bg-emerald-50 text-emerald-900 border-emerald-200" : "bg-slate-100 text-slate-600 border-slate-200"}`}>
                      {pc(g.robust_no_time)}{g.robust ? " håller" : " delvis"}</span>)}</td>
                  <td className="p-2 text-xs">{g.nearest_carver ? `${g.nearest_carver.carver} (${d2(g.nearest_carver.km, 0)} km bort, inte lika nära som samma ristares stenar)` : "ingen inom 50 km"}</td>
                  <td className="p-2 text-xs min-w-[16rem]"><Literature lit={g.literature} n={g.n} /></td>
                </tr>
              );
            })}</tbody>
          </table></ExportTable>
        </div>
      </Details>
      {known.length > 0 && (
        <Details title={`Grupper som liknar en känd ristare (${known.length})`}>
          <p className="text-xs text-slate-500">Stenar utan ristare i Rundata som kan höra till en känd ristare – underlag för attribuering snarare än en ny ristare.</p>
          <div className="overflow-x-auto">
            <ExportTable><table className="w-full text-sm">
              <thead><tr><Th>Nr</Th><Th>Liknar</Th><Th>Stenar</Th><Th>Attribueringsmodellen</Th><Th>Stabilitet</Th></tr></thead>
              <tbody>{known.map(g => (
                <tr key={g.id} className="border-t border-slate-900/5 align-top">
                  <td className="p-2">{g.id}</td>
                  <td className="p-2 font-semibold">{g.nearest_carver?.as_close_as_same_carver ? g.nearest_carver.carver : g.model?.carver}</td>
                  <td className="p-2 text-xs">{g.n}: <Stones list={asList(g.stones)} /></td>
                  <td className="p-2 text-xs">{g.model ? `${g.model.carver} för ${pc(g.model.share)} av ${g.model.n} stenar med förslag` : "–"}</td>
                  <td className="p-2">{pc(g.stability)}</td>
                </tr>))}</tbody>
            </table></ExportTable>
          </div>
        </Details>
      )}
      <Details title="Hur metoden prövades">
        <p className="text-sm text-slate-600">
          När metoden kördes på {v.n_stones} stenar med känd ristare, som om ristaren vore okänd, bestod en grupp i genomsnitt till {pc(v.purity)} av
          samma ristare ({pc(v.share_pure)} av grupperna till minst tre fjärdedelar), mot {pc(v.purity_geography)} för lika många närliggande stenar.
          Två stenar länkas när de ligger inom {cal.link_km} km och är så lika att paret är minst {cal.lr_min} gånger vanligare bland samma ristares
          stenar än bland olika ristares; {pc(cal.precision)} av sådana par med känd ristare är samma ristare. Gränsen justerades efter just den kontrollen, så
          resultatet överskattar något.
        </p>
        {ho && (
          <p className="mt-2 text-sm text-slate-600">
            Strängare prov: ristarna delades slumpvis i {ho.folds} delar, gränsen togs fram på två och prövades på den tredje, som metoden aldrig sett,
            och allt upprepades {ho.runs} gånger. Grupperna bestod då i genomsnitt till {pc(ho.purity)} av samma ristare, mot {pc(ho.purity_geography)} för
            närliggande stenar – en skillnad på {Math.round(ho.difference * 100)} procentenheter ({([] as number[]).concat(ho.difference_ci).map(x => Math.round(x * 100)).join("–")}), till gruppernas fördel i {ho.runs_above} av {ho.runs} upprepningar.
            Procenttalen är högre än i det första provet eftersom varje prov bara har en del av ristarna; det som räknas är avståndet till närhetsgrupperna.
          </p>
        )}
      </Details>
      <DocsNote anchor="1g-okända-ristare">Hur grupperna ska läsas och vilka reservationer som gäller står i avsnitt 1g.</DocsNote>
      <Method text={a.method} />
    </>
  );
}
