"use client";

// Exportera: the researcher ticks the files to download from the groove analysis – images computed from the scan,
// figures and tables from the measurement, the whole analysis as JSON – and gets one file, or a ZIP with README.txt
// and kalla.json when there are more. The list of files, their names and the texts that explain them come from the
// analysis engine (GET /api/3d/export_items, src/groove_export.py ITEMS), the same texts as in README.txt; the files are
// computed there (POST /api/3d/export) from the existing results, so the numbers are those of the analysis and the
// stone report. The automatic analysis goes with the researcher's labels, read as the stone report reads them
// (lib/stoneReport.ts fromSession). The scan is credited to an open dataset only when the engine recognises the loaded
// file as one of its published files (GET /api/3d/scan_credit); otherwise the researcher can write their own credit.
import { useEffect, useRef, useState } from "react";
import { API_URL } from "@/lib/api";
import { download } from "@/lib/exportTable";
import { GLOSSARY } from "@/lib/glossary";
import { InfoTip } from "@/components/Explain";
import { ApiError, MIN_RUNES_COMPARE, MIN_RUNES_DESCRIBE, type AutoAnalysisResult, type AutoLabel, type MeshInfo, type MeshSession } from "@/lib/mesh";
import type { AnalysisProvenance, ThreeDAnalysisResult } from "@/lib/db";
import type { ViewDirection } from "@/components/ThreeDViewer";

interface ExportItem {
  id: string;
  label: string;
  file: string;
  explanation: string;
  group: "skanning" | "matning" | "data";
  formats: string[];
  needs: string[];
}

// The catalogue from GET /api/3d/export_items: the files to tick, plus texts for the ZIP, the stone report and the caveat
interface ExportCatalogue {
  items: ExportItem[];
  groups?: Partial<Record<ExportItem["group"], string>>;
  bundle?: { label: string; explanation: string };
  stone_report?: { label: string; explanation: string };
  readme_intro?: string;
  caveat?: string;
}

interface ScanCredit {
  known: boolean;
  match: string | null;
  // signa: every stone the file shows (one file can hold two, as Ög 240 and Ög 241)
  file: { name: string; signum: string | null; signa?: string[] } | null;
  dataset: {
    scanned_by: string;
    institution: string | null;
    project: string;
    license: string;
    license_url: string | null;
    doi: string;
    url: string;
    short: string;
  } | null;
  credit_text: string | null;
  computed_note: string;
}

interface Props {
  session: () => MeshSession | null;
  meshInfo: MeshInfo | null;
  getView: () => ViewDirection | null;
  signum: string;
  featureType: string;
  // The automatic analysis is exported when its tab is open (or there is no other measurement), unless the researcher
  // has chosen otherwise (an "Exportera …" button or the choice in the menu); the mode written in the files is read
  // from the exported analysis itself, not from the tab
  preferAuto: boolean;
  // Lets the researcher switch between the automatic analysis and the measurement shown, when both exist
  onChooseAnalysis?: (which: "auto" | "result") => void;
  result: ThreeDAnalysisResult | null;
  autoResult: AutoAnalysisResult | null;
  autoLabels: AutoLabel[];
  onCreateReport?: () => void;
}

const GROUPS: [ExportItem["group"], string][] = [
  ["skanning", "Bilder ur skanningen"],
  ["matning", "Bilder ur mätningen"],
  ["data", "Tabeller och data"],
];
// Not files to tick, should the catalogue list them as items: the ZIP is made by itself when more than one file is
// chosen, the stone report is its own page
const NOT_CHOSEN = new Set(["bundle_zip", "stone_report_link"]);
// Items that give more than one file (README.txt and kalla.json in the ZIP are not counted)
const FILE_COUNT: Record<string, number> = { raking: 4, depth_grid: 2 };
// Items with no visible credit (their pixels are left untouched): the engine always sends them in a ZIP with
// README.txt, also on their own (src/groove_export.py NO_FOOTER)
const NO_FOOTER = new Set(["relief", "groove_map"]);
// Terms in the glossary that explain an item
const TERM: Record<string, string> = {
  depth_heatmap: "Djup under stenytan",
  depth_grid: "ESRI ASCII-rutnät",
  relief: "Relief",
  raking: "Strykljus",
  groove_map: "Ristningskarta",
};
// provenance.parameters.mode of each measuring form (api/routers/threed.py), as src/groove_export.py MODES
const MODES: Record<string, string> = { automatic: "auto", "one-click": "oneclick", slices: "manual", path: "path" };
const FEATURE_TYPES = new Set(["rune", "ornament", "unknown"]);
const STORAGE_KEY = "vitki.export3d";
const MAX_SCAN_NOTE = 500;

// Fetched once per page load; a failure is not cached, so that a later visit tries again
let itemsCache: Promise<ExportCatalogue> | null = null;
function loadItems(): Promise<ExportCatalogue> {
  itemsCache ??= fetch(`${API_URL}/api/3d/export_items`)
    .then(async res => {
      if (!res.ok) throw new Error(`Fel ${res.status}`);
      return (await res.json()) as ExportCatalogue;
    })
    .catch(e => {
      itemsCache = null;
      throw e;
    });
  return itemsCache;
}

// The scan file to identify: the loaded model (by its id in the engine) or, without it, the file named in the
// analysis' provenance
type ScanFile = { mesh_id?: string; filename?: string; sha256?: string; md5?: string; size?: number };
const creditCache = new Map<string, Promise<ScanCredit>>();
function loadCredit(file: ScanFile): Promise<ScanCredit> {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(file)) if (v !== undefined && v !== "") q.set(k, String(v));
  const key = q.toString();
  let hit = creditCache.get(key);
  if (!hit) {
    hit = fetch(`${API_URL}/api/3d/scan_credit?${key}`).then(async res => {
      if (!res.ok) throw new Error(`Fel ${res.status}`);
      return res.json() as Promise<ScanCredit>;
    });
    hit.catch(() => creditCache.delete(key));
    creditCache.set(key, hit);
  }
  return hit;
}

function scanFileOf(meshInfo: MeshInfo | null, prov: AnalysisProvenance | undefined): ScanFile | null {
  if (meshInfo) return { mesh_id: meshInfo.mesh_id, filename: meshInfo.filename, sha256: meshInfo.sha256, md5: meshInfo.md5, size: meshInfo.bytes };
  const m = prov?.mesh;
  if (m && (m.filename || m.sha256)) return { filename: m.filename, sha256: m.sha256, md5: m.md5, size: m.bytes };
  return null;
}

function readStored(): string[] | null {
  try {
    const v = JSON.parse(window.localStorage.getItem(STORAGE_KEY) ?? "null");
    return Array.isArray(v) && v.every(x => typeof x === "string") ? v : null;
  } catch {
    return null;
  }
}

function store(ids: string[]) {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(ids));
  } catch {
    // works without it
  }
}

/** The file name the engine gave the download: filename*=UTF-8''… first, then filename="…". */
function fileNameFrom(header: string | null): string {
  if (header) {
    const star = /filename\*=UTF-8''([^;]+)/i.exec(header);
    if (star) {
      try {
        return decodeURIComponent(star[1].trim().replace(/^"|"$/g, ""));
      } catch {
        // fall through to the plain name
      }
    }
    const plain = /filename="?([^";]+)"?/i.exec(header);
    if (plain) return plain[1].trim();
  }
  return "vitki_export.zip";
}

/** A header value with Swedish letters, whichever way the server sent it: percent-encoded, Latin-1, or UTF-8 bytes that
 *  the browser has read as Latin-1. */
function headerText(value: string): string {
  let s = value;
  if (/%[0-9A-Fa-f]{2}/.test(s)) {
    try { s = decodeURIComponent(s); } catch { /* keep as it is */ }
  }
  if (/[\u0080-ÿ]/.test(s) && !/[^\u0000-ÿ]/.test(s)) {
    try { s = new TextDecoder("utf-8", { fatal: true }).decode(Uint8Array.from(s, c => c.charCodeAt(0))); } catch { /* Latin-1 */ }
  }
  return s;
}

const isAbort = (e: unknown) => e instanceof DOMException && e.name === "AbortError";

/** Signum key as src/signum.py fold_signum: no diacritics, spaces, underscores or case ("Sö 113" -> "so113"). */
function foldSignum(s: string): string {
  return s.normalize("NFKD").replace(/[\u0300-\u036f]/g, "").replace(/[\s_]+/g, "").toLowerCase();
}

/** Scrolls to the export menu on the 3D page. */
export function scrollToExport() {
  document.getElementById("exportera")?.scrollIntoView({ behavior: "smooth", block: "start" });
}

export default function GrooveExportMenu({
  session, meshInfo, getView, signum, featureType, preferAuto, onChooseAnalysis, result, autoResult, autoLabels,
  onCreateReport,
}: Props) {
  const [catalogue, setCatalogue] = useState<ExportCatalogue | null>(null);
  const items = catalogue?.items ?? null;
  const [itemsError, setItemsError] = useState(false);
  const [retry, setRetry] = useState(0);
  // The credit with the scan file it was fetched for, so that a credit never outlives its file
  const [creditFor, setCreditFor] = useState<{ key: string; credit: ScanCredit | null } | null>(null);
  const [scanNote, setScanNote] = useState("");
  // What the researcher has ticked; null = not yet, the defaults apply
  const [picked, setPicked] = useState<string[] | null>(readStored);
  const [busy, setBusy] = useState(false);
  const [skipped, setSkipped] = useState<{ label: string; reason: string }[]>([]);
  const abortRef = useRef<AbortController | null>(null);
  const meshLoaded = !!meshInfo;

  useEffect(() => {
    let live = true;
    loadItems()
      .then(cat => { if (live) { setCatalogue(cat); setItemsError(false); } })
      .catch(() => { if (live) setItemsError(true); });
    return () => { live = false; };
  }, [retry]);


  // The analysis that is exported: the automatic one with its labels when preferAuto (its tab is open, or it was
  // chosen) or nothing else has been measured, otherwise the measurement shown on the page (one click, manual, path,
  // or a selection used from the automatic analysis). The menu says which, with a switch when both exist.
  const exported: ThreeDAnalysisResult | AutoAnalysisResult | null =
    autoResult && (preferAuto || !result) ? autoResult : result;
  const isAuto = !!autoResult && exported === autoResult;
  const prov = exported?.provenance;
  const analysisMode = MODES[String(prov?.parameters?.mode ?? "")] ?? "";
  const analysisFeature = !isAuto && prov?.feature_type && FEATURE_TYPES.has(prov.feature_type) ? prov.feature_type : featureType;

  // The scan file the credit is decided by: never the typed signum
  const scanFile = scanFileOf(meshInfo, prov);
  const scanKey = scanFile ? JSON.stringify(scanFile) : "";
  useEffect(() => {
    if (!scanKey) return;
    let live = true;
    loadCredit(JSON.parse(scanKey) as ScanFile)
      .then(c => { if (live) setCreditFor({ key: scanKey, credit: c }); })
      .catch(() => { if (live) setCreditFor({ key: scanKey, credit: null }); });
    return () => { live = false; };
  }, [scanKey]);
  const credit = scanKey && creditFor?.key === scanKey ? creditFor.credit : null;

  // A download under way stops when the page is left, when another model is loaded or when the exported analysis
  // changes, so that a file for the previous model or analysis is never saved
  const meshId = meshInfo?.mesh_id;
  const current = useRef({ meshId, exported });
  useEffect(() => {
    current.current = { meshId, exported };
    return () => abortRef.current?.abort();
  }, [meshId, exported]);

  // The slices the figures and summaries use, as the stone report takes them (fromSession): in the automatic analysis
  // accepted slices not labelled excluded (a missing label counts as unknown)
  const slices = (exported?.slices ?? []) as { accepted?: boolean; point?: unknown; profile?: unknown }[];
  const used = slices.filter((s, i) => isAuto
    ? s.accepted === true && (autoLabels[i] ?? "unknown") !== "excluded"
    : s.accepted !== false);
  const withPoint = used.filter(s => s.point).length;
  const depthProfile = !isAuto ? result?.depth_profile : undefined;

  const has = (need: string): boolean => {
    switch (need) {
      case "mesh": return meshLoaded;
      case "auto": return isAuto;
      case "slices": return slices.length > 0;
      case "point>=1": return withPoint >= 1;
      case "point>=3": return withPoint >= 3;
      case "profile": return used.some(s => s.profile);
      case "summary": return isAuto ? used.length > 0 : !!exported?.summary;
      case "runes": return isAuto && (autoResult?.runes?.length ?? 0) > 0;
      case "depth_profile": return (depthProfile?.distances.length ?? 0) > 0;
      case "groove_map": return isAuto && !!autoResult?.groove_map_base64;
      case "review_image": return isAuto && !!autoResult?.image_base64;
      default: return false;
    }
  };

  const choosable = (items ?? []).filter(it => !NOT_CHOSEN.has(it.id));
  // Tables and data describe a measurement, so they need one even when the item names nothing else (full_json)
  const available = choosable.filter(it => it.needs.every(has) && (it.group !== "data" || !!exported));
  const hiddenCount = choosable.length - available.length;
  const defaults = ["depth_heatmap", "relief", ...(exported ? ["slices_csv", "summary_csv", "full_json"] : [])];
  const chosenSet = new Set(picked ?? defaults);
  const chosen = available.filter(it => chosenSet.has(it.id));
  const fileCount = chosen.reduce((n, it) => n + (FILE_COUNT[it.id] ?? 1), 0);
  const zipAnyway = fileCount === 1 && chosen.every(it => NO_FOOTER.has(it.id));
  const anyImage = chosen.some(it => it.group !== "data");

  const toggle = (id: string) => {
    const next = new Set(chosenSet);
    if (next.has(id)) next.delete(id); else next.add(id);
    const list = [...next];
    setPicked(list);
    store(list);
  };

  const cancel = () => abortRef.current?.abort();

  const runExport = async () => {
    if (chosen.length === 0 || busy) return;
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    const startMesh = meshId, startExported = exported;
    setBusy(true);
    setSkipped([]);
    try {
      const view = getView();
      const note = scanNote.trim().slice(0, MAX_SCAN_NOTE);
      const fields: Record<string, string | number> = {
        items: chosen.map(it => it.id).join(","),
        signum: signum.trim(),
        feature_type: analysisFeature,
        ...(analysisMode ? { mode: analysisMode } : {}),
        ...(exported ? { result_json: JSON.stringify(exported) } : {}),
        ...(isAuto ? { labels_json: JSON.stringify(autoLabels) } : {}),
        ...(!credit?.known && note ? { scan_note: note } : {}),
        ...(view ? {
          normal_x: view.toward[0], normal_y: view.toward[1], normal_z: view.toward[2],
          up_x: view.up[0], up_y: view.up[1], up_z: view.up[2],
        } : {}),
      };
      const s = session();
      let res: Response;
      if (s) {
        res = await s.post("/api/3d/export", fields, ctrl.signal);
      } else {
        // The model is not loaded (only tables and data can be chosen then): no mesh_id is needed
        const fd = new FormData();
        for (const [k, v] of Object.entries(fields)) fd.append(k, String(v));
        res = await fetch(`${API_URL}/api/3d/export`, { method: "POST", body: fd, signal: ctrl.signal });
        if (!res.ok) {
          const body = await res.json().catch(() => null);
          throw new ApiError(res.status, body?.detail || `Fel ${res.status}`);
        }
      }
      const blob = await res.blob();
      if (ctrl.signal.aborted) return;
      // The model or the analysis changed while the files were computed: they belong to the previous one
      if (current.current.meshId !== startMesh || current.current.exported !== startExported) return;
      download(blob, fileNameFrom(res.headers.get("Content-Disposition")));
      const label = new Map((items ?? []).map(it => [it.id, it.label]));
      setSkipped(headerText(res.headers.get("X-Export-Skipped") ?? "").split(";").flatMap(part => {
        const [id, ...rest] = part.split(":");
        return id.trim() ? [{ label: label.get(id.trim()) ?? id.trim(), reason: rest.join(":").trim() }] : [];
      }));
    } catch (e) {
      if (!isAbort(e) && !ctrl.signal.aborted) alert(e instanceof Error ? e.message : "Exporten misslyckades.");
    } finally {
      if (abortRef.current === ctrl) abortRef.current = null;
      setBusy(false);
    }
  };

  // "Vad innehåller filerna?": the files that can be chosen now, then the ZIP and the stone report
  const extra = (id: string) => (items ?? []).find(it => it.id === id);
  const bundle = catalogue?.bundle ?? extra("bundle_zip");
  const report = onCreateReport ? catalogue?.stone_report ?? extra("stone_report_link") : undefined;
  const explained: { id: string; label: string; explanation: string }[] = [
    ...available,
    ...(bundle ? [{ ...bundle, id: "bundle_zip" }] : []),
    ...(report ? [{ ...report, id: "stone_report_link" }] : []),
  ];
  const ds = credit?.known ? credit.dataset : null;
  const typed = signum.trim();
  const fileSigna = credit?.file?.signa?.length ? credit.file.signa : credit?.file?.signum ? [credit.file.signum] : [];
  // A part stone (Sö 137A) counts as the stone, as src/scan_sources.lookup reads it
  const typedKey = foldSignum(typed);
  const signumDiffers = fileSigna.length > 0 && !!typed
    && !fileSigna.some(sg => [typedKey, typedKey.replace(/[ab]$/, "")].includes(foldSignum(sg)));
  const bothAnalyses = !!autoResult && !!result;
  const resultIsSelection = !!result?.provenance?.parameters && "selection" in result.provenance.parameters;
  const exportedText = isAuto
    ? "hela den automatiska analysen, med dina etiketter"
    : resultIsSelection ? "urvalet ur den automatiska analysen, som visas under resultaten" : "mätningen som visas under resultaten";
  const otherText = isAuto
    ? (resultIsSelection ? "urvalet under resultaten" : "mätningen under resultaten")
    : "hela den automatiska analysen";

  return (
    <div id="exportera" className="liquid-glass-island rounded-[32px] p-6 shadow-sm border border-white/50 space-y-4 scroll-mt-6">
      <div>
        <h3 className="text-lg font-bold text-slate-900">Exportera</h3>
        <p className="text-xs text-slate-500 font-medium mt-1 max-w-2xl">
          Välj vad du vill ladda ned. Allt räknas fram ur samma skanning och samma mätning som visas här, och varje fil
          anger vem som har skannat stenen.
        </p>
      </div>

      {itemsError ? (
        <p className="text-xs text-amber-800">
          <span>Exportvalen kunde inte hämtas från analysmotorn.</span>{" "}
          <button type="button" onClick={() => setRetry(r => r + 1)} className="underline font-semibold">Försök igen</button>
        </p>
      ) : !items ? (
        <p className="text-xs text-slate-500">Hämtar exportvalen …</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {GROUPS.map(([group, title]) => {
            const list = available.filter(it => it.group === group);
            if (list.length === 0) return null;
            return (
              <div key={group} className="space-y-1.5">
                <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500">{catalogue?.groups?.[group] ?? title}</div>
                {list.map(it => (
                  <label key={it.id} className="flex items-start gap-2 text-xs text-slate-700 cursor-pointer">
                    <input type="checkbox" checked={chosenSet.has(it.id)} onChange={() => toggle(it.id)} disabled={busy} className="mt-0.5" />
                    <span>
                      <span>{it.label}</span>
                      {TERM[it.id] && <InfoTip text={GLOSSARY[TERM[it.id]]} />}
                      {" "}
                      <span translate="no" className="text-[10px] font-mono bg-slate-100 text-slate-600 rounded px-1 whitespace-nowrap">
                        {FILE_COUNT[it.id] && it.formats.length === 1 ? `${FILE_COUNT[it.id]} × ${it.formats[0]}` : it.formats.join("+")}
                      </span>
                    </span>
                  </label>
                ))}
              </div>
            );
          })}
        </div>
      )}

      {items && hiddenCount > 0 && (!meshLoaded || !exported) && (
        <p className="text-[11px] text-slate-500">
          {!meshLoaded ? "Fler val när 3D-modellen är inläst." : "Fler val när du har mätt med Ett klick eller automatiskt."}
        </p>
      )}

      {bothAnalyses && exported && (
        <p className="text-[11px] text-slate-700">
          <span>Exporteras:</span> <span className="font-semibold">{exportedText}</span>.{" "}
          {onChooseAnalysis && (
            <button type="button" disabled={busy} onClick={() => onChooseAnalysis(isAuto ? "result" : "auto")}
              className="underline font-semibold text-[#b7410e] disabled:opacity-40">
              <span>Exportera i stället</span> <span>{otherText}</span>
            </button>
          )}
        </p>
      )}

      {isAuto && (
        <p className="text-[11px] text-slate-500">
          Den automatiska analysen exporteras med dina etiketter: snitt du märkt som uteslutna räknas inte i
          sammanfattningen och figurerna, som i stenrapporten.
        </p>
      )}

      {ds ? (
        <div className="text-[11px] text-slate-500 space-y-0.5">
          <p>
            <span>Skanning:</span>{" "}
            <span translate="no">{credit?.file?.name}</span>{" "}
            <span>är en publicerad fil i</span> <span translate="no">{ds.short}</span>.
          </p>
          <p>
            <span>Skannad av</span> <span translate="no">{ds.scanned_by}</span>{" "}
            {ds.institution ? <span translate="no">({ds.institution})</span> : <span>(institutionen anges inte i datamängden)</span>}
            <span>, inom</span> <span translate="no">{ds.project}</span>.{" "}
            <span>Licens:</span>{" "}
            {ds.license_url
              ? <a href={ds.license_url} target="_blank" rel="noopener noreferrer" className="underline" translate="no">{ds.license}</a>
              : <span translate="no">{ds.license}</span>}.{" "}
            <span>DOI:</span>{" "}
            <a href={ds.url} target="_blank" rel="noopener noreferrer" className="underline" translate="no">{ds.doi}</a>.{" "}
            <span>{credit?.computed_note}</span>
          </p>
          {credit?.match === "filnamn och storlek" && (
            <p className="text-amber-800">Igenkänd på filnamn och storlek, inte på kontrollsumma; kontrollera att det är originalfilen.</p>
          )}
          {signumDiffers && (
            <p className="text-amber-800">
              <span>Filen är skanningen av</span> <span translate="no">{fileSigna.join(" och ")}</span>
              <span>, men signumet ovan är</span> <span translate="no">{typed}</span>.
            </p>
          )}
        </div>
      ) : (meshLoaded || exported) && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 space-y-1.5">
          <p className="text-[11px] text-amber-900">
            Vitki känner inte igen skanningsfilen som en av de öppna datamängder appen känner till. Ange vem som skannat
            stenen, institution, licens och DOI; texten följer med i filerna.
          </p>
          <input value={scanNote} onChange={e => setScanNote(e.target.value)} maxLength={MAX_SCAN_NOTE} disabled={busy}
            placeholder="Skannad av, institution, licens, DOI"
            className="w-full liquid-glass-input-wrapper rounded-lg px-3 py-1.5 text-xs outline-none" />
        </div>
      )}

      <div className="flex flex-wrap items-center gap-3">
        <button type="button" onClick={runExport} disabled={busy || chosen.length === 0}
          className="bg-slate-900 hover:bg-black text-white text-xs font-bold rounded-xl px-4 py-2 disabled:opacity-40 flex items-center gap-2">
          {busy && <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />}
          <span>{busy ? "Räknar fram filerna …" : zipAnyway ? "Ladda ned 1 fil som ZIP med README.txt" : fileCount === 1 ? "Ladda ned 1 fil" : `Ladda ned ${fileCount} filer som ZIP`}</span>
        </button>
        {busy && (
          <button type="button" onClick={cancel} className="text-xs font-semibold text-slate-600 hover:text-slate-900 underline">
            Avbryt
          </button>
        )}
        {busy && anyImage && <span className="text-[11px] text-slate-500">(första gången kan det ta upp till en halv minut)</span>}
        {onCreateReport && (
          <button type="button" onClick={onCreateReport} className="text-xs text-slate-600 hover:text-slate-900">
            <span>Allt med figurtexter i ett dokument:</span> <span className="font-semibold text-[#b7410e] underline">Skapa stenrapport</span>
          </button>
        )}
      </div>

      {skipped.length > 0 && (
        <div className="text-[11px] text-amber-900">
          <span>Hoppades över, eftersom underlaget saknas:</span>
          <ul className="list-disc ml-5">
            {skipped.map((s, i) => <li key={i}><span>{s.label}</span>{s.reason && <> (<span>{s.reason}</span>)</>}</li>)}
          </ul>
        </div>
      )}

      {items && (
        <details className="text-xs text-slate-600">
          <summary className="cursor-pointer font-semibold text-xs">Vad innehåller filerna?</summary>
          <div className="mt-3 space-y-3 max-w-3xl">
            {explained.map(it => (
              <div key={it.id}>
                <div className="font-semibold text-slate-800">{it.label}</div>
                <p className="leading-relaxed">{it.explanation}</p>
              </div>
            ))}
            <p className="leading-relaxed">
              {catalogue?.readme_intro ?? "Koordinaterna i filerna är millimeter i 3D-modellen, flyttad så att mitten av dess omslutande låda ligger i origo. De är inte originalfilens koordinater och inte geografiska."}
            </p>
            <p className="leading-relaxed">
              {catalogue?.caveat ?? `Måtten beskriver hur spåren är huggna, men det är inte visat att de skiljer ristare åt. Mät minst ${MIN_RUNES_DESCRIBE} runor för att beskriva en sten och minst ${MIN_RUNES_COMPARE} för att jämföra stenar.`}
            </p>
          </div>
        </details>
      )}
    </div>
  );
}
