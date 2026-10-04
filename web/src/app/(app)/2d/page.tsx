/* eslint-disable @next/next/no-img-element */
"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import ReactCrop, { type PercentCrop } from "react-image-crop";
import "react-image-crop/dist/ReactCrop.css";
import { useSettings } from "@/components/SettingsContext";
import { useAnalysis } from "@/components/AnalysisContext";
import RuneCanvasBackground from "@/components/RuneCanvasBackground";
import { db, type GrooveSummaryLite, type PaleographicCrop, type ProjectData, type TwoDSourceKind } from "@/lib/db";
import type { KSamsokResult } from "@/lib/ksamsok";
import { API_URL } from "@/lib/api";
import { canvasToBlob, drawScaled, persistentDataURL } from "@/lib/images";
import { RUNE_TAGS } from "@/lib/runes";
import { rundata, type Inscription } from "@/lib/rundata";

const ANALYSIS_MAX_SIDE = 2048; // Gemini downscales larger images anyway
const THUMB_MAX_SIDE = 256;
const FEATURE_MAX_SIDE = 512;

const SOURCE_LABEL: Record<TwoDSourceKind, string> = {
  upload: "Uppladdad bild",
  ksamsok: "Bild från K-samsök",
  "3d-snapshot": "Ögonblicksbild från 3D",
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

export default function TwoDPage() {
  const [loading, setLoading] = useState(false);
  const [crop, setCrop] = useState<PercentCrop>();
  const [completedCrop, setCompletedCrop] = useState<PercentCrop | null>(null);
  const [analyzedCrop, setAnalyzedCrop] = useState<PercentCrop | null>(null);
  const [brightness, setBrightness] = useState(100);
  const [contrast, setContrast] = useState(100);
  const [channel, setChannel] = useState<"all" | "r" | "g" | "b">("all");
  const [cropTag, setCropTag] = useState(RUNE_TAGS[4].tag);
  const [savingCrop, setSavingCrop] = useState(false);

  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<KSamsokResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  const [allCrops, setAllCrops] = useState<CropWithStone[]>([]);
  const [comparingTo, setComparingTo] = useState<CropWithStone | null>(null);
  const [sameTagOnly, setSameTagOnly] = useState(true);
  const [rundataRec, setRundataRec] = useState<Inscription | null>(null);

  const imgRef = useRef<HTMLImageElement>(null);
  const {
    latest2DResults: result, setLatest2DResults: setResult,
    latest2DImage: imagePreview, setLatest2DImage: setImagePreview,
    latest2DFile: file, setLatest2DFile: setFile,
    latest2DSource: source, setLatest2DSource: setSource,
    latest3DMeta, setLatest3DMeta,
    activeProjectId, setActiveProjectId,
  } = useAnalysis();
  const { geminiKey, addUsedTokens } = useSettings();
  const signum = latest3DMeta.text;
  const sourceKind: TwoDSourceKind = source?.kind ?? "upload";
  const isBinarySource = sourceKind === "groove-map" || sourceKind === "3d-snapshot";

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
    setResult(null);
    setCrop(undefined);
    setCompletedCrop(null);
    setAnalyzedCrop(null);
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

  // ---- AI analysis -------------------------------------------------------------------------
  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!imagePreview) return;
    setLoading(true);
    setResult(null);
    try {
      const canvas = processedCanvas(ANALYSIS_MAX_SIDE, completedCrop);
      if (!canvas) throw new Error("Kunde inte läsa bilden.");
      const blob = await canvasToBlob(canvas, isBinarySource ? "image/png" : "image/jpeg", 0.9);
      setAnalyzedCrop(completedCrop);
      const formData = new FormData();
      formData.append("file", blob, isBinarySource ? "bild.png" : "bild.jpg");
      const res = await fetch(`${API_URL}/api/2d/analyze`, { method: "POST", headers: { "X-Gemini-Api-Key": geminiKey }, body: formData });
      if (!res.ok) throw new Error((await res.json().catch(() => null))?.detail || `Fel ${res.status}`);
      const data = await res.json();
      setResult({ ...data, source: sourceKind });
      if (data.tokens_used) addUsedTokens(data.tokens_used);
    } catch (err) {
      alert(`Något gick fel vid 2D-analysen: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setLoading(false);
    }
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

  const handleSaveProject = async () => {
    if (!result || !imagePreview) return;
    const projectId = await resolveProjectId();
    const twoDImage = await persistentDataURL(imagePreview);
    const update: Partial<ProjectData> = projectId
      ? { id: projectId, twoDResults: result, twoDImage, ...(signum ? { metaText: signum, name: signum } : {}) }
      : { ...newProjectFields("Nytt projekt (2D)"), twoDResults: result, twoDImage };
    const saved = await db.saveProject(update);
    setActiveProjectId(saved.id);
    alert(`2D-data sparat till projekt: ${saved.name}`);
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

  const handleSaveCrop = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!completedCrop || completedCrop.width <= 0 || completedCrop.height <= 0) {
      alert("Markera först en runa genom att dra en ruta i bilden.");
      return;
    }
    setSavingCrop(true);
    try {
      const thumb = processedCanvas(THUMB_MAX_SIDE, completedCrop);
      const featureCanvas = processedCanvas(FEATURE_MAX_SIDE, completedCrop);
      if (!thumb || !featureCanvas) throw new Error("Kunde inte läsa utsnittet.");
      const thumbnail = thumb.toDataURL(isBinarySource ? "image/png" : "image/jpeg", 0.8);
      const res = await fetch(`${API_URL}/api/2d/extract_features`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image_base64: featureCanvas.toDataURL("image/png") }),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => null))?.detail || "Kunde inte beskriva runformen.");
      const features = await res.json();
      const newCrop: PaleographicCrop = {
        id: crypto.randomUUID(),
        tag: cropTag,
        imageBase64: thumbnail,
        coordinates: [completedCrop.x / 100, completedCrop.y / 100,
          (completedCrop.x + completedCrop.width) / 100, (completedCrop.y + completedCrop.height) / 100],
        featureVector: features.feature_vector,
        featureVersion: features.feature_version,
        formPng: features.form_png,
        sourceKind,
        grooveSummary: grooveSummaryFor(completedCrop),
        createdAt: new Date().toISOString(),
      };
      const projectId = await resolveProjectId();
      let update: Partial<ProjectData>;
      if (projectId) {
        const existing = await db.getProject(projectId);
        update = { id: projectId, paleographicCrops: [...(existing?.paleographicCrops ?? []), newCrop] };
      } else {
        update = { ...newProjectFields("Nytt projekt (runformer)"), paleographicCrops: [newCrop] };
      }
      const saved = await db.saveProject(update);
      setActiveProjectId(saved.id);
      await loadAllCrops();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Kunde inte spara utsnittet.");
    } finally {
      setSavingCrop(false);
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
      const res = await fetch(`/api/proxy-image?url=${encodeURIComponent(item.url)}`);
      if (!res.ok) throw new Error();
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
    } catch {
      alert("Bilden kunde inte hämtas från K-samsök (källan tillåter kanske inte extern åtkomst).");
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

  // ---- marker overlay (positions in % of the displayed image) -----------------------------
  const markerBox = (m: { polygon?: number[][]; box_2d?: number[] }) => {
    let ymin, xmin, ymax, xmax;
    if (m.polygon && m.polygon.length > 0) {
      ymin = Math.min(...m.polygon.map(p => p[0])) / 1000;
      xmin = Math.min(...m.polygon.map(p => p[1])) / 1000;
      ymax = Math.max(...m.polygon.map(p => p[0])) / 1000;
      xmax = Math.max(...m.polygon.map(p => p[1])) / 1000;
    } else if (m.box_2d && m.box_2d.length === 4) {
      [ymin, xmin, ymax, xmax] = m.box_2d.map(v => v / 1000);
    } else {
      return null;
    }
    const ac = analyzedCrop && analyzedCrop.width > 0 ? analyzedCrop : { x: 0, y: 0, width: 100, height: 100 };
    return {
      xmin, ymin, xmax, ymax,
      left: ac.x + xmin * ac.width, top: ac.y + ymin * ac.height,
      width: (xmax - xmin) * ac.width, height: (ymax - ymin) * ac.height,
    };
  };

  const styleAgrees = result && rundataForSignum?.style ? result.predicted_style === rundataForSignum.style : null;

  return (
    <>
      <svg width="0" height="0" className="absolute pointer-events-none">
        <filter id="channel-r"><feColorMatrix type="matrix" values="1 0 0 0 0  1 0 0 0 0  1 0 0 0 0  0 0 0 1 0" /></filter>
        <filter id="channel-g"><feColorMatrix type="matrix" values="0 1 0 0 0  0 1 0 0 0  0 1 0 0 0  0 0 0 1 0" /></filter>
        <filter id="channel-b"><feColorMatrix type="matrix" values="0 0 1 0 0  0 0 1 0 0  0 0 1 0 0  0 0 0 1 0" /></filter>
      </svg>
      <RuneCanvasBackground />
      <div className="flex flex-col h-full w-full max-w-7xl mx-auto p-4 md:p-6 relative z-10 overflow-y-auto">
        <div className="mb-8">
          <h2 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">2D-bildanalys (paleografi)</h2>
          <p className="text-slate-600 text-[16px] leading-relaxed max-w-3xl font-medium mb-6">
            Analysera ett foto, en vy från RTI-visaren eller en ristningskarta från 3D-analysen. AI:n bedömer stilgrupp och
            runformer; sparade runutsnitt jämförs med samma runa på andra stenar.
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
            {searchResults.length > 0 && (
              <div className="border-t border-slate-100 pt-3">
                <p className="text-xs font-bold text-slate-500 mb-2 uppercase tracking-wider">Sökresultat ({searchResults.length})</p>
                <div className="flex gap-3 overflow-x-auto pb-2">
                  {searchResults.map((res, i) => (
                    <button key={i} type="button" onClick={() => loadKSamsokImage(res)}
                      className="flex-shrink-0 w-24 h-24 rounded-xl overflow-hidden border-2 border-transparent hover:border-[#b7410e] relative group bg-slate-100">
                      <img src={res.thumbnail} alt="" className="w-full h-full object-cover" />
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
                    {result?.markers?.map((m, i) => {
                      const box = markerBox(m);
                      if (!box) return null;
                      return (
                        <div key={i}
                          onClick={e => {
                            e.stopPropagation();
                            const pc: PercentCrop = { unit: "%", x: box.left, y: box.top, width: box.width, height: box.height };
                            setCrop(pc);
                            setCompletedCrop(pc);
                          }}
                          className={`absolute group cursor-pointer z-40 rounded ${!m.polygon ? "border-2 border-[#b7410e] bg-[#b7410e]/10 hover:bg-[#b7410e]/40" : ""}`}
                          style={{ left: `${box.left}%`, top: `${box.top}%`, width: `${box.width}%`, height: `${box.height}%` }}>
                          {m.polygon && (
                            <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="absolute inset-0 w-full h-full overflow-visible pointer-events-none">
                              <polygon
                                points={m.polygon.map(p => `${((p[1] / 1000 - box.xmin) / (box.xmax - box.xmin || 1)) * 100},${((p[0] / 1000 - box.ymin) / (box.ymax - box.ymin || 1)) * 100}`).join(" ")}
                                className="fill-[#b7410e]/10 stroke-[#b7410e] group-hover:fill-[#b7410e]/40 pointer-events-auto" vectorEffect="non-scaling-stroke" />
                            </svg>
                          )}
                          <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 w-56 bg-slate-900 text-white text-xs p-3 rounded-xl opacity-0 group-hover:opacity-100 pointer-events-none z-50 shadow-xl">
                            <span className="font-bold block mb-1 text-[#f0a37f]">{m.label}</span>{m.description}
                          </div>
                        </div>
                      );
                    })}
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
                    Dra en ruta i bilden för att analysera eller spara ett utsnitt. Utan ruta analyseras hela bilden.
                  </p>
                </div>
              </div>
            )}

            <form onSubmit={handleAnalyze} className="w-full mt-6">
              <button type="submit" disabled={loading || !imagePreview}
                className="w-full py-3.5 bg-slate-900 hover:bg-black disabled:opacity-40 text-white font-semibold text-sm rounded-2xl shadow-lg flex justify-center items-center gap-2">
                {loading ? (<><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Analyserar...</>)
                  : completedCrop && completedCrop.width > 0 ? "Kör AI-analys av utsnittet" : "Kör AI-analys av hela bilden"}
              </button>
              {!imagePreview && <p className="text-xs text-slate-500 mt-2 text-center">Välj eller hämta en bild först.</p>}
            </form>

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

            {loading ? (
              <div className="liquid-glass-island rounded-[36px] flex flex-col items-center justify-center border border-white/50 p-8 text-center min-h-[300px]">
                <div className="w-16 h-16 border-4 border-slate-200 border-t-[#b7410e] rounded-full animate-spin mb-6" />
                <h3 className="text-xl font-bold text-slate-800 mb-2">Analyserar bilden...</h3>
                <p className="text-sm text-slate-500 max-w-sm">Det kan ta upp till 30 sekunder.</p>
              </div>
            ) : result ? (
              <div className="space-y-6">
                <div className="liquid-glass-island rounded-[36px] p-8 border border-[#b7410e]/20 bg-gradient-to-br from-white/50 to-[#b7410e]/5">
                  <div className="text-slate-500 text-[12px] uppercase tracking-wider font-bold mb-2">Stilgrupp enligt AI (Gräslund)</div>
                  <div className="flex flex-wrap items-end gap-4">
                    <h3 className="text-5xl font-black text-[#b7410e]">{result.predicted_style}</h3>
                    <div className="mb-2 bg-slate-900 text-white text-xs font-bold px-3 py-1 rounded-full" title="AI:ns egen uppskattning, inte en kalibrerad sannolikhet">
                      AI:ns självskattning {result.confidence} % (okalibrerad)
                    </div>
                  </div>
                  {rundataForSignum && (
                    <div className={`mt-4 rounded-xl px-4 py-3 text-sm font-semibold ${styleAgrees === null ? "bg-slate-100 text-slate-700" : styleAgrees ? "bg-emerald-50 text-emerald-800" : "bg-amber-50 text-amber-800"}`}>
                      Rundata ({rundataForSignum.signum}): {rundataForSignum.style ? `${rundataForSignum.style}${rundataForSignum.style_uncertain ? " (osäker)" : ""}` : "ingen stilgrupp angiven"}
                      {styleAgrees === true && " – stämmer med AI:ns bedömning."}
                      {styleAgrees === false && " – skiljer sig från AI:ns bedömning. Granska ornamentiken."}
                      {" "}<Link href={`/stilgrupper#${result.predicted_style}`} className="underline">Om stilgrupperna</Link>
                    </div>
                  )}
                </div>
                <div className="liquid-glass-island rounded-[36px] p-8 border border-white/50">
                  <div className="text-slate-500 text-[12px] uppercase tracking-wider font-bold mb-4">Epigrafisk motivering (AI)</div>
                  <p className="text-slate-700 text-sm font-medium leading-relaxed">{result.reasoning}</p>
                </div>
                {result.rune_types && (
                  <div className="liquid-glass-island rounded-[36px] p-8 border border-white/50">
                    <div className="text-slate-500 text-[12px] uppercase tracking-wider font-bold mb-2">Runtyper och paleografi (AI)</div>
                    <p className="text-slate-700 text-sm font-medium leading-relaxed">{result.rune_types}</p>
                  </div>
                )}
                <div className="liquid-glass-island rounded-[36px] p-6 border border-white/50 flex items-end justify-between gap-4">
                  <div className="flex-1">
                    <label className="block text-slate-500 text-[10px] font-bold uppercase tracking-wider mb-1">Signum (t.ex. Sö 112)</label>
                    <input value={signum} onChange={e => setLatest3DMeta({ ...latest3DMeta, text: e.target.value })}
                      placeholder="Ange signum..." className="w-full liquid-glass-input-wrapper rounded-xl px-4 py-2.5 text-slate-900 text-sm font-semibold outline-none" />
                  </div>
                  <button onClick={handleSaveProject}
                    className="px-6 py-3 bg-[#b7410e] hover:bg-[#9a350b] text-white font-bold rounded-2xl shadow-lg flex-shrink-0">
                    Spara i projekt
                  </button>
                </div>
                <p className="text-[11px] text-slate-500">
                  Bedömningen är gjord av {result.model || "en AI-modell"} och ska granskas. I syntesen vägs den mot Rundata.
                </p>
              </div>
            ) : (
              <div className="liquid-glass-island rounded-[36px] flex flex-col items-center justify-center border border-white/50 p-8 text-center text-slate-400 min-h-[300px]">
                <p className="font-semibold text-lg text-slate-500 mb-2">Ingen analys ännu</p>
                <p className="text-sm max-w-sm">Välj en bild och klicka på Kör AI-analys.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}

