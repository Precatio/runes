"use client";

import { useState, useEffect, useEffectEvent, Suspense } from "react";
import PlotlyGraph from "@/components/PlotlyGraph";
import { toJpeg } from 'html-to-image';
import { useLanguage } from "@/components/LanguageContext";
import { useAnalysis } from "@/components/AnalysisContext";
import { useSettings } from "@/components/SettingsContext";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { db, ProjectData } from "@/lib/db";
import GrooveResultsPanel from "@/components/GrooveResultsPanel";
import { FEATURE_TYPES, type FeatureType } from "@/lib/metrics";
import dynamic from 'next/dynamic';
import { API_URL } from "@/lib/api";

// Disable SSR for ThreeDViewer since it uses browser APIs (window, DOM)
const ThreeDViewer = dynamic(() => import('@/components/ThreeDViewer'), {
  ssr: false,
  loading: () => <div className="w-full h-full flex items-center justify-center">Laddar 3D-miljö...</div>
});

function ThreeDPageContent() {
  const searchParams = useSearchParams();
  const urlProjectId = searchParams.get("projectId");
  const urlSignum = searchParams.get("signum");

  const { 
    latest3DResults: results, 
    setLatest3DResults: setResults,
    latest3DFile: file,
    setLatest3DFile: setFile,
    latest3DMeta: meta,
    setLatest3DMeta: setMeta,
    activeProjectId,
    setActiveProjectId,
    setLatest2DImage
  } = useAnalysis();

  const [activeProject, setActiveProject] = useState<ProjectData | null>(null);

  useEffect(() => {
    const fetchProj = async () => {
      if (activeProjectId) {
         setActiveProject(await db.getProject(activeProjectId));
      } else {
         setActiveProject(null);
      }
    };
    fetchProj();
  }, [activeProjectId]);

  const [loading, setLoading] = useState(false);
  
  const [origin, setOrigin] = useState([0.0, 0.0, 0.0]);
  const [direction, setDirection] = useState([0.0, 1.0, 0.0]);
  const [up, setUp] = useState([0.0, 0.0, 1.0]);
  const [sliceCount, setSliceCount] = useState(3); // Averaging
  const [pathPoints, setPathPoints] = useState<[number, number, number][] | null>(null);
  
  // Metadata & Context
  const metaStone = meta.stone;
  const setMetaStone = (v: string) => setMeta({...meta, stone: v});
  
  const metaWeathering = meta.weathering;
  const setMetaWeathering = (v: string) => setMeta({...meta, weathering: v});

  const metaText = meta.text;
  const setMetaText = (v: string) => setMeta({...meta, text: v});

  const metaOrnamentation = meta.ornamentation;

  const metaPeriod = meta.period;

  const attributedCarver = meta.carver;

  const location = meta.location;
  
  // Advanced UI
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [cutoffDepth, setCutoffDepth] = useState(0.0);
  const [layerThickness, setLayerThickness] = useState(100.0);
  const [slicerMode, setSlicerMode] = useState<'flat' | 'peeling'>('flat');

  // RAA Fetching
  const [fetchingRaa, setFetchingRaa] = useState(false);
  const [raaSource, setRaaSource] = useState<{ source: string; signum?: string; attribution?: string } | null>(null);
  const [featureType, setFeatureType] = useState<FeatureType>("rune");
  // Lighter, pre-centred model for display of very large scans; analysis always uses the original file
  const [viewFile, setViewFile] = useState<File | null>(null);
  const [preparingView, setPreparingView] = useState(false);
  const { t } = useLanguage();
  const { geminiKey } = useSettings();

  // Load project on mount
  useEffect(() => {
    const load = async () => {
      const idToLoad = urlProjectId || activeProjectId;
      if (idToLoad) {
        const proj = await db.getProject(idToLoad);
        if (proj) {
          if (urlProjectId) setActiveProjectId(urlProjectId);
          setMeta({
            ...meta, 
            stone: proj.metaStone || "Okänd", 
            weathering: proj.metaWeathering || "Låg", 
            text: proj.metaText || "", 
            ornamentation: proj.metaOrnamentation || "", 
            period: proj.metaPeriod || "", 
            carver: proj.attributedCarver || "", 
            location: proj.location || ""
          });
        }
      }
    };
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [urlProjectId]);


  const handleSaveProject = async () => {
    if (!results) return;
    
    let projectIdToSaveTo = activeProjectId;
    let projToUpdate = projectIdToSaveTo ? await db.getProject(projectIdToSaveTo) : null;
    
    // Auto-grouping by signum
    if (!projToUpdate && metaText) {
      const existingProj = await db.getProjectBySignum(metaText);
      if (existingProj) {
        projectIdToSaveTo = existingProj.id;
        projToUpdate = existingProj;
      }
    }

    // Create new slice data
    const newSlice = {
      p1: origin as [number, number, number],
      p2: [origin[0] + direction[0]*10, origin[1] + direction[1]*10, origin[2] + direction[2]*10] as [number, number, number], // rough endpoint
      angle: results.results.apex_vinkel_deg,
      asymmetry: results.results.asymmetri_deg,
      depth: results.results.spårdjup_mm,
      width: results.results.spårbredd_mm,
      djup_bredd_kvot: results.results.djup_bredd_kvot,
      bottenradie: results.results.bottenradie_mm,
      ytrahet: results.results.ytråhet_mm,
      tool: results.results.troligt_verktyg
    };

    // Capture images
    let threeImage = projToUpdate?.threeImage;
    const canvas = document.querySelector('canvas');
    if (canvas) {
      const tempCanvas = document.createElement('canvas');
      tempCanvas.width = canvas.width;
      tempCanvas.height = canvas.height;
      const ctx = tempCanvas.getContext('2d');
      if (ctx) {
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, tempCanvas.width, tempCanvas.height);
        ctx.drawImage(canvas, 0, 0);
        threeImage = tempCanvas.toDataURL("image/jpeg", 0.7);
      } else {
        threeImage = canvas.toDataURL("image/jpeg", 0.7);
      }
    }
    
    let plotImage = projToUpdate?.plotImage;
    const plotlyEl = document.querySelector('.js-plotly-plot') as HTMLElement;
    if (plotlyEl) {
      try {
        plotImage = await toJpeg(plotlyEl, { quality: 0.95, backgroundColor: '#ffffff' });
      } catch (e) {
        console.error("Could not capture plotly image", e);
      }
    }

    const saved = await db.saveProject({
      id: projToUpdate?.id,
      name: projToUpdate ? projToUpdate.name : (file ? file.name.split('.')[0] : "Nytt Projekt"),
      fileName: file ? file.name : (projToUpdate ? projToUpdate.fileName : "Mock.stl"),
      metaStone: metaStone,
      metaWeathering: metaWeathering,
      metaText: metaText,
      metaOrnamentation: metaOrnamentation,
      metaPeriod: metaPeriod,
      attributedCarver: attributedCarver,
      location: location,
      plotImage: plotImage,
      threeImage: threeImage,
      slices: projToUpdate ? [...projToUpdate.slices, newSlice] : [newSlice],
      grooveAnalyses: results.summary && results.slices && results.provenance
        ? [
            ...(projToUpdate?.grooveAnalyses ?? []),
            {
              id: crypto.randomUUID(),
              feature_type: featureType,
              summary: results.summary,
              slices: results.slices,
              provenance: results.provenance,
              savedAt: new Date().toISOString(),
            },
          ]
        : projToUpdate?.grooveAnalyses,
    });
    
    setActiveProjectId(saved.id);
    alert(`3D-data sparat till projekt: ${saved.name}`);
  };

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResults(null);

    const formData = new FormData();
    if (file) {
      formData.append("file", file);
    }
    
    formData.append("origin_x", origin[0].toString());
    formData.append("origin_y", origin[1].toString());
    formData.append("origin_z", origin[2].toString());
    formData.append("dir_x", direction[0].toString());
    formData.append("dir_y", direction[1].toString());
    formData.append("dir_z", direction[2].toString());
    formData.append("up_x", up[0].toString());
    formData.append("up_y", up[1].toString());
    formData.append("up_z", up[2].toString());
    formData.append("slice_count", sliceCount.toString());
    formData.append("slice_spacing_mm", "1.0");
    formData.append("meta_stone", metaStone);
    formData.append("meta_weathering", metaWeathering);
    formData.append("meta_text", metaText);
    formData.append("feature_type", featureType);

    let endpoint = `${API_URL}/api/3d/analyze`;
    if (pathPoints && pathPoints.length > 2) {
      endpoint = `${API_URL}/api/3d/analyze_path`;
      formData.append("path_points_json", JSON.stringify(pathPoints));
    }

    try {
      const res = await fetch(endpoint, {
        method: "POST",
        headers: {
          "X-Gemini-Api-Key": geminiKey
        },
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail || "Analys misslyckades");
      }

      const data = await res.json();
      setResults(data);
    } catch (err) {
      console.error(err);
      alert(err instanceof Error ? err.message : "Något gick fel vid 3D-analysen.");
    } finally {
      setLoading(false);
    }
  };

  const handleSnapshot2D = async () => {
    const canvas = document.querySelector('canvas');
    if (!canvas) return;
    
    // Create a temporary canvas matching the original size
    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = canvas.width;
    tempCanvas.height = canvas.height;
    const ctx = tempCanvas.getContext('2d');
    if (!ctx) return;
    
    // Draw the 3D canvas onto our 2D canvas
    ctx.drawImage(canvas, 0, 0);
    
    // Binarization (Adaptive Thresholding)
    const imgData = ctx.getImageData(0, 0, tempCanvas.width, tempCanvas.height);
    const data = imgData.data;
    
    // Simple global threshold to start with (since shader already outputs grayscale high contrast)
    // The peeling shader outputs very dark for carved areas, light for surface.
    // We want white background, black runes.
    for (let i = 0; i < data.length; i += 4) {
      const r = data[i];
      const g = data[i+1];
      const b = data[i+2];
      
      // Calculate luminance
      const lum = 0.299 * r + 0.587 * g + 0.114 * b;
      
      if (lum < 100) {
        // Dark areas (runes) -> Black
        data[i] = data[i+1] = data[i+2] = 0;
      } else {
        // Light areas (surface/background) -> White
        data[i] = data[i+1] = data[i+2] = 255;
      }
      // Keep alpha as is (fully opaque)
      data[i+3] = 255;
    }
    
    ctx.putImageData(imgData, 0, 0);
    
    const binarizedBase64 = tempCanvas.toDataURL('image/png');
    setLatest2DImage(binarizedBase64); // Send to 2D image preview context
    alert("2D-Ögonblicksbild fångad och binariserad! Gå till 'Paleografi / 2D Bild' för att arbeta med bilden.");
  };

  const handleAutoSnapRequest = async (points: [number, number, number][]): Promise<[number, number, number][]> => {
    const formData = new FormData();
    if (file) {
      formData.append("file", file);
    } else {
      formData.append("use_mock", "true");
    }
    formData.append("path_points_json", JSON.stringify(points));
    formData.append("up_x", up[0].toString());
    formData.append("up_y", up[1].toString());
    formData.append("up_z", up[2].toString());

    const res = await fetch(`${API_URL}/api/3d/auto_snap_path`, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      throw new Error("Kunde inte snappa banan mot botten.");
    }
    const data = await res.json();
    return data.snapped_path;
  };

  const STONE_TYPES = ["Granit", "Gnejs", "Sandsten", "Kalksten", "Skiffer", "Gråsten", "Porfyr", "Kvartsit"];

  // Fetch metadata for a signum (Rundata first, K-samsök + AI as fallback) and apply it in ONE state update,
  // so that no field overwrites another
  const fetchRaa = async (signum: string, interactive: boolean) => {
    setFetchingRaa(true);
    try {
      const res = await fetch(`${API_URL}/api/raa/fetch`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Gemini-Api-Key": geminiKey },
        body: JSON.stringify({ signum }),
      });
      if (!res.ok) throw new Error("Kunde inte hämta uppgifter om signumet");
      const data = await res.json();

      const material = String(data.material || "").toLowerCase();
      const stone = STONE_TYPES.find(st => material.includes(st.toLowerCase()))
        ?? meta.stone;
      const condition = String(data.condition || "").toLowerCase();
      let weathering = meta.weathering;
      if (/låg|gott|bra/.test(condition)) weathering = "Låg";
      else if (/medel/.test(condition)) weathering = "Medel";
      else if (/hög|svår|kraftig/.test(condition)) weathering = "Hög";
      const keep = (value: string | undefined, unknown: string, current: string) =>
        value && value !== unknown ? value : current;

      setMeta({
        ...meta,
        text: data.signum || signum,
        stone,
        weathering,
        carver: keep(data.attributed_carver, "Okänd", meta.carver),
        location: keep(data.location, "Okänd plats", meta.location),
        ornamentation: keep(data.ornamentation, "Okänd", meta.ornamentation),
        period: keep(data.period, "Okänd", meta.period),
      });
      setRaaSource({ source: data.source, signum: data.signum, attribution: data.attribution });
      if (interactive) {
        alert(`Hämtade uppgifter (${data.source === "rundata" ? "Rundata" : "K-samsök, AI-tolkat"}):\n` +
          `Material: ${data.material}\nRistare: ${data.attributed_carver}\nPlats: ${data.location}\nStil: ${data.ornamentation}\nDatering: ${data.period}`);
      }
    } catch (err) {
      console.error(err);
      if (interactive) alert("Något gick fel vid hämtningen av uppgifter om signumet.");
    } finally {
      setFetchingRaa(false);
    }
  };

  const handleFetchRAA = () => {
    if (!metaText) {
      alert("Ange ett signum först (t.ex. 'Sö 112').");
      return;
    }
    fetchRaa(metaText, true);
  };

  // Opened from an inscription page: prefill the signum and its Rundata metadata
  const prefillFromSignum = useEffectEvent((signum: string) => {
    if (!urlProjectId && signum !== meta.text) fetchRaa(signum, false);
  });
  useEffect(() => {
    if (!urlSignum) return;
    const timer = setTimeout(() => prefillFromSignum(urlSignum), 0);
    return () => clearTimeout(timer);
  }, [urlSignum]);

  const LARGE_FILE_BYTES = 150 * 1024 * 1024;

  const prepareViewModel = async (selectedFile: File) => {
    setPreparingView(true);
    try {
      const fd = new FormData();
      fd.append("file", selectedFile);
      const res = await fetch(`${API_URL}/api/3d/view_model`, { method: "POST", body: fd });
      if (!res.ok) throw new Error("Kunde inte skapa visningsmodell");
      const blob = await res.blob();
      setViewFile(new File([blob], selectedFile.name.replace(/\.[^.]+$/, "") + "_visning.stl", { type: "model/stl" }));
    } catch (err) {
      console.error(err);
      setViewFile(null);
    } finally {
      setPreparingView(false);
    }
  };

  const handleFileUpload = async (selectedFile: File | null) => {
    setFile(selectedFile);
    setViewFile(null);
    setRaaSource(null);
    if (!selectedFile) return;
    if (selectedFile.size > LARGE_FILE_BYTES) prepareViewModel(selectedFile);

    try {
      const res = await fetch(`${API_URL}/api/raa/extract-signum`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Gemini-Api-Key": geminiKey },
        body: JSON.stringify({ filename: selectedFile.name }),
      });
      if (res.ok) {
        const data = await res.json();
        if (data.signum && data.signum !== "Okänd") fetchRaa(data.signum, false);
      }
    } catch (err) {
      if (err instanceof Error && err.message === "Failed to fetch") {
        console.log("Python backend ej nåbar, hoppar över auto-extract av signum.");
      } else {
        console.error("Kunde inte extrahera signum från filnamn", err);
      }
    }
  };

  const getPlotData = () => {
    const d = results?.plot_data;
    if (!results || !d) return [];

    const dataTrace = {
      x: d.x,
      y: d.z,
      mode: "markers",
      name: "Data",
      marker: { color: "#64748b", size: 5, opacity: 0.5 }
    };

    // Path analysis returns only the raw profile, without line fits
    const apex = results.results.apex_idx;
    const { fit_left, fit_right } = d;
    if (apex === undefined || !fit_left || !fit_right) return [dataTrace];

    // Använd de faktiska axlarna om de finns, annars default
    const left_shoulder = results.results.left_shoulder || 0;
    const right_shoulder = results.results.right_shoulder || d.x.length - 1;
    
    const x_left = d.x.slice(left_shoulder, apex);
    const x_right = d.x.slice(apex + 1, right_shoulder + 1);

    return [
      dataTrace,
      // Highlight the ROI region
      {
        x: d.x.slice(left_shoulder, right_shoulder + 1),
        y: d.z.slice(left_shoulder, right_shoulder + 1),
        mode: "markers",
        name: "ROI (Spår)",
        marker: { color: "#0f172a", size: 6 }
      },
      {
        x: x_left,
        y: x_left.map((x: number) => fit_left.k * x + fit_left.m),
        mode: "lines",
        name: "Vänster",
        line: { color: "#ef4444", width: 3 }
      },
      {
        x: x_right,
        y: x_right.map((x: number) => fit_right.k * x + fit_right.m),
        mode: "lines",
        name: "Höger",
        line: { color: "#b7410e", width: 3 }
      }
    ];
  };

  const plotLayout = {
    title: t.threed.graph_title,
    paper_bgcolor: "transparent",
    plot_bgcolor: "transparent",
    font: { color: "#0f172a", family: "-apple-system, sans-serif" },
    xaxis: { title: "X (mm)", gridcolor: "rgba(0,0,0,0.08)", zerolinecolor: "rgba(0,0,0,0.15)" },
    yaxis: { title: "Z (mm)", gridcolor: "rgba(0,0,0,0.08)", zerolinecolor: "rgba(0,0,0,0.15)", scaleanchor: "x", scaleratio: 1 },
    margin: { l: 45, r: 25, t: 45, b: 45 },
  };

  return (
    <div className="flex flex-col h-full w-full max-w-7xl mx-auto p-4 md:p-6 relative z-10 overflow-y-auto">
      <div className="mb-8">
        <div className="flex justify-between items-end">
          <div>
            <h2 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">
              {activeProject ? `Projekt: ${activeProject.name}` : t.threed.title}
            </h2>
            <p className="text-slate-600 text-[16px] leading-relaxed max-w-3xl font-medium">
              {activeProject ? `Ladda in filen "${activeProject.fileName}" lokalt för att återuppta arbetet.` : t.threed.description}
            </p>
          </div>
          {activeProject && (
             <div className="bg-[#b7410e]/10 text-[#b7410e] px-4 py-2 rounded-full font-bold text-sm">
                Sparat i molnet
             </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Settings Sidebar */}
        <div className="liquid-glass-island rounded-[36px] p-8 h-fit">
          <form onSubmit={handleAnalyze} className="space-y-8">
            <div>
              <label className="block text-slate-500 text-[12px] mb-2 font-bold uppercase tracking-wider">{t.threed.upload_mesh}</label>
              <div className="relative overflow-hidden">
                <input 
                  type="file" 
                  accept=".stl,.obj,.ply" 
                  onChange={(e) => handleFileUpload(e.target.files?.[0] || null)}
                  className="w-full text-slate-900 text-xs file:mr-4 file:py-2 file:px-5 file:rounded-full file:border-0 file:font-semibold transition-all cursor-pointer bg-slate-900 text-white hover:bg-black shadow-md"
                />
              </div>
            </div>

            {(preparingView || viewFile) && (
              <p className="text-[11px] text-slate-500 -mt-5">
                {preparingView
                  ? "Stor fil – skapar en lättare visningsmodell. Mätningarna görs på originalet."
                  : "Visar en förenklad modell. Mätningarna görs på originalfilen."}
              </p>
            )}

            <div>
              <label className="block text-slate-500 text-[12px] mb-2 font-bold uppercase tracking-wider">Spårtyp</label>
              <select value={featureType} onChange={e => setFeatureType(e.target.value as FeatureType)} className="w-full liquid-glass-input-wrapper rounded-xl px-4 py-2.5 text-slate-900 text-sm font-semibold outline-none">
                {Object.entries(FEATURE_TYPES).map(([k, label]) => <option key={k} value={k}>{label}</option>)}
              </select>
              <p className="text-[11px] text-slate-500 mt-1">Runor och ornamentik huggs ofta olika och jämförs var för sig.</p>
            </div>

            <div>
              <label className="block text-slate-500 text-[12px] mb-2 font-bold uppercase tracking-wider">Flera snitt (Medelvärde)</label>
              <select value={sliceCount} onChange={e => setSliceCount(+e.target.value)} className="w-full liquid-glass-input-wrapper rounded-xl px-4 py-2.5 text-slate-900 text-sm font-semibold outline-none">
                <option value={1}>1 snitt (Snabb)</option>
                <option value={3}>3 snitt (Standard)</option>
                <option value={5}>5 snitt (Hög Precision)</option>
                <option value={9}>9 snitt (Spridningsmått)</option>
                <option value={15}>15 snitt (Robust)</option>
              </select>
            </div>

            <div className="space-y-5 pt-2">
              <div>
                <label className="block text-slate-500 text-[12px] mb-2 font-bold uppercase tracking-wider">Stenart</label>
                <select value={metaStone} onChange={e => setMetaStone(e.target.value)} className="w-full liquid-glass-input-wrapper rounded-xl px-4 py-2.5 text-slate-900 text-sm font-semibold outline-none">
                  <option value="Granit">Granit</option>
                  <option value="Gnejs">Gnejs</option>
                  <option value="Gråsten">Gråsten</option>
                  <option value="Sandsten">Sandsten</option>
                  <option value="Kalksten">Kalksten</option>
                  <option value="Skiffer">Skiffer</option>
                  <option value="Porfyr">Porfyr</option>
                  <option value="Kvartsit">Kvartsit</option>
                  <option value="Okänd">Okänd</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-500 text-[12px] mb-2 font-bold uppercase tracking-wider">Yttre påverkan (Vittring)</label>
                <select value={metaWeathering} onChange={e => setMetaWeathering(e.target.value)} className="w-full liquid-glass-input-wrapper rounded-xl px-4 py-2.5 text-slate-900 text-sm font-semibold outline-none">
                  <option value="Låg">Låg</option>
                  <option value="Medel">Medel</option>
                  <option value="Hög">Hög</option>
                </select>
              </div>

              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="block text-slate-500 text-[12px] font-bold uppercase tracking-wider">Signum (RAÄ)</label>
                  <button 
                    type="button" 
                    onClick={handleFetchRAA}
                    disabled={fetchingRaa || !metaText}
                    className="text-[10px] bg-slate-900 hover:bg-black text-white font-bold px-3 py-1.5 rounded-full transition-colors flex items-center gap-1.5 disabled:opacity-50 shadow-sm"
                  >
                    {fetchingRaa ? (
                      <div className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : (
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-3 h-3">
                        <path fillRule="evenodd" d="M10.5 3.75a6.75 6.75 0 1 0 0 13.5 6.75 6.75 0 0 0 0-13.5ZM2.25 10.5a8.25 8.25 0 1 1 14.59 5.28l4.69 4.69a.75.75 0 1 1-1.06 1.06l-4.69-4.69A8.25 8.25 0 0 1 2.25 10.5Z" clipRule="evenodd" />
                      </svg>
                    )}
                    {fetchingRaa ? "Hämtar..." : "Autofyll info"}
                  </button>
                </div>
                <input 
                  type="text" 
                  placeholder="t.ex. Sö 112" 
                  value={metaText} 
                  onChange={e => setMetaText(e.target.value)} 
                  className="w-full liquid-glass-input-wrapper rounded-xl px-4 py-2.5 text-slate-900 text-sm font-semibold outline-none placeholder:text-slate-400"
                />
                
                {/* Auto-fetched Hypothesis Info */}
                {(attributedCarver || location || metaOrnamentation || metaPeriod) && (
                  <div className="mt-3 bg-slate-900/5 rounded-xl p-3 border border-slate-900/10 animate-in fade-in grid grid-cols-2 gap-2">
                    {raaSource && (
                      <div className="col-span-2 text-[10px] font-bold uppercase tracking-wider">
                        {raaSource.source === "rundata" ? (
                          <Link href={`/inskrifter?signum=${encodeURIComponent(raaSource.signum || metaText)}`} className="text-emerald-700 hover:underline">
                            Källa: Rundata (Samnordisk runtextdatabas) →
                          </Link>
                        ) : (
                          <span className="text-amber-700">Källa: K-samsök, tolkat av AI – kontrollera uppgifterna</span>
                        )}
                      </div>
                    )}
                    {attributedCarver && (
                      <div className="text-[11px] text-slate-600 mb-1">
                        <span className="font-bold uppercase tracking-wider text-slate-900">Ristare:</span> {attributedCarver}
                      </div>
                    )}
                    {location && (
                      <div className="text-[11px] text-slate-600">
                        <span className="font-bold uppercase tracking-wider text-slate-900">Plats:</span> {location}
                      </div>
                    )}
                    {metaOrnamentation && (
                      <div className="text-[11px] text-slate-600">
                        <span className="font-bold uppercase tracking-wider text-slate-900">Stilgrupp:</span> {metaOrnamentation}
                      </div>
                    )}
                    {metaPeriod && (
                      <div className="text-[11px] text-slate-600">
                        <span className="font-bold uppercase tracking-wider text-slate-900">Datering (RAÄ):</span> {metaPeriod}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            <div className="pt-4 border-t border-slate-900/10">
              <button 
                type="button" 
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="text-slate-500 hover:text-slate-900 text-xs font-bold uppercase tracking-wider flex items-center gap-2"
              >
                {showAdvanced ? "Dölj manuella vektorer" : "Visa manuella vektorer"}
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className={`w-4 h-4 transition-transform ${showAdvanced ? "rotate-180" : ""}`}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                </svg>
              </button>
              
              {showAdvanced && (
                <div className="space-y-4 mt-4 animate-in slide-in-from-top-2">
                  {[
                    { label: t.threed.origin, state: origin, set: setOrigin },
                    { label: t.threed.direction, state: direction, set: setDirection },
                    { label: t.threed.up_vector, state: up, set: setUp },
                  ].map((vec, i) => (
                    <div key={i}>
                      <label className="block text-slate-500 text-[10px] mb-1.5 font-bold uppercase tracking-wider">{vec.label}</label>
                      <div className="flex gap-2">
                        <input type="number" step="0.1" value={vec.state[0]} onChange={e => vec.set([+e.target.value, vec.state[1], vec.state[2]])} className="w-full liquid-glass-input-wrapper rounded-xl px-2.5 py-2 text-slate-900 text-center text-xs font-semibold outline-none transition-all" />
                        <input type="number" step="0.1" value={vec.state[1]} onChange={e => vec.set([vec.state[0], +e.target.value, vec.state[2]])} className="w-full liquid-glass-input-wrapper rounded-xl px-2.5 py-2 text-slate-900 text-center text-xs font-semibold outline-none transition-all" />
                        <input type="number" step="0.1" value={vec.state[2]} onChange={e => vec.set([vec.state[0], vec.state[1], +e.target.value])} className="w-full liquid-glass-input-wrapper rounded-xl px-2.5 py-2 text-slate-900 text-center text-xs font-semibold outline-none transition-all" />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="pt-4 border-t border-slate-900/10 space-y-4">
              
              {/* Slicer Mode Toggle */}
              <div className="flex bg-slate-900/5 p-1 rounded-xl">
                <button
                  type="button"
                  onClick={() => setSlicerMode('flat')}
                  className={`flex-1 py-1.5 text-[11px] font-bold rounded-lg transition-all uppercase tracking-wider ${slicerMode === 'flat' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
                >
                  🔪 Platt
                </button>
                <button
                  type="button"
                  onClick={() => setSlicerMode('peeling')}
                  className={`flex-1 py-1.5 text-[11px] font-bold rounded-lg transition-all uppercase tracking-wider ${slicerMode === 'peeling' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
                >
                  🍎 Ytföljande
                </button>
              </div>

              <div>
                <label className="flex justify-between block text-slate-500 text-[12px] mb-2 font-bold uppercase tracking-wider">
                  <span>Skala av ytan (%)</span>
                  <span>{cutoffDepth.toFixed(0)}</span>
                </label>
                <input 
                  type="range" min="0" max="100" step="1" 
                  value={cutoffDepth} 
                  onChange={e => setCutoffDepth(parseFloat(e.target.value))} 
                  className="w-full accent-slate-900 cursor-pointer" 
                />
              </div>
              <div>
                <label className="flex justify-between block text-slate-500 text-[12px] mb-2 font-bold uppercase tracking-wider">
                  <span>Skikttjocklek (%)</span>
                  <span>{layerThickness.toFixed(0)}</span>
                </label>
                <input 
                  type="range" min="1" max="100" step="1" 
                  value={layerThickness} 
                  onChange={e => setLayerThickness(parseFloat(e.target.value))} 
                  className="w-full accent-slate-900 cursor-pointer" 
                />
              </div>

              <button 
                type="button" 
                onClick={handleSnapshot2D}
                disabled={!file}
                className="w-full mt-4 py-2.5 bg-white border border-[#b7410e] text-[#b7410e] hover:bg-[#b7410e] hover:text-white active:scale-[0.98] disabled:opacity-40 font-semibold text-sm rounded-xl transition-all shadow-sm flex justify-center items-center gap-2"
              >
                📸 Ta 2D-Ögonblicksbild (Binariserad)
              </button>
            </div>

            <button 
              type="submit" 
              disabled={loading || !file}
              className="w-full py-3.5 bg-slate-900 hover:bg-black active:scale-[0.98] disabled:opacity-40 text-white font-semibold text-sm rounded-2xl transition-all shadow-lg flex justify-center items-center gap-2 mt-4"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  {t.threed.calculating}
                </>
              ) : t.threed.analyze_btn}
            </button>
          </form>
        </div>

        {/* Results Area */}
        <div className="lg:col-span-2 space-y-8 flex flex-col">
          
          {/* Interactive 3D Viewer */}
          <div className="liquid-glass-island rounded-[36px] p-2 h-[600px] xl:h-[700px] flex-shrink-0 relative group shadow-sm border border-white/50">
            <ThreeDViewer 
              file={viewFile ?? file} 
              preCentered={!!viewFile}
              onVectorSelected={(o, d) => {
                setOrigin(o);
                setDirection(d);
                setPathPoints(null);
              }}
              onPathSelected={(pts) => {
                setPathPoints(pts);
              }}
              onAutoSnapRequest={handleAutoSnapRequest}
              cutoffDepth={cutoffDepth}
              layerThickness={layerThickness}
              slicerMode={slicerMode}
            />
          </div>

          {results && (
            <GrooveResultsPanel results={results} signum={metaText} featureType={featureType} />
          )}

          {/* Graph */}
          {results && (
            <div className="liquid-glass-island rounded-[36px] p-6 flex flex-col items-center justify-center relative shadow-sm border border-white/50 animate-in fade-in slide-in-from-bottom-8">
              
              <div className="w-full grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* V-form Graph */}
                <div>
                  <h3 className="font-bold text-sm text-slate-700 mb-2">Tvärsnittsprofil (V-form)</h3>
                  <div className="bg-white/80 rounded-2xl border border-white p-2 shadow-inner h-[300px]">
                    <PlotlyGraph 
                      data={getPlotData()}
                      layout={{...plotLayout, margin: { l: 40, r: 20, t: 20, b: 40 }, showlegend: false, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)' }}
                    />
                  </div>
                </div>
                
                {/* Longitudinal Depth Profile */}
                {results.depth_profile && results.depth_profile.distances.length > 0 ? (
                  <div>
                    <h3 className="font-bold text-sm text-slate-700 mb-2">Topografisk Längdprofil (Djup längs banan)</h3>
                    <div className="bg-white/80 rounded-2xl border border-white p-2 shadow-inner h-[300px]">
                      <PlotlyGraph 
                        data={[
                          { 
                            x: results.depth_profile.distances, 
                            y: results.depth_profile.depths, 
                            mode: 'lines+markers', 
                            line: { color: '#b7410e', shape: 'spline' }, 
                            marker: { size: 4 },
                            fill: 'tozeroy',
                            fillcolor: 'rgba(183, 65, 14, 0.1)',
                            name: 'Djup' 
                          }
                        ]}
                        layout={{
                          margin: { l: 40, r: 20, t: 20, b: 40 },
                          xaxis: { title: 'Avstånd längs spår (mm)' },
                          yaxis: { 
                            title: 'Spårdjup (mm)', 
                            autorange: 'reversed' // Reversed so deeper is lower
                          },
                          showlegend: false,
                          paper_bgcolor: 'rgba(0,0,0,0)',
                          plot_bgcolor: 'rgba(0,0,0,0)'
                        }}
                      />
                    </div>
                  </div>
                ) : (
                  <div>
                    <h3 className="font-bold text-sm text-slate-700 mb-2">Topografisk Längdprofil</h3>
                    <div className="flex flex-col items-center justify-center h-[300px] bg-white/50 rounded-2xl border border-white/50 shadow-inner">
                      <p className="text-slate-500 text-sm font-medium">Rita en bana (Path) på stenen</p>
                      <p className="text-slate-400 text-xs mt-1">för att se spårdjupet längs skåran.</p>
                    </div>
                  </div>
                )}
              </div>
              
              <div className="mt-6 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                💡 Tips: Dra en rektangel i graferna för att zooma &nbsp;&bull;&nbsp; Dubbelklicka för att återställa
              </div>
            </div>
          )}

          {results && (
             <div className="flex justify-end animate-in fade-in slide-in-from-bottom-8">
               <button 
                 onClick={handleSaveProject}
                 className="px-8 py-4 bg-[#b7410e] hover:bg-[#9a350b] text-white font-bold rounded-2xl shadow-lg transition-transform active:scale-95 flex items-center gap-2"
               >
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M17.593 3.322c1.1.128 1.907 1.077 1.907 2.185V21L12 17.25 4.5 21V5.507c0-1.108.806-2.057 1.907-2.185a48.507 48.507 0 0111.186 0z" />
                  </svg>
                 Spara snitt i Projekt
               </button>
             </div>
          )}
          
        </div>

      </div>
    </div>
  );
}

export default function ThreeDPage() {
  // useSearchParams() requires a Suspense boundary for static prerendering
  return (
    <Suspense fallback={null}>
      <ThreeDPageContent />
    </Suspense>
  );
}
