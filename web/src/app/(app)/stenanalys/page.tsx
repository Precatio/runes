/* eslint-disable @next/next/no-img-element */
"use client";

// Full stone analysis: one scan and a signum in, an article out. Runs the same steps as the individual
// tools (and scripts/full_stone_analysis.py): images from the scan, automatic groove analysis with a
// sensitivity analysis, 2D analysis, blind readings validated against Rundata, synthesis and the stone
// report with an appendix on how the analysis was made.
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/components/AuthContext";
import { useSettings } from "@/components/SettingsContext";
import ReportPreview, { downloadBlob, type ReportResult } from "@/components/ReportPreview";
import { API_URL } from "@/lib/api";
import { corpus, type ScanMetadata } from "@/lib/corpus";
import { db, type GrooveAnalysisRecord, type LinguisticResultData, type TwoDResultData } from "@/lib/db";
import { safeFilename } from "@/lib/export";
import { loadImage } from "@/lib/images";
import { MeshSession, type AutoAnalysisResult } from "@/lib/mesh";
import { METRICS, type FeatureType, type Metric, type SliceMetrics } from "@/lib/metrics";
import { rundata, type Inscription } from "@/lib/rundata";
import type { SynthesisResult } from "@/lib/synthesis";

type StepState = "väntar" | "pågår" | "klart" | "misslyckades" | "hoppades över";
interface Step { key: string; name: string; state: StepState; result?: string }
interface Relief { relief: string; depth: string; raking: Record<string, string>; resolution_mm: number; normal: number[] }
interface Reading extends LinguisticResultData { label: string; error?: string }

const STEPS: [string, string][] = [
  ["upload", "Ladda upp skanningen"], ["images", "Bilder ur skanningen"], ["grooves", "Spåranalys och känslighet"],
  ["twod", "2D-bildanalys"], ["reading", "Blind läsning och validering"], ["synthesis", "Syntes och attribuering"],
  ["research", "Forskningsläge och syfte"], ["report", "Stenrapport"],
];

const field = "liquid-glass-input-wrapper rounded-xl px-3 py-2 text-sm font-semibold outline-none w-full mt-1";
const label = "text-[11px] font-bold uppercase tracking-wider text-slate-500";

async function rotated(dataUrl: string, deg: number): Promise<string> {
  if (!deg) return dataUrl;
  const img = await loadImage(dataUrl);
  const c = document.createElement("canvas");
  const swap = deg % 180 !== 0;
  c.width = swap ? img.height : img.width;
  c.height = swap ? img.width : img.height;
  const ctx = c.getContext("2d")!;
  ctx.translate(c.width / 2, c.height / 2);
  ctx.rotate((deg * Math.PI) / 180);
  ctx.drawImage(img, -img.width / 2, -img.height / 2);
  return c.toDataURL("image/png");
}

const detail = async (res: Response, fallback: string) =>
  (await res.json().catch(() => null))?.detail || `${fallback} (${res.status})`;

export default function StoneAnalysisPage() {
  const { user } = useAuth();
  const { aiHeaders, userName, userInstitution } = useSettings();
  const [file, setFile] = useState<File | null>(null);
  const [signum, setSignum] = useState("");
  const [rec, setRec] = useState<Inscription | null>(null);
  const [stone, setStone] = useState("Granit");
  const [weathering, setWeathering] = useState("Medel");
  const [featureType, setFeatureType] = useState<FeatureType>("rune");
  const [scan, setScan] = useState<ScanMetadata>({});
  const [sensitivities, setSensitivities] = useState("3,5");
  const [orientations, setOrientations] = useState<number[]>([0, 180]);
  const [useAI, setUseAI] = useState(true);
  const [flip, setFlip] = useState(false);

  const [steps, setSteps] = useState<Step[]>(STEPS.map(([key, name]) => ({ key, name, state: "väntar" })));
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [preview, setPreview] = useState<Relief | null>(null);
  const [report, setReport] = useState<(ReportResult & { surface: boolean; surface_note: string | null }) | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState<string | null>(null);
  const [busyDocx, setBusyDocx] = useState(false);
  const last = useRef<{ body: Record<string, unknown>; analysis: GrooveAnalysisRecord; reading: Reading | null;
    twod: TwoDResultData | null; synthesis: SynthesisResult | null; raking: string } | null>(null);

  useEffect(() => {
    const s = signum.trim();
    const t = setTimeout(() => {
      if (!s) { setRec(null); return; }
      rundata.inscription(s).then(setRec).catch(() => setRec(null));
    }, 400);
    return () => clearTimeout(t);
  }, [signum]);

  const mark = (key: string, state: StepState, result?: string) =>
    setSteps(ss => ss.map(s => (s.key === key ? { ...s, state, result: result ?? s.result } : s)));

  const run = async () => {
    if (!file) return;
    setRunning(true); setError(null); setReport(null); setSaved(null); setPreview(null);
    setSteps(STEPS.map(([key, name]) => ({ key, name, state: "väntar" })));
    const notes: string[] = [];
    const wfSteps: { name: string; result: string }[] = [];
    const headers = aiHeaders;
    try {
      // 1. Upload
      mark("upload", "pågår");
      const session = new MeshSession(file, setProgress);
      const info = await session.ensure();
      mark("upload", "klart", `${info.faces.toLocaleString("sv-SE")} trianglar`);

      // 2. Images from the scan (the carved side: the stone's thinnest direction, or the other side)
      mark("images", "pågår");
      let relief = await session.postJSON<Relief>("/api/3d/render_relief", {});
      if (flip) {
        const n = relief.normal.map(v => -v);
        relief = await session.postJSON<Relief>("/api/3d/render_relief", { normal_x: n[0], normal_y: n[1], normal_z: n[2] });
      }
      setPreview(relief);
      const normal = relief.normal;
      const res = relief.resolution_mm.toFixed(2).replace(".", ",");
      wfSteps.push({ name: "Bilder ur skanningen", result: `relief, djup och strykljus ur fyra riktningar (${res} mm per pixel)` });
      mark("images", "klart", `${res} mm per pixel`);

      // 3. Groove analysis with sensitivity analysis
      mark("grooves", "pågår");
      const sens = sensitivities.split(",").map(x => Number(x.trim())).filter(x => x >= 1 && x <= 10);
      const sensitivity = [];
      let main: AutoAnalysisResult | null = null;
      for (const k of sens) {
        try {
          const d = await session.postJSON<AutoAnalysisResult>("/api/3d/auto_analyze", {
            normal_x: normal[0], normal_y: normal[1], normal_z: normal[2], sensitivity: k, meta_stone: stone, meta_weathering: weathering,
          });
          if (!d.summary) { notes.push(`Spåranalysen med känslighet ${k} gav inga godkända snitt.`); continue; }
          main = main ?? d;
          const sm = d.summary;
          sensitivity.push({
            sensitivity: k, threshold_mm: d.parameters.threshold_mm, candidates: d.counts.candidates, accepted: d.counts.accepted,
            wide_area_mm2: d.counts.wide_area_mm2, angle_mean: sm.apex_vinkel_deg.mean, angle_sd: sm.apex_vinkel_deg.sd,
            depth_mean: sm.spårdjup_mm.mean, width_mean: sm.spårbredd_mm.mean, review_png: d.image_base64,
          });
        } catch (e) {
          notes.push(`Spåranalysen med känslighet ${k} misslyckades: ${e instanceof Error ? e.message : e}`);
        }
      }
      if (!main) throw new Error("Spåranalysen hittade inga godkända tvärsnitt. Prova den andra sidan eller lägre känslighet.");
      const acc = main.slices.filter(s => s.accepted);
      const slices: SliceMetrics[] = acc.map(s => ({
        ...(Object.fromEntries(METRICS.map(m => [m, s[m] as number])) as Record<Metric, number>),
        position_mm: s.position_mm, fit_r2: s.fit_r2, profile: s.profile, point: s.point, direction: s.direction, up: s.up,
      }));
      const analysis: GrooveAnalysisRecord = {
        id: `auto-${Date.now()}`, feature_type: featureType, summary: main.summary!, slices,
        provenance: { ...main.provenance, feature_type: featureType }, savedAt: new Date().toISOString(),
      };
      const s0 = sensitivity[0];
      const fmt1 = (v: number | null) => (v == null ? "–" : v.toFixed(1).replace(".", ","));
      wfSteps.push({ name: "Spåranalys", result: `${s0.accepted} godkända av ${s0.candidates} snitt; V-vinkel ${fmt1(s0.angle_mean)}° ± ${fmt1(s0.angle_sd)}°` });
      mark("grooves", "klart", `${s0.accepted} snitt, V-vinkel ${fmt1(s0.angle_mean)}°` + (sensitivity.length > 1 ? `; ${sensitivity.length} känsligheter` : ""));

      const raking = relief.raking["nordväst"];
      let twod: TwoDResultData | null = null;
      const readings: Reading[] = [];
      if (useAI) {
        // 4. 2D analysis
        mark("twod", "pågår");
        const fd = new FormData();
        fd.append("file", await (await fetch(raking)).blob(), "strykljus.png");
        const r2 = await fetch(`${API_URL}/api/2d/analyze`, { method: "POST", headers, body: fd });
        if (r2.ok) {
          twod = await r2.json();
          wfSteps.push({ name: "2D-bildanalys", result: `stilgrupp ${twod!.predicted_style} (AI, okalibrerad ${twod!.confidence} %)` });
          mark("twod", "klart", `stilgrupp ${twod!.predicted_style}` + (rec?.style ? ` (Rundata ${rec.style})` : ""));
        } else {
          const msg = await detail(r2, "2D-analysen misslyckades");
          notes.push(`2D-bildanalysen misslyckades: ${msg}`);
          mark("twod", "misslyckades", msg);
        }

        // 5. Blind readings in each orientation, then validated against each other, Rundata and known texts
        mark("reading", "pågår");
        for (const deg of orientations) {
          const r = await fetch(`${API_URL}/api/phonetics/analyze`, {
            method: "POST", headers: { ...headers, "Content-Type": "application/json" },
            body: JSON.stringify({ image_base64: await rotated(raking, deg), signum: signum || "Okänd" }),
          });
          if (r.ok) readings.push({ label: `Strykljus, ${deg}°`, ...(await r.json()) });
          else {
            const msg = await detail(r, "Läsningen misslyckades");
            readings.push({ label: `Strykljus, ${deg}°`, error: "misslyckades" } as Reading);
            notes.push(`Blind läsning (${deg}°) misslyckades: ${msg}`);
          }
        }
        const ok = readings.filter(x => x.transliteration);
        for (const x of ok) {
          const r = await fetch(`${API_URL}/api/phonetics/compare`, {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ signum, transliteration: x.transliteration, normalization: x.normalization ?? "",
              other_readings: ok.filter(y => y !== x).map(y => y.transliteration) }),
          });
          if (r.ok) Object.assign(x, await r.json());
        }
        if (ok.length) {
          const v = ok[0].validation;
          wfSteps.push({ name: "Blind läsning", result: `${ok.length} av ${readings.length} lyckades; den första: ${v?.status ?? "ej validerad"}` });
          mark("reading", ok.some(x => x.validation?.reliable) ? "klart" : "misslyckades",
            ok.map(x => `${x.label}: ${x.validation?.status ?? "–"}`).join("; "));
        } else {
          mark("reading", "misslyckades", "ingen läsning lyckades");
        }
      } else {
        mark("twod", "hoppades över"); mark("reading", "hoppades över");
        notes.push("AI-stegen (2D-analys, läsning, AI-text) hoppades över.");
      }

      // 6. Synthesis
      mark("synthesis", "pågår");
      const reading = readings.find(x => x.transliteration) ?? null;
      const entries = user ? await corpus.list().catch(() => []) : null;
      const rs = await fetch(`${API_URL}/api/synthesis/analyze`, {
        method: "POST", headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify({
          signum: signum || "Okänd", stoneType: stone, weathering,
          analyses: [{ id: analysis.id, feature_type: featureType, savedAt: analysis.savedAt,
            slices: slices.map(s => ({ ...Object.fromEntries(METRICS.map(m => [m, s[m]])), position_mm: s.position_mm })) }],
          analysis_id: analysis.id,
          corpus: (entries ?? []).map(e => ({ signum: e.signum, feature_type: e.feature_type, means: e.means,
            slices: e.slices.map(s => ({ ...Object.fromEntries(METRICS.map(m => [m, s[m]])), position_mm: s.position_mm })) })),
          corpus_note: entries === null ? "logga in för att jämföra med den delade mätkorpusen." : null,
          reading: reading ? { transliteration: reading.transliteration, normalization: reading.normalization,
            others: readings.filter(x => x.transliteration && x !== reading).map(x => x.transliteration) } : null,
          two_d: twod ? { predicted_style: twod.predicted_style, confidence: twod.confidence, reasoning: twod.reasoning } : undefined,
          include_geology: true,
        }),
      });
      if (!rs.ok) throw new Error(await detail(rs, "Syntesen misslyckades"));
      const synthesis: SynthesisResult = await rs.json();
      if (synthesis.outcome) wfSteps.push({ name: "Syntes", result: synthesis.outcome.text });
      if (useAI && !synthesis.ai_used) notes.push("Syntesens AI-text var inte tillgänglig (ingen nyckel, slut på kvot eller tidsgräns); texterna är framräknade.");
      mark("synthesis", "klart", synthesis.outcome?.text);

      // 7. What Forskningsluckor knows about the stone; purpose; how often the candidates carved in its style
      if (signum.trim() && rec) {
        mark("research", "pågår");
        const names = synthesis.candidates.slice(0, 3).map(c => c.name).join(",");
        const rr0 = await fetch(`${API_URL}/api/research/stone/${encodeURIComponent(signum.trim())}?candidates=${encodeURIComponent(names)}`);
        if (rr0.ok) {
          const ctx: { purpose: { label: string }[]; carvers: { carver: string; style: string | null; style_k: number; style_n: number }[];
            status: { carver: boolean } } = await rr0.json();
          const purpose = ctx.purpose.map(c => c.label.toLowerCase()).join(", ") || "ingen kategori";
          const styles = ctx.carvers.map(c => `${c.carver} ${c.style ?? "–"} i ${c.style_k} av ${c.style_n}`).join("; ");
          const text = `Syfte: ${purpose}${styles ? `. Stilgrupp hos kandidaterna: ${styles}` : ""}`;
          wfSteps.push({ name: "Forskningsläge och syfte", result: text });
          mark("research", "klart", text);
        } else {
          mark("research", "misslyckades", await detail(rr0, "Forskningsläget kunde inte hämtas"));
        }
      } else {
        mark("research", "hoppades över", "inget signum i Rundata");
      }

      // 8. Report
      mark("report", "pågår");
      const body = {
        signum, author: userName, institution: userInstitution,
        meta: { stone, weathering, text: signum }, scan, condition: { weathering: weathering.toLowerCase() },
        analyses: [analysis], counts: main.counts, mesh_id: info.mesh_id, view: { normal },
        corpus: (entries ?? []).map(e => ({ signum: e.signum, feature_type: e.feature_type, means: e.means })),
        synthesis, reading: reading ? { ...reading, markers: undefined, others: readings.filter(x => x.transliteration && x !== reading).map(x => x.transliteration) } : null,
        two_d: { image: raking, result: twod, crops: [],
          caption: "Digitalt strykljus från nordväst, räknat ur 3D-skanningen – bilden som 2D-analysen och läsningen fick." },
        workflow: {
          date: new Date().toISOString().slice(0, 10), steps: wfSteps, sensitivity, relief_png: relief.relief,
          two_d_reasoning: twod?.reasoning ?? null,
          readings: readings.map(x => ({ label: x.label, transliteration: x.transliteration, reading_comparison: x.reading_comparison,
            validation: x.validation, error: x.error })),
          notes: [...notes, ...(scan.device ? [] : ["Skanningens upplösning, utrustning och licens bör fyllas i."])],
        },
        use_ai: useAI,
      };
      const rr = await fetch(`${API_URL}/api/reports/stone`, {
        method: "POST", headers: { ...headers, "Content-Type": "application/json" }, body: JSON.stringify(body),
      });
      if (!rr.ok) throw new Error(await detail(rr, "Rapporten kunde inte skapas"));
      const rep = await rr.json();
      setReport(rep);
      last.current = { body, analysis, reading, twod, synthesis, raking };
      mark("report", "klart", `${rep.figures.length} figurer`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysen avbröts.");
      setSteps(ss => ss.map(s => (s.state === "pågår" ? { ...s, state: "misslyckades" } : s)));
    } finally {
      setRunning(false);
    }
  };

  const base = safeFilename(`${signum || file?.name || "sten"} stenanalys`);
  const downloadDocx = async () => {
    if (!last.current || !report) return;
    setBusyDocx(true);
    try {
      const res = await fetch(`${API_URL}/api/reports/stone`, {
        method: "POST", headers: { "Content-Type": "application/json", ...aiHeaders },
        body: JSON.stringify({ ...last.current.body, format: "docx", ai_text: report.ai_text }),
      });
      if (!res.ok) throw new Error("Word-filen kunde inte skapas.");
      await downloadBlob(res, `${base}.docx`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Word-filen kunde inte skapas.");
    } finally {
      setBusyDocx(false);
    }
  };

  const saveProject = async () => {
    if (!last.current) return;
    const { analysis, reading, twod, synthesis, raking } = last.current;
    const existing = signum ? await db.getProjectBySignum(signum) : null;
    const p = await db.saveProject({
      id: existing?.id, name: existing?.name ?? (signum || file?.name || "Stenanalys"), fileName: file?.name ?? "",
      metaText: signum, metaStone: stone, metaWeathering: weathering, slices: existing?.slices ?? [],
      grooveAnalyses: [...(existing?.grooveAnalyses ?? []), analysis],
      // Only a validated reading is stored as the project's reading
      linguisticResults: reading && reading.validation?.reliable ? { ...reading, markers: undefined } : existing?.linguisticResults,
      twoDResults: twod ?? existing?.twoDResults, twoDImage: raking,
      synthesis: synthesis ? { result: synthesis, analysisId: analysis.id, featureType, savedAt: new Date().toISOString() } : existing?.synthesis,
    });
    setSaved(p.name);
  };

  const stateStyle: Record<StepState, string> = {
    "väntar": "text-slate-400", "pågår": "text-sky-700 font-bold", "klart": "text-emerald-700",
    "misslyckades": "text-red-700", "hoppades över": "text-slate-400",
  };
  const icon: Record<StepState, string> = { "väntar": "○", "pågår": "◐", "klart": "✓", "misslyckades": "!", "hoppades över": "–" };

  return (
    <div className="flex flex-col w-full max-w-7xl mx-auto p-4 md:p-6 space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">Fullständig stenanalys</h2>
        <p className="text-slate-600 text-[16px] leading-relaxed max-w-3xl font-medium">
          Ladda upp en 3D-skanning och ange signum. Appen räknar fram bilder ur skanningen, mäter huggspåren (med
          känslighetsanalys), gör en 2D-analys och blinda läsningar som prövas mot Rundata, väger samman beläggen och
          skriver en artikel med alla figurer och en bilaga om hur analysen gjordes. Varje steg använder samma metoder som
          de enskilda verktygen; se METHODS.md, avsnitt 14c.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="liquid-glass-island rounded-[32px] p-6 space-y-4 h-fit">
          <label className={label}>3D-skanning (STL, OBJ, PLY)
            <input type="file" accept=".stl,.obj,.ply" disabled={running} onChange={e => setFile(e.target.files?.[0] ?? null)}
              className="w-full mt-1 text-xs bg-white border border-slate-200 rounded-xl p-2" />
          </label>
          <label className={label}>Signum
            <input value={signum} onChange={e => setSignum(e.target.value)} placeholder="t.ex. Sö 113" className={field} disabled={running} />
          </label>
          {signum.trim() && (
            <p className={`text-xs ${rec ? "text-emerald-700" : "text-amber-700"}`}>
              {rec ? `I Rundata: ${rec.signum}, ${rec.place} · ${rec.material || "material saknas"} · ${rec.style || "ingen stilgrupp"}` : "Finns inte i Rundata – läsningen kan inte prövas mot en publicerad text."}
            </p>
          )}
          <div className="grid grid-cols-2 gap-3">
            <label className={label}>Bergart<input value={stone} onChange={e => setStone(e.target.value)} className={field} /></label>
            <label className={label}>Vittring
              <select value={weathering} onChange={e => setWeathering(e.target.value)} className={field}>
                <option>Låg</option><option>Medel</option><option>Hög</option>
              </select>
            </label>
            <label className={label}>Spårtyp
              <select value={featureType} onChange={e => setFeatureType(e.target.value as FeatureType)} className={field}>
                <option value="rune">Runor</option><option value="unknown">Ej indelat</option>
              </select>
            </label>
            <label className={label}>Känsligheter
              <input value={sensitivities} onChange={e => setSensitivities(e.target.value)} className={field} title="Den första är huvudanalysen" />
            </label>
            <label className={label}>Skanner<input value={scan.device ?? ""} onChange={e => setScan(s => ({ ...s, device: e.target.value }))} className={field} /></label>
            <label className={label}>Skannat av<input value={scan.scanned_by ?? ""} onChange={e => setScan(s => ({ ...s, scanned_by: e.target.value }))} className={field} /></label>
            <label className={label}>Upplösning (mm)<input inputMode="decimal" value={scan.resolution_mm ?? ""} onChange={e => setScan(s => ({ ...s, resolution_mm: e.target.value ? Number(e.target.value.replace(",", ".")) : undefined }))} className={field} /></label>
            <label className={label}>Licens<input value={scan.license ?? ""} onChange={e => setScan(s => ({ ...s, license: e.target.value }))} className={field} /></label>
          </div>
          <div className="space-y-1.5 text-sm text-slate-700">
            <label className="flex items-center gap-2"><input type="checkbox" checked={useAI} onChange={e => setUseAI(e.target.checked)} /> AI-steg (2D-analys, blind läsning, AI-text)</label>
            <div className="flex items-center gap-3 pl-6 text-xs">
              Läs i orienteringarna:
              {[0, 90, 180, 270].map(d => (
                <label key={d} className="flex items-center gap-1">
                  <input type="checkbox" disabled={!useAI} checked={orientations.includes(d)}
                    onChange={e => setOrientations(o => (e.target.checked ? [...o, d].sort((a, b) => a - b) : o.filter(x => x !== d)))} />{d}°
                </label>
              ))}
            </div>
            <label className="flex items-center gap-2"><input type="checkbox" checked={flip} onChange={e => setFlip(e.target.checked)} /> Analysera den andra sidan av stenen</label>
          </div>
          <button onClick={run} disabled={!file || running}
            className="w-full py-3 bg-[#b7410e] hover:bg-[#9a350b] text-white font-bold rounded-2xl disabled:opacity-40">
            {running ? "Analyserar …" : "Starta stenanalysen"}
          </button>
          <p className="text-[11px] text-slate-500">
            Tar några minuter. Den ristade sidan skattas som stenens tunnaste riktning; visar förhandsbilden fel sida, kryssa i
            &quot;den andra sidan&quot; och kör igen. Med inloggning jämförs huggtekniken också med mätkorpusen.
          </p>
        </div>

        <div className="lg:col-span-2 space-y-4">
          <div className="liquid-glass-island rounded-[32px] p-6">
            <ol className="space-y-2">
              {steps.map(s => (
                <li key={s.key} className="flex gap-3 text-sm">
                  <span className={`w-4 ${stateStyle[s.state]}`}>{icon[s.state]}</span>
                  <span className="font-semibold text-slate-800 w-56 shrink-0">{s.name}</span>
                  <span className={`${stateStyle[s.state]} font-normal`}>
                    {s.key === "upload" && s.state === "pågår" ? `${Math.round(progress * 100)} %` : s.result ?? s.state}
                  </span>
                </li>
              ))}
            </ol>
            {error && <p className="text-sm text-red-700 font-semibold mt-3">{error}</p>}
          </div>
          {preview && (
            <div className="liquid-glass-island rounded-[32px] p-4">
              <img src={preview.raking["nordväst"]} alt="Strykljus ur skanningen" className="w-full rounded-2xl" />
              <p className="text-[11px] text-slate-500 mt-2">Strykljus från nordväst, räknat ur skanningen – kontrollera att det är den ristade sidan.</p>
            </div>
          )}
        </div>
      </div>

      {report && (
        <>
          <div className="flex flex-wrap items-center gap-3">
            <button onClick={saveProject} className="px-5 py-2.5 bg-white border border-slate-300 font-bold rounded-xl text-sm">
              {saved ? `Sparat i projektet ${saved}` : "Spara i projekt"}
            </button>
            <Link href="/synthesis" className="text-sm underline text-slate-600">Öppna syntesen</Link>
            {report.surface_note && <span className="text-sm text-amber-800">{report.surface_note}</span>}
          </div>
          <ReportPreview report={report} base={base} busy={busyDocx} onDocx={downloadDocx} />
        </>
      )}
    </div>
  );
}
