/* eslint-disable @next/next/no-img-element */
"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import ReactCrop, { type PercentCrop } from "react-image-crop";
import "react-image-crop/dist/ReactCrop.css";
import { useAnalysis } from "@/components/AnalysisContext";
import { db, type GrooveSummaryLite, type PaleographicCrop, type ProjectData, type TwoDSourceKind } from "@/lib/db";
import type { KSamsokResult } from "@/lib/ksamsok";
import { API_URL } from "@/lib/api";
import { canvasToBlob, drawScaled, persistentDataURL } from "@/lib/images";
import { RUNE_TAGS, UNKNOWN_RUNE_TAG } from "@/lib/runes";
import { rundata, type Inscription } from "@/lib/rundata";

const ANALYSIS_MAX_SIDE = 2048; // Gemini downscales larger images anyway
const THUMB_MAX_SIDE = 256;
const FEATURE_MAX_SIDE = 512;
// Automatic crops are many: smaller thumbnails and rounded vectors keep a project under the 1 MB limit
const AUTO_THUMB_MAX_SIDE = 128;
const MAX_AUTO_CROPS = 40;

interface DetectedRune {
  box: number[]; // [x0, y0, x1, y1] as fractions of the image
  tag: string;
  translit: string;
  confidence: number;
  selected: boolean;
  origin: "ai" | "3d";
}

const SOURCE_LABEL: Record<TwoDSourceKind, string> = {
  upload: "Uppladdad bild",
  ksamsok: "Bild från K-samsök",
  "3d-snapshot": "Ögonblicksbild från 3D",
  "3d-relief": "Relief ur 3D-skanningen",
  "groove-map": "Ristningskarta från 3D-analysen",
  rti: "Vy från RTI-visaren",
};

interface CropWithStone {
  crop: PaleographicCrop;
  projectId: string;
  signum: string;
}

function cosine(a: number[], b: number[]) {
  let dot = 0, na = 0, nb = 0;
  for (let i = 0; i < a.length; i++) { dot += a[i] * b[i]; na += a[i] * a[i]; nb += b[i] * b[i]; }
  return na && nb ? dot / Math.sqrt(na * nb) : 0;
}

const fmt = (v: number, d = 1) => v.toFixed(d).replace(".", ",");

// Images and rune forms: a tab on the 3D page. A photo, an RTI view, a relief or the groove map from the 3D analysis;
// rune crops are compared by shape (src/graphemes.py), and Rundata's style group is shown beside the image. The AI style
// assessment and the AI reading were removed 2026-10-20 (METHODS.md 8 and 12): the reading returned mostly blanks, and
// the style assessment got the exact group right in 35 % of 57 tested stones.
export default function TwoDAnalysis() {
  const [crop, setCrop] = useState<PercentCrop>();
  const [completedCrop, setCompletedCrop] = useState<PercentCrop | null>(null);
  const [brightness, setBrightness] = useState(100);
  const [contrast, setContrast] = useState(100);
  const [channel, setChannel] = useState<"all" | "r" | "g" | "b">("all");
  const [cropTag, setCropTag] = useState(RUNE_TAGS[4].tag);
  const [loading, setLoading] = useState(false);  // a K-samsök image is being fetched
  const [savingCrop, setSavingCrop] = useState(false);
  const [detected, setDetected] = useState<DetectedRune[] | null>(null);
  const [detectNote, setDetectNote] = useState<string | null>(null);
  const [savingAuto, setSavingAuto] = useState(false);

  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<KSamsokResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  const [allCrops, setAllCrops] = useState<CropWithStone[]>([]);
  const [comparingTo, setComparingTo] = useState<CropWithStone | null>(null);
  const [sameTagOnly, setSameTagOnly] = useState(true);
  const [rundataRec, setRundataRec] = useState<Inscription | null>(null);

  const imgRef = useRef<HTMLImageElement>(null);
  const {
    latest2DImage: imagePreview, setLatest2DImage: setImagePreview,
    latest2DFile: file, setLatest2DFile: setFile,
    latest2DSource: source, setLatest2DSource: setSource,
    latest3DMeta, setLatest3DMeta,
    activeProjectId, setActiveProjectId,
  } = useAnalysis();
  const signum = latest3DMeta.text;
  const sourceKind: TwoDSourceKind = source?.kind ?? "upload";
  const isBinarySource = sourceKind === "groove-map" || sourceKind === "3d-snapshot" || sourceKind === "3d-relief";

  // ---- data loading ------------------------------------------------------------------------
  const loadAllCrops = async () => {
    const projects = await db.getProjects();
    setAllCrops(projects.flatMap(p => (p.paleographicCrops ?? []).map(crop => ({
      crop, projectId: p.id, signum: p.metaText || p.name,
    }))));
  };

  useEffect(() => {
    let cancelled = false;
    db.getProjects().then(projects => {
      if (cancelled) return;
      setAllCrops(projects.flatMap(p => (p.paleographicCrops ?? []).map(crop => ({
        crop, projectId: p.id, signum: p.metaText || p.name,
      }))));
    });
    return () => { cancelled = true; };
  }, [activeProjectId]);

  useEffect(() => {
    if (!signum) return;
    let cancelled = false;
    const timer = setTimeout(() => {
      rundata.inscription(signum).then(r => { if (!cancelled) setRundataRec(r); }).catch(() => { if (!cancelled) setRundataRec(null); });
    }, 400);
    return () => { cancelled = true; clearTimeout(timer); };
  }, [signum]);
  const rundataForSignum = signum && rundataRec && rundataRec.signum ? rundataRec : null;

  // ---- image processing --------------------------------------------------------------------
  // Region of the natural image covered by a percent crop
  const regionOf = (img: HTMLImageElement, pc: PercentCrop | null) => {
    if (!pc || pc.width <= 0 || pc.height <= 0) return undefined;
    return {
      x: (pc.x / 100) * img.naturalWidth, y: (pc.y / 100) * img.naturalHeight,
      w: (pc.width / 100) * img.naturalWidth, h: (pc.height / 100) * img.naturalHeight,
    };
  };

  // The image as the user sees it (brightness, contrast, colour channel), scaled down
  const processedCanvas = (maxSide: number, pc: PercentCrop | null): HTMLCanvasElement | null => {
    const img = imgRef.current;
    if (!img) return null;
    const raw = drawScaled(img, maxSide, regionOf(img, pc));
    const out = document.createElement("canvas");
    out.width = raw.width;
    out.height = raw.height;
    const ctx = out.getContext("2d")!;
    ctx.filter = `brightness(${brightness}%) contrast(${contrast}%)`;
    ctx.drawImage(raw, 0, 0);
    if (channel !== "all") {
      const data = ctx.getImageData(0, 0, out.width, out.height);
      const k = channel === "r" ? 0 : channel === "g" ? 1 : 2;
      for (let i = 0; i < data.data.length; i += 4) {
        const v = data.data[i + k];
        data.data[i] = data.data[i + 1] = data.data[i + 2] = v;
      }
      ctx.putImageData(data, 0, 0);
    }
    return out;
  };

  const resetImageState = () => {
    setDetected(null);
    setDetectNote(null);
    setCrop(undefined);
    setCompletedCrop(null);
    setBrightness(100);
    setContrast(100);
    setChannel("all");
  };

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;
    setFile(selectedFile);
    setImagePreview(URL.createObjectURL(selectedFile));
    setSource({ kind: "upload", description: selectedFile.name });
    resetImageState();
  };

  // ---- projects ----------------------------------------------------------------------------
  const resolveProjectId = async () => {
    if (activeProjectId) return activeProjectId;
    if (signum) {
      const existing = await db.getProjectBySignum(signum);
      if (existing) return existing.id;
    }
    return null;
  };

  const newProjectFields = (fallbackName: string): Partial<ProjectData> => ({
    name: signum || (file ? file.name : fallbackName),
    fileName: file ? file.name : "Bild",
    metaStone: latest3DMeta.stone || "Okänd",
    metaWeathering: latest3DMeta.weathering || "Låg",
    metaText: signum || "",
    slices: [],
  });

  // The image goes into the project (and so into the stone report's picture section)
  const handleSaveProject = async () => {
    if (!imagePreview) return;
    const projectId = await resolveProjectId();
    const twoDImage = await persistentDataURL(imagePreview);
    const update: Partial<ProjectData> = projectId
      ? { id: projectId, twoDImage, ...(signum ? { metaText: signum, name: signum } : {}) }
      : { ...newProjectFields("Nytt projekt (bild)"), twoDImage };
    const saved = await db.saveProject(update);
    setActiveProjectId(saved.id);
    alert(`Bilden sparad i projektet: ${saved.name}`);
  };

  // Groove measurements inside the crop, when the image is a groove map from the 3D analysis
  const grooveSummaryFor = (pc: PercentCrop): GrooveSummaryLite | undefined => {
    if (source?.kind !== "groove-map" || !source.autoSlices) return undefined;
    const [x0, y0, x1, y1] = [pc.x / 100, pc.y / 100, (pc.x + pc.width) / 100, (pc.y + pc.height) / 100];
    const inside = source.autoSlices.filter(s => s.x >= x0 && s.x <= x1 && s.y >= y0 && s.y <= y1);
    if (inside.length === 0) return undefined;
    const mean = (k: string) => inside.reduce((a, s) => a + s.metrics[k], 0) / inside.length;
    const angleMean = mean("apex_vinkel_deg");
    const sd = inside.length > 1
      ? Math.sqrt(inside.reduce((a, s) => a + (s.metrics.apex_vinkel_deg - angleMean) ** 2, 0) / (inside.length - 1)) : 0;
    return { n: inside.length, angle_mean: angleMean, angle_sd: sd, depth_mean: mean("spårdjup_mm"), width_mean: mean("spårbredd_mm") };
  };

  // A rune crop with its form description; thumbSide is smaller for automatic crops
  const buildCrop = async (pc: PercentCrop, tag: string, extra: Partial<PaleographicCrop> = {},
                           thumbSide = THUMB_MAX_SIDE): Promise<PaleographicCrop> => {
    const thumb = processedCanvas(thumbSide, pc);
    const featureCanvas = processedCanvas(FEATURE_MAX_SIDE, pc);
    if (!thumb || !featureCanvas) throw new Error("Kunde inte läsa utsnittet.");
    const thumbnail = thumb.toDataURL(isBinarySource ? "image/png" : "image/jpeg", thumbSide < THUMB_MAX_SIDE ? 0.7 : 0.8);
    const res = await fetch(`${API_URL}/api/2d/extract_features`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ image_base64: featureCanvas.toDataURL("image/png") }),
    });
    if (!res.ok) throw new Error((await res.json().catch(() => null))?.detail || "Kunde inte beskriva runformen.");
    const features = await res.json();
    const vector: number[] = features.feature_vector;
    return {
      id: crypto.randomUUID(),
      tag,
      imageBase64: thumbnail,
      coordinates: [pc.x / 100, pc.y / 100, (pc.x + pc.width) / 100, (pc.y + pc.height) / 100],
      featureVector: extra.auto ? vector.map(v => Math.round(v * 1000) / 1000) : vector,
      featureVersion: features.feature_version,
      formPng: features.form_png,
      sourceKind,
      grooveSummary: grooveSummaryFor(pc),
      createdAt: new Date().toISOString(),
      ...extra,
    };
  };

  const storeCrops = async (crops: PaleographicCrop[]) => {
    const projectId = await resolveProjectId();
    let update: Partial<ProjectData>;
    if (projectId) {
      const existing = await db.getProject(projectId);
      update = { id: projectId, paleographicCrops: [...(existing?.paleographicCrops ?? []), ...crops] };
    } else {
      update = { ...newProjectFields("Nytt projekt (runformer)"), paleographicCrops: crops };
    }
    const saved = await db.saveProject(update);
    setActiveProjectId(saved.id);
    await loadAllCrops();
  };

  const handleSaveCrop = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!completedCrop || completedCrop.width <= 0 || completedCrop.height <= 0) {
      alert("Markera först en runa genom att dra en ruta i bilden.");
      return;
    }
    setSavingCrop(true);
    try {
      await storeCrops([await buildCrop(completedCrop, cropTag)]);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Kunde inte spara utsnittet.");
    } finally {
      setSavingCrop(false);
    }
  };

  // ---- automatic rune crops ----------------------------------------------------------------
  // Only for the groove map from the 3D analysis: the runes the analysis itself recognised. (The AI marking of runes in
  // other images was removed 2026-10-20, together with the AI reading.)
  const handleDetectRunes = () => {
    if (!imagePreview) return;
    setDetected(null);
    setDetectNote(null);
    if (source?.kind === "groove-map" && source.runeBoxes?.length) {
      setDetected(source.runeBoxes.map(r => ({ box: r.box, tag: UNKNOWN_RUNE_TAG, translit: "", confidence: 100,
        selected: true, origin: "3d" as const })));
      setDetectNote(`${source.runeBoxes.length} runor som 3D-analysen känt igen. Analysen vet inte vilken runa det är, så ange det i listan (eller spara dem som obestämda och ange det senare).`);
      return;
    }
    setDetectNote("Automatiska runutsnitt finns bara för ristningskartan från 3D-analysen. Rita utsnitten själv i andra bilder.");
  };

  const handleSaveDetected = async () => {
    const chosen = (detected ?? []).filter(d => d.selected).slice(0, MAX_AUTO_CROPS);
    if (!chosen.length) return;
    setSavingAuto(true);
    try {
      const crops: PaleographicCrop[] = [];
      for (const d of chosen) {
        const pc: PercentCrop = { unit: "%", x: d.box[0] * 100, y: d.box[1] * 100,
          width: (d.box[2] - d.box[0]) * 100, height: (d.box[3] - d.box[1]) * 100 };
        try {
          crops.push(await buildCrop(pc, d.tag, { auto: d.origin, confidence: d.origin === "ai" ? d.confidence : undefined },
            AUTO_THUMB_MAX_SIDE));
        } catch {
          // a box without a recognisable form (e.g. only weathering) is skipped
        }
      }
      if (!crops.length) throw new Error("Ingen av rutorna innehöll en runform som kunde beskrivas.");
      await storeCrops(crops);
      setDetected(null);
      setDetectNote(`${crops.length} runutsnitt sparade i projektet${crops.length < chosen.length ? ` (${chosen.length - crops.length} rutor saknade en tydlig runform)` : ""}.`);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Kunde inte spara runutsnitten.");
    } finally {
      setSavingAuto(false);
    }
  };

  // ---- K-samsök ----------------------------------------------------------------------------
  const searchKSamsok = async (query: string) => {
    if (!query) return;
    setIsSearching(true);
    try {
      const res = await fetch(`/api/ksamsok?q=${encodeURIComponent(query)}`);
      const data = await res.json();
      setSearchResults(data.results ?? []);
      if (!data.results?.length) alert("Inga bilder hittades i K-samsök.");
    } catch {
      alert("Fel vid sökning i K-samsök.");
    } finally {
      setIsSearching(false);
    }
  };

  const loadKSamsokImage = async (item: KSamsokResult) => {
    setLoading(true);
    try {
      const res = await fetch(`/api/proxy-image?w=3000&url=${encodeURIComponent(item.url)}`);
      if (!res.ok) throw new Error(res.status === 504 ? "Bildservern svarar inte just nu." : "Bilden kunde inte hämtas.");
      const blob = await res.blob();
      setImagePreview(URL.createObjectURL(blob));
      setFile(new File([blob], "ksamsok.jpg", { type: blob.type }));
      setSource({ kind: "ksamsok", description: item.description, url: item.url });
      resetImageState();
      // Only set a signum if the search text actually contains one known to Rundata
      if (!signum) {
        const found = await rundata.find(searchQuery).catch(() => []);
        if (found.length) setLatest3DMeta({ ...latest3DMeta, text: found[0].signum });
      }
      setSearchResults([]);
    } catch (e) {
      alert(`${e instanceof Error && e.message ? e.message : "Bilden kunde inte hämtas."} (Bilderna i K-samsök ligger hos Riksantikvarieämbetet och andra arkiv.)`);
    } finally {
      setLoading(false);
    }
  };

  // ---- rune form comparison ----------------------------------------------------------------
  const comparison = useMemo(() => {
    if (!comparingTo?.crop.featureVector) return [];
    const ref = comparingTo.crop;
    return allCrops
      .filter(c => c.crop.id !== ref.id && c.crop.featureVector && c.crop.featureVersion === ref.featureVersion)
      .filter(c => !sameTagOnly || c.crop.tag === ref.tag)
      .map(c => ({ ...c, similarity: cosine(ref.featureVector!, c.crop.featureVector!) }))
      .sort((a, b) => b.similarity - a.similarity)
      .slice(0, 12);
  }, [comparingTo, allCrops, sameTagOnly]);

  const projectCrops = allCrops.filter(c => c.projectId === activeProjectId);

  return (
    <>
      <svg width="0" height="0" className="absolute pointer-events-none">
        <filter id="channel-r"><feColorMatrix type="matrix" values="1 0 0 0 0  1 0 0 0 0  1 0 0 0 0  0 0 0 1 0" /></filter>
        <filter id="channel-g"><feColorMatrix type="matrix" values="0 1 0 0 0  0 1 0 0 0  0 1 0 0 0  0 0 0 1 0" /></filter>
        <filter id="channel-b"><feColorMatrix type="matrix" values="0 0 1 0 0  0 0 1 0 0  0 0 1 0 0  0 0 0 1 0" /></filter>
      </svg>
      <div className="flex flex-col w-full">
        <div className="mb-8">
          <h2 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">Bilder och runformer</h2>
          <p className="text-slate-600 text-[16px] leading-relaxed max-w-3xl font-medium mb-6">
            Ett foto, en vy från RTI-visaren, en relief eller ristningskartan från 3D-analysen. Rita runutsnitt och jämför
            deras form med samma runa på andra stenar. Ingen AI: stilgruppen hämtas ur Rundata.
          </p>

          <div className="w-full max-w-3xl bg-white p-4 rounded-[24px] shadow-sm border border-slate-200 space-y-3">
            <form onSubmit={e => { e.preventDefault(); searchKSamsok(searchQuery); }} className="flex gap-2">
              <input value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
                placeholder="Sök bilder i K-samsök (t.ex. 'U 11' eller 'runsten Uppland')"
                className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-sm font-semibold text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#b7410e]/50" />
              <button type="submit" disabled={isSearching}
                className="px-5 py-3 bg-[#b7410e] hover:bg-[#96350b] text-white font-bold text-sm rounded-xl disabled:opacity-50">
                {isSearching ? "Söker..." : "Sök bild"}
              </button>
              {signum && (
                <button type="button" onClick={() => { setSearchQuery(signum); searchKSamsok(signum); }}
                  className="px-4 py-3 bg-white border border-slate-300 hover:border-slate-900 text-xs font-bold rounded-xl whitespace-nowrap">
                  Bilder för {signum}
                </button>
              )}
            </form>
            {loading && <p className="text-xs text-slate-500">Hämtar bilden …</p>}
            {searchResults.length > 0 && (
              <div className="border-t border-slate-100 pt-3">
                <p className="text-xs font-bold text-slate-500 mb-2 uppercase tracking-wider">Sökresultat ({searchResults.length})</p>
                <div className="flex gap-3 overflow-x-auto pb-2">
                  {searchResults.map((res, i) => (
                    <button key={i} type="button" onClick={() => loadKSamsokImage(res)}
                      className="flex-shrink-0 w-24 h-24 rounded-xl overflow-hidden border-2 border-transparent hover:border-[#b7410e] relative group bg-slate-100">
                      <Thumbnail url={res.thumbnail} />
                      <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 flex items-center justify-center p-2">
                        <span className="text-[9px] text-white font-bold text-center leading-tight line-clamp-3">{res.description}</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left: image */}
          <div className="liquid-glass-island rounded-[36px] p-8 flex flex-col items-center border border-white/50 relative h-fit">
            {!imagePreview ? (
              <label className="flex flex-col items-center justify-center w-full h-[400px] border-2 border-dashed border-slate-300 rounded-3xl cursor-pointer hover:bg-slate-50/50 group">
                <div className="flex flex-col items-center text-slate-500 group-hover:text-[#b7410e]">
                  <p className="mb-2 text-sm font-semibold">Klicka eller dra hit en bild</p>
                  <p className="text-xs">PNG, JPG eller WEBP (max 20 MB). Stora bilder skalas ner före analysen.</p>
                </div>
                <input type="file" className="hidden" accept="image/*" onChange={handleImageChange} />
              </label>
            ) : (
              <div className="w-full flex flex-col items-center">
                <div className="w-full flex items-center justify-between mb-2 text-xs">
                  <span className="font-bold text-slate-600">{SOURCE_LABEL[sourceKind]}{source?.description ? ` · ${source.description}` : ""}</span>
                  {source?.kind === "groove-map" && (
                    <span className="text-emerald-700 font-semibold">Runutsnitt får huggspårsmått ur 3D-analysen</span>
                  )}
                </div>
                <div className="relative w-full rounded-3xl overflow-hidden bg-slate-900/5 flex items-center justify-center p-4">
                  <ReactCrop crop={crop} onChange={(_, pc) => setCrop(pc)} onComplete={(_, pc) => setCompletedCrop(pc)} className="max-h-[500px] relative">
                    <img ref={imgRef} src={imagePreview} alt="Runsten"
                      style={{ filter: `brightness(${brightness}%) contrast(${contrast}%) ${channel !== "all" ? `url(#channel-${channel})` : ""}` }}
                      className="w-auto h-auto max-h-[460px] object-contain shadow-sm" />
                    {detected?.map((d, i) => (
                      <button key={`det-${i}`} type="button" title={`${i + 1}: ${d.tag}${d.origin === "ai" ? ` (${d.confidence} %)` : ""}`}
                        onClick={e => { e.stopPropagation(); setDetected(ds => ds && ds.map((x, j) => j === i ? { ...x, selected: !x.selected } : x)); }}
                        className={`absolute z-40 rounded-sm border ${d.selected ? "border-emerald-500 bg-emerald-400/15" : "border-slate-400 border-dashed bg-transparent"}`}
                        style={{ left: `${d.box[0] * 100}%`, top: `${d.box[1] * 100}%`, width: `${(d.box[2] - d.box[0]) * 100}%`, height: `${(d.box[3] - d.box[1]) * 100}%` }}>
                        <span className={`absolute -top-3.5 left-0 text-[9px] font-bold px-1 rounded ${d.selected ? "bg-emerald-600 text-white" : "bg-slate-400 text-white"}`}>
                          {i + 1}{d.translit ? ` ${d.translit}` : ""}
                        </span>
                      </button>
                    ))}
                  </ReactCrop>
                  <label className="absolute top-4 right-4 bg-slate-900/80 hover:bg-black text-white text-xs font-bold px-3 py-1.5 rounded-full cursor-pointer z-10">
                    Byt bild
                    <input type="file" className="hidden" accept="image/*" onChange={handleImageChange} />
                  </label>
                </div>

                <div className="flex flex-col gap-4 mt-6 w-full px-2">
                  <div className="flex gap-6 w-full">
                    {([["Ljusstyrka", brightness, setBrightness, 50, 200], ["Kontrast", contrast, setContrast, 50, 250]] as const).map(([label, value, set, min, max]) => (
                      <div key={label} className="flex-1 flex flex-col gap-2">
                        <div className="flex justify-between items-center">
                          <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">{label}</label>
                          <span className="text-[10px] font-bold text-slate-700 bg-slate-100 px-2 py-0.5 rounded-full">{value}%</span>
                        </div>
                        <input type="range" min={min} max={max} value={value} onChange={e => set(Number(e.target.value))} className="w-full accent-[#b7410e]" />
                      </div>
                    ))}
                  </div>
                  <div className="flex gap-2 bg-slate-100 p-1.5 rounded-xl border border-slate-200">
                    {([["all", "RGB"], ["r", "Röd"], ["g", "Grön"], ["b", "Blå"]] as const).map(([c, label]) => (
                      <button key={c} type="button" onClick={() => setChannel(c)}
                        className={`flex-1 py-1.5 text-xs font-bold rounded-lg ${channel === c ? "bg-white shadow-sm text-slate-800" : "text-slate-500 hover:bg-slate-200/50"}`}>{label}</button>
                    ))}
                  </div>
                  <p className="text-[11px] text-slate-500">
                    Dra en ruta i bilden för att spara ett runutsnitt.
                  </p>
                </div>
              </div>
            )}

            <form onSubmit={handleSaveCrop} className="w-full mt-4 flex gap-2">
              <select value={cropTag} onChange={e => setCropTag(e.target.value)}
                className="flex-1 bg-white/70 border border-slate-200 rounded-xl px-3 py-3 text-sm font-semibold text-slate-800 outline-none">
                {["Långkvist", "Kortkvist", "Stungna", "Övrigt"].map(g => (
                  <optgroup key={g} label={g}>
                    {RUNE_TAGS.filter(r => r.group === g).map(r => <option key={r.tag} value={r.tag}>{r.tag}{r.name ? ` (${r.name})` : ""}</option>)}
                  </optgroup>
                ))}
              </select>
              <button type="submit" disabled={!imagePreview || savingCrop}
                className="px-5 py-3 bg-white border border-slate-200 hover:border-[#b7410e]/40 text-[#b7410e] font-bold text-sm rounded-xl disabled:opacity-40 whitespace-nowrap">
                {savingCrop ? "Sparar..." : "Spara runutsnitt"}
              </button>
            </form>

            <div className="w-full mt-4 rounded-2xl border border-slate-200 bg-white/60 p-4">
              <div className="flex items-center justify-between gap-3">
                <div className="text-xs text-slate-600">
                  <span className="font-bold text-slate-800">Automatiska runutsnitt.</span>{" "}
                  {source?.kind === "groove-map" && source.runeBoxes?.length
                    ? "Runorna som 3D-analysen känt igen klipps ut direkt."
                    : "Bara för ristningskartan från 3D-analysen; i andra bilder ritar du utsnitten själv."}
                </div>
                <button type="button" onClick={handleDetectRunes} disabled={!imagePreview || source?.kind !== "groove-map"}
                  className="px-4 py-2 bg-slate-900 hover:bg-black text-white font-bold text-xs rounded-xl disabled:opacity-40 whitespace-nowrap">
                  Hitta runorna
                </button>
              </div>
              {detectNote && <p className="text-[11px] text-slate-600 mt-2">{detectNote}</p>}
              {detected && detected.length > 0 && (
                <>
                  <div className="mt-3 max-h-56 overflow-y-auto divide-y divide-slate-100">
                    {detected.map((d, i) => (
                      <div key={i} className="flex items-center gap-2 py-1 text-xs">
                        <input type="checkbox" checked={d.selected} className="accent-[#b7410e]"
                          onChange={() => setDetected(ds => ds && ds.map((x, j) => j === i ? { ...x, selected: !x.selected } : x))} />
                        <span className="w-6 text-slate-500">{i + 1}</span>
                        <select value={d.tag} onChange={e => setDetected(ds => ds && ds.map((x, j) => j === i ? { ...x, tag: e.target.value } : x))}
                          className="flex-1 bg-white border border-slate-200 rounded-lg px-2 py-1">
                          {RUNE_TAGS.map(r => <option key={r.tag} value={r.tag}>{r.tag}</option>)}
                        </select>
                        {d.origin === "ai" && <span className={`w-12 text-right ${d.confidence < 50 ? "text-amber-700" : "text-slate-500"}`}>{d.confidence} %</span>}
                      </div>
                    ))}
                  </div>
                  <div className="flex items-center justify-between mt-3">
                    <span className="text-[11px] text-slate-500">
                      {detected.filter(d => d.selected).length} av {detected.length} valda
                      {detected.filter(d => d.selected).length > MAX_AUTO_CROPS ? ` (högst ${MAX_AUTO_CROPS} sparas åt gången)` : ""}
                    </span>
                    <button type="button" onClick={handleSaveDetected} disabled={savingAuto || !detected.some(d => d.selected)}
                      className="px-4 py-2 bg-white border border-slate-200 hover:border-[#b7410e]/40 text-[#b7410e] font-bold text-xs rounded-xl disabled:opacity-40">
                      {savingAuto ? "Sparar …" : "Spara valda som runutsnitt"}
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Right */}
          <div className="flex flex-col gap-6">
            {projectCrops.length > 0 && (
              <div className="liquid-glass-island rounded-[36px] p-6 border border-white/50">
                <h3 className="text-lg font-bold text-slate-800 mb-1">Runutsnitt i projektet ({projectCrops.length})</h3>
                <p className="text-xs text-slate-500 mb-4">Klicka på ett utsnitt för att jämföra formen med samma runa på andra stenar.</p>
                <div className="grid grid-cols-3 sm:grid-cols-4 gap-3">
                  {projectCrops.map(c => (
                    <button key={c.crop.id} type="button" onClick={() => setComparingTo(c)}
                      className={`flex flex-col bg-white border-2 rounded-2xl overflow-hidden text-left ${comparingTo?.crop.id === c.crop.id ? "border-[#b7410e]" : "border-slate-200 hover:border-[#b7410e]/40"}`}>
                      <div className="w-full h-20 bg-slate-50 flex items-center justify-center p-1.5">
                        <img src={c.crop.imageBase64} alt={c.crop.tag} className="max-w-full max-h-full object-contain" />
                      </div>
                      <div className="px-2 py-1 bg-slate-900 text-white text-[10px] font-bold truncate">{c.crop.tag}</div>
                      {c.crop.grooveSummary && (
                        <div className="px-2 py-1 text-[10px] text-slate-600 bg-emerald-50">
                          {fmt(c.crop.grooveSummary.angle_mean)}° · {c.crop.grooveSummary.n} snitt
                        </div>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {comparingTo && (
              <div className="liquid-glass-island rounded-[36px] p-6 border border-[#b7410e]/20">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-lg font-bold text-slate-800">Mest lika runformer</h3>
                  <button onClick={() => setComparingTo(null)} className="text-xs text-slate-500 hover:text-slate-900">Stäng</button>
                </div>
                <div className="flex gap-4 items-start mb-3">
                  {comparingTo.crop.formPng && <img src={comparingTo.crop.formPng} alt="Normaliserad form" className="w-16 h-16 border border-slate-200 rounded-lg bg-white" />}
                  <div className="text-xs text-slate-600">
                    <div className="font-bold text-slate-900">{comparingTo.crop.tag} · {comparingTo.signum}</div>
                    <label className="flex items-center gap-2 mt-1"><input type="checkbox" checked={sameTagOnly} onChange={e => setSameTagOnly(e.target.checked)} /> Bara samma runa</label>
                    {!comparingTo.crop.featureVersion && <p className="text-amber-700 mt-1">Utsnittet är sparat med en äldre beskrivning – spara det på nytt för att jämföra.</p>}
                  </div>
                </div>
                {comparison.length === 0 ? (
                  <p className="text-sm text-slate-500">Inga jämförbara utsnitt ännu. Spara samma runa från fler stenar.</p>
                ) : (
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                    {comparison.map(c => (
                      <div key={c.crop.id} className="bg-white border border-slate-200 rounded-xl overflow-hidden">
                        <div className="h-20 flex items-center justify-center bg-slate-50 p-1.5">
                          <img src={c.crop.imageBase64} alt={c.crop.tag} className="max-w-full max-h-full object-contain" />
                        </div>
                        <div className="px-2 py-1.5 text-[11px]">
                          <div className="font-bold text-slate-800 truncate">{c.signum}</div>
                          <div className="text-slate-500">{c.crop.tag} · formlikhet {fmt(c.similarity, 2)}</div>
                          {c.crop.grooveSummary && <div className="text-emerald-700">{fmt(c.crop.grooveSummary.angle_mean)}° ({c.crop.grooveSummary.n} snitt)</div>}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                <p className="text-[11px] text-slate-500 mt-3">
                  Formlikheten jämför normaliserade svartvita runformer (kantriktningar, täthet och proportioner). På
                  syntetiska testrunor hittas samma runa i 85 % av fallen; på verkliga foton påverkar skador och vittring.
                  Den är ett underlag för jämförelse, inte ett bevis för samma ristare.
                </p>
              </div>
            )}

            <div className="liquid-glass-island rounded-[36px] p-6 border border-white/50 space-y-4">
              <div>
                <label className="block text-slate-500 text-[10px] font-bold uppercase tracking-wider mb-1">Signum (t.ex. Sö 112)</label>
                <input value={signum} onChange={e => setLatest3DMeta({ ...latest3DMeta, text: e.target.value })}
                  placeholder="Ange signum..." className="w-full liquid-glass-input-wrapper rounded-xl px-4 py-2.5 text-slate-900 text-sm font-semibold outline-none" />
              </div>
              {rundataForSignum && (
                <div className="rounded-xl bg-slate-50 border border-slate-200 px-4 py-3 text-sm text-slate-700">
                  <span className="font-bold text-slate-900">Rundata ({rundataForSignum.signum}):</span>{" "}
                  stilgrupp {rundataForSignum.style ? `${rundataForSignum.style}${rundataForSignum.style_uncertain ? " (osäker)" : ""}` : "ej angiven"}
                  {rundataForSignum.dating ? `, datering ${rundataForSignum.dating}` : ""}. Fakta ur databasen, ingen bildbedömning.
                </div>
              )}
              <p className="text-[11px] text-slate-500">
                Vitki bedömer inte stilgrupp ur bilder: i ett prov på 57 stenar träffade AI:n den exakta stilgruppen i 35 % av
                fallen (METHODS.md 12). Stilgruppen hämtas ur Rundata; saknas den, avgör ornamentiken för ögat.
              </p>
              <button onClick={handleSaveProject} disabled={!imagePreview}
                className="w-full px-6 py-3 bg-[#b7410e] hover:bg-[#9a350b] disabled:opacity-40 text-white font-bold rounded-2xl shadow-lg">
                Spara bilden i projekt
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}


// A search-result thumbnail through the image proxy (archival TIFFs are converted to JPEG); if the archive's
// image server does not answer, a short note replaces the broken image
function Thumbnail({ url }: { url: string }) {
  const [broken, setBroken] = useState(false);
  if (broken) {
    return <span className="absolute inset-0 flex items-center justify-center p-1 text-[9px] text-slate-500 text-center leading-tight">Bilden kunde inte hämtas</span>;
  }
  return (
    <img src={`/api/proxy-image?w=240&url=${encodeURIComponent(url)}`} alt="" className="w-full h-full object-cover" onError={() => setBroken(true)} />
  );
}
