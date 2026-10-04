"use client";

import { useState, useEffect, useEffectEvent, useRef, Suspense } from "react";
import PlotlyGraph from "@/components/PlotlyGraph";
import { toJpeg } from 'html-to-image';
import { useLanguage } from "@/components/LanguageContext";
import { useAnalysis } from "@/components/AnalysisContext";
import { useSettings } from "@/components/SettingsContext";
import { useRouter, useSearchParams } from "next/navigation";
import { dataURLToFile } from "@/lib/images";
import Link from "next/link";
import { db, ProjectData } from "@/lib/db";
import GrooveResultsPanel from "@/components/GrooveResultsPanel";
import { fromSession } from "@/lib/stoneReport";
import AutoGrooveReview from "@/components/AutoGrooveReview";
import type { SliceMarker, Vec3, ViewDirection, ViewerPoint } from "@/components/ThreeDViewer";
import { MeshSession, type AutoAnalysisResult, type AutoLabel, type MeshInfo } from "@/lib/mesh";
import type { ThreeDAnalysisResult } from "@/lib/db";
import { METRICS, type SliceMetrics } from "@/lib/metrics";
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
    setLatest2DImage,
    setLatest2DFile,
    setLatest2DSource,
    setLatest2DResults,
    setStoneReportInput,
  } = useAnalysis();
  const router = useRouter();

  // Send the groove map of the automatic analysis to the 2D page, with the measured slices,
  // so that rune crops drawn there get the groove measurements inside them
  const sendGrooveMapToTwoD = async (labels: AutoLabel[]) => {
    if (!autoResult) return;
    const W = autoResult.image_width, H = autoResult.image_height;
    const autoSlices = autoResult.slices.flatMap((sl, i) => (sl.accepted && labels[i] !== "excluded"
      ? [{ x: sl.img_x / W, y: sl.img_y / H, metrics: Object.fromEntries(METRICS.map(m => [m, sl[m] as number])) }]
      : []));
    setLatest2DImage(autoResult.groove_map_base64);
    setLatest2DFile(await dataURLToFile(autoResult.groove_map_base64, "ristningskarta.png"));
    setLatest2DSource({
      kind: "groove-map", description: metaText || file?.name, autoSlices,
      methodVersion: autoResult.provenance.method_version,
    });
    setLatest2DResults(null);
    router.push("/2d");
  };

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
  // How the cross-section was chosen; analysing without a selection would slice through the stone's centre
  const [selection, setSelection] = useState<"none" | "line" | "path" | "manual">("none");
  
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

  // The scan is uploaded once to the analysis engine and referred to by id
  const sessionRef = useRef<MeshSession | null>(null);
  const [meshInfo, setMeshInfo] = useState<MeshInfo | null>(null);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  type MeasureMode = "manual" | "oneclick" | "auto";
  const [measureMode, setMeasureMode] = useState<MeasureMode>("oneclick");
  const viewDirRef = useRef<ViewDirection | null>(null);

  // One click per slice
  const [clickMarkers, setClickMarkers] = useState<SliceMarker[]>([]);
  const [clickSlices, setClickSlices] = useState<SliceMetrics[]>([]);
  const [clickSelections, setClickSelections] = useState<Record<string, unknown>[]>([]);
  const [clickBusy, setClickBusy] = useState(false);
  const [clickMessage, setClickMessage] = useState<string | null>(null);

  // Automatic analysis
  const [autoResult, setAutoResult] = useState<AutoAnalysisResult | null>(null);
  const [autoLabels, setAutoLabels] = useState<AutoLabel[]>([]);
  const [autoBusy, setAutoBusy] = useState(false);
  const [autoError, setAutoError] = useState<string | null>(null);
  const [autoSpacing, setAutoSpacing] = useState(3);
  const [autoSensitivity, setAutoSensitivity] = useState(3);
  const [autoMaxWidth, setAutoMaxWidth] = useState(16);
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

  const errorText = (err: unknown, fallback: string) => (err instanceof Error ? err.message : fallback);

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    const session = sessionRef.current;
    if (!session) return;
    setLoading(true);
    setResults(null);
    const common = {
      up_x: up[0], up_y: up[1], up_z: up[2],
      meta_stone: metaStone, meta_weathering: metaWeathering, feature_type: featureType,
    };
    try {
      const data = pathPoints && pathPoints.length > 2
        ? await session.postJSON<ThreeDAnalysisResult>("/api/3d/analyze_path", { ...common, path_points_json: JSON.stringify(pathPoints) })
        : await session.postJSON<ThreeDAnalysisResult>("/api/3d/analyze", {
            ...common,
            origin_x: origin[0], origin_y: origin[1], origin_z: origin[2],
            dir_x: direction[0], dir_y: direction[1], dir_z: direction[2],
            slice_count: sliceCount, slice_spacing_mm: 1.0, meta_text: metaText,
          });
      setResults(data);
    } catch (err) {
      console.error(err);
      alert(errorText(err, "Något gick fel vid 3D-analysen."));
    } finally {
      setLoading(false);
    }
  };

  // ---- One click per slice -------------------------------------------------------------
  const summarizeSlices = async (slices: SliceMetrics[]) => {
    const res = await fetch(`${API_URL}/api/stats/summarize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ slices, meta_stone: metaStone, meta_weathering: metaWeathering }),
    });
    if (!res.ok) throw new Error((await res.json().catch(() => null))?.detail || "Sammanfattningen misslyckades");
    return res.json();
  };

  const handleSingleClick = async (point: Vec3, normal: Vec3) => {
    const session = sessionRef.current;
    if (!session || clickBusy) return;
    setClickBusy(true);
    setClickMessage(null);
    try {
      const data = await session.postJSON<ThreeDAnalysisResult & { selection: { origin: Vec3; direction: Vec3; up: Vec3; across: Vec3; window_mm: number } }>(
        "/api/3d/auto_slice",
        {
          point_x: point[0], point_y: point[1], point_z: point[2],
          normal_x: normal[0], normal_y: normal[1], normal_z: normal[2],
          slice_count: sliceCount, meta_stone: metaStone, meta_weathering: metaWeathering, feature_type: featureType,
        },
      );
      const sel = data.selection;
      const half = (data.results.spårbredd_mm || sel.window_mm / 2) * 0.75;
      const marker: SliceMarker = {
        from: sel.origin.map((v, i) => v - sel.across[i] * half) as Vec3,
        to: sel.origin.map((v, i) => v + sel.across[i] * half) as Vec3,
      };
      const allSlices = [...clickSlices, ...(data.slices ?? [])];
      const selections = [...clickSelections, { click: point, ...sel }];
      const summary = await summarizeSlices(allSlices);
      setClickMarkers([...clickMarkers, marker]);
      setClickSlices(allSlices);
      setClickSelections(selections);
      setResults({
        ...data,
        results: { ...data.results, ...summary.means, troligt_verktyg: summary.tool_heuristic.label },
        summary: summary.summary,
        slices: allSlices,
        tool_heuristic: summary.tool_heuristic,
        provenance: data.provenance && {
          ...data.provenance,
          parameters: { mode: "one-click", clicks: selections.length, slices_per_click: sliceCount, selections },
        },
      });
    } catch (err) {
      setClickMessage(errorText(err, "Kunde inte mäta vid klicket."));
    } finally {
      setClickBusy(false);
    }
  };

  const clearClicks = () => {
    setClickMarkers([]);
    setClickSlices([]);
    setClickSelections([]);
    setClickMessage(null);
    setResults(null);
  };

  // ---- Automatic analysis ----------------------------------------------------------------
  const runAutoAnalysis = async () => {
    const session = sessionRef.current;
    const view = viewDirRef.current;
    if (!session) return;
    if (!view) {
      setAutoError("3D-vyn är inte redo ännu. Vänta tills stenen visas och försök igen.");
      return;
    }
    setAutoBusy(true);
    setAutoError(null);
    setAutoResult(null);
    try {
      const data = await session.postJSON<AutoAnalysisResult>("/api/3d/auto_analyze", {
        normal_x: view.toward[0], normal_y: view.toward[1], normal_z: view.toward[2],
        up_x: view.up[0], up_y: view.up[1], up_z: view.up[2],
        spacing_mm: autoSpacing, sensitivity: autoSensitivity, max_halfwidth_mm: autoMaxWidth / 2,
        meta_stone: metaStone, meta_weathering: metaWeathering,
      });
      setAutoResult(data);
      setAutoLabels(data.slices.map(sl => (sl.accepted ? "unknown" : "excluded")));
      if (data.counts.accepted === 0) {
        setAutoError("Inga spår kunde mätas på den sida som vetter mot dig. Kontrollera att den ristade sidan är vänd mot kameran, eller prova högre känslighet.");
      }
    } catch (err) {
      setAutoError(errorText(err, "Den automatiska analysen misslyckades."));
    } finally {
      setAutoBusy(false);
    }
  };

  const LABEL_COLORS: Record<AutoLabel, string> = { rune: "#b7410e", ornament: "#0369a1", unknown: "#0f172a", excluded: "#94a3b8" };
  const autoPoints: ViewerPoint[] = autoResult
    ? autoResult.slices.flatMap((sl, i) => (sl.accepted && sl.point ? [{ position: sl.point, color: LABEL_COLORS[autoLabels[i] ?? "unknown"] }] : []))
    : [];

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
    // Send image, file and source to the 2D analysis (the file is needed to analyse it there)
    setLatest2DImage(binarizedBase64);
    setLatest2DFile(await dataURLToFile(binarizedBase64, "3d_ogonblicksbild.png"));
    setLatest2DSource({ kind: "3d-snapshot", description: metaText || file?.name });
    setLatest2DResults(null);
    router.push("/2d");
  };

  const handleAutoSnapRequest = async (points: [number, number, number][]): Promise<[number, number, number][]> => {
    const session = sessionRef.current;
    if (!session) throw new Error("Ladda upp en 3D-fil först.");
    const data = await session.postJSON<{ snapped_path: [number, number, number][] }>("/api/3d/auto_snap_path", {
      path_points_json: JSON.stringify(points), up_x: up[0], up_y: up[1], up_z: up[2],
    });
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

  const prepareViewModel = async (session: MeshSession, name: string) => {
    setPreparingView(true);
    try {
      const res = await session.post("/api/3d/view_model", {});
      const blob = await res.blob();
      setViewFile(new File([blob], name.replace(/\.[^.]+$/, "") + "_visning.stl", { type: "model/stl" }));
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
    setSelection("none");
    setPathPoints(null);
    setResults(null);
    setMeshInfo(null);
    setUploadError(null);
    setClickMarkers([]);
    setClickSlices([]);
    setClickSelections([]);
    setAutoResult(null);
    sessionRef.current = null;
    if (!selectedFile) return;

    const session = new MeshSession(selectedFile, fraction => setUploadProgress(fraction));
    sessionRef.current = session;
    const isLarge = selectedFile.size > LARGE_FILE_BYTES;
    if (isLarge) setPreparingView(true);
    setUploadProgress(0);
    session.ensure()
      .then(info => {
        if (sessionRef.current !== session) return;
        setMeshInfo(info);
        if (isLarge) prepareViewModel(session, selectedFile.name);
      })
      .catch(err => {
        if (sessionRef.current !== session) return;
        setUploadError(errorText(err, "Uppladdningen misslyckades."));
        setPreparingView(false);
      })
      .finally(() => setUploadProgress(null));

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

  // What is still missing before a measurement can be made, for the status box
  const uploadDone = !!meshInfo;
  const steps: { done: boolean; text: string }[] = [
    {
      done: uploadDone,
      text: !file ? "Ladda upp en 3D-skanning (STL, OBJ eller PLY)."
        : uploadError ? `Uppladdningen misslyckades: ${uploadError}`
        : uploadProgress !== null && uploadProgress < 1 ? `Laddar upp till analysmotorn … ${Math.round(uploadProgress * 100)} %`
        : !uploadDone ? "Analysmotorn läser in modellen …"
        : `Modellen är inläst (${meshInfo!.faces.toLocaleString("sv-SE")} ytor).`,
    },
    measureMode === "manual"
      ? { done: selection !== "none", text: selection !== "none" ? "Spår markerat." : "Håll Shift och klicka två punkter tvärs över ett spår, eller flera längs spåret." }
      : measureMode === "oneclick"
      ? { done: clickMarkers.length > 0, text: clickMarkers.length > 0 ? `${clickMarkers.length} snitt mätta (${clickSlices.length} tvärsnitt).` : "Håll Shift och klicka mitt i ett spår – varje klick mäter ett snitt." }
      : { done: !!autoResult, text: autoResult ? "Automatisk analys klar – granska resultatet nedan." : "Vrid stenen så att den ristade sidan vetter mot dig och starta analysen." },
  ];

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

            {file && (
              <div>
                <label className="block text-slate-500 text-[12px] mb-2 font-bold uppercase tracking-wider">Mätsätt</label>
                <div className="grid grid-cols-3 gap-1 bg-slate-900/5 p-1 rounded-xl">
                  {([["oneclick", "Ett klick"], ["manual", "Manuellt"], ["auto", "Automatiskt"]] as const).map(([mode, name]) => (
                    <button key={mode} type="button" onClick={() => setMeasureMode(mode)}
                      className={`py-2 rounded-lg text-xs font-bold transition-all ${measureMode === mode ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:text-slate-800"}`}>
                      {name}
                    </button>
                  ))}
                </div>
                <p className="text-[11px] text-slate-500 mt-1.5">
                  {measureMode === "oneclick" && "Klicka i ett spår – appen hittar riktning och botten och mäter direkt."}
                  {measureMode === "manual" && "Du väljer själv snittets läge med två punkter, eller en bana längs spåret."}
                  {measureMode === "auto" && "Appen hittar alla spår på den sida som vetter mot dig och mäter med jämna mellanrum."}
                </p>
              </div>
            )}

            <div className="rounded-xl border border-slate-200 bg-white/70 p-3 space-y-1.5">
              <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Status</div>
              {steps.map((st, i) => (
                <div key={i} className={`flex gap-2 text-xs ${st.done ? "text-emerald-700" : i === 0 && uploadError ? "text-red-700" : "text-slate-700"}`}>
                  <span className="font-bold w-4 flex-shrink-0">{st.done ? "✓" : `${i + 1}.`}</span>
                  <span>{st.text}</span>
                </div>
              ))}
              {measureMode === "oneclick" && clickBusy && <div className="text-xs text-slate-600">Mäter …</div>}
              {measureMode === "oneclick" && clickMessage && <div className="text-xs text-amber-800">{clickMessage}</div>}
            </div>

            {measureMode === "auto" && file && (
              <div className="space-y-3 rounded-xl border border-slate-200 bg-white/70 p-3">
                <div className="grid grid-cols-3 gap-2">
                  <label className="text-[11px] font-bold text-slate-500">Avstånd
                    <select value={autoSpacing} onChange={e => setAutoSpacing(+e.target.value)} className="mt-1 w-full liquid-glass-input-wrapper rounded-lg px-2 py-1.5 text-xs font-semibold outline-none">
                      {[2, 3, 5, 8].map(v => <option key={v} value={v}>{v} mm</option>)}
                    </select>
                  </label>
                  <label className="text-[11px] font-bold text-slate-500">Känslighet
                    <select value={autoSensitivity} onChange={e => setAutoSensitivity(+e.target.value)} className="mt-1 w-full liquid-glass-input-wrapper rounded-lg px-2 py-1.5 text-xs font-semibold outline-none">
                      <option value={4}>Låg</option><option value={3}>Normal</option><option value={2}>Hög</option>
                    </select>
                  </label>
                  <label className="text-[11px] font-bold text-slate-500">Max bredd
                    <select value={autoMaxWidth} onChange={e => setAutoMaxWidth(+e.target.value)} className="mt-1 w-full liquid-glass-input-wrapper rounded-lg px-2 py-1.5 text-xs font-semibold outline-none">
                      {[10, 16, 24, 32].map(v => <option key={v} value={v}>{v} mm</option>)}
                    </select>
                  </label>
                </div>
                <button type="button" onClick={runAutoAnalysis} disabled={!uploadDone || autoBusy}
                  className="w-full py-3 bg-slate-900 hover:bg-black text-white font-semibold text-sm rounded-xl disabled:opacity-40 flex justify-center items-center gap-2">
                  {autoBusy ? (<><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Analyserar stenen …</>) : "Kör automatisk analys"}
                </button>
                {autoError && <p className="text-xs text-amber-800">{autoError}</p>}
              </div>
            )}

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
                        <input type="number" step="0.1" value={vec.state[0]} onChange={e => { vec.set([+e.target.value, vec.state[1], vec.state[2]]); setSelection("manual"); }} className="w-full liquid-glass-input-wrapper rounded-xl px-2.5 py-2 text-slate-900 text-center text-xs font-semibold outline-none transition-all" />
                        <input type="number" step="0.1" value={vec.state[1]} onChange={e => { vec.set([vec.state[0], +e.target.value, vec.state[2]]); setSelection("manual"); }} className="w-full liquid-glass-input-wrapper rounded-xl px-2.5 py-2 text-slate-900 text-center text-xs font-semibold outline-none transition-all" />
                        <input type="number" step="0.1" value={vec.state[2]} onChange={e => { vec.set([vec.state[0], vec.state[1], +e.target.value]); setSelection("manual"); }} className="w-full liquid-glass-input-wrapper rounded-xl px-2.5 py-2 text-slate-900 text-center text-xs font-semibold outline-none transition-all" />
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

            {measureMode === "manual" && (
            <button 
              type="submit" 
              disabled={loading || !uploadDone || selection === "none"}
              title={!file ? "Ladda upp en 3D-fil först" : !uploadDone ? "Väntar på att modellen ska läsas in" : selection === "none" ? "Markera ett spår först" : undefined}
              className="w-full py-3.5 bg-slate-900 hover:bg-black active:scale-[0.98] disabled:opacity-40 text-white font-semibold text-sm rounded-2xl transition-all shadow-lg flex justify-center items-center gap-2 mt-4"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  {t.threed.calculating}
                </>
              ) : t.threed.analyze_btn}
            </button>
            )}
          </form>
        </div>

        {/* Results Area */}
        <div className="lg:col-span-2 space-y-8 flex flex-col">
          
          {/* Interactive 3D Viewer */}
          <div className="liquid-glass-island rounded-[36px] p-2 h-[600px] xl:h-[700px] flex-shrink-0 relative group shadow-sm border border-white/50">
            <ThreeDViewer 
              file={viewFile ?? (preparingView ? null : file)} 
              preCentered={!!viewFile}
              emptyMessage={preparingView ? "Stor fil – skapar en lättare visningsmodell (kan ta en minut)..." : undefined}
              onVectorSelected={(o, d, normal) => {
                setOrigin(o);
                setDirection(d);
                if (normal) setUp(normal);
                setPathPoints(null);
                setSelection("line");
              }}
              onPathSelected={(pts, normal) => {
                setPathPoints(pts);
                if (normal) setUp(normal);
                setSelection("path");
              }}
              clickMode={measureMode === "oneclick" ? "single" : measureMode === "auto" ? "view" : "points"}
              onSingleClick={handleSingleClick}
              onClearMarkers={clearClicks}
              markers={measureMode === "oneclick" ? clickMarkers : undefined}
              autoPoints={measureMode === "auto" ? autoPoints : undefined}
              viewDirRef={viewDirRef}
              onAutoSnapRequest={handleAutoSnapRequest}
              cutoffDepth={cutoffDepth}
              layerThickness={layerThickness}
              slicerMode={slicerMode}
            />
          </div>

          {measureMode === "auto" && autoResult && autoResult.counts.accepted > 0 && (
            <AutoGrooveReview
              result={autoResult}
              signum={metaText}
              metaStone={metaStone}
              metaWeathering={metaWeathering}
              labels={autoLabels}
              onLabelsChange={setAutoLabels}
              onUse={(r, ft) => { setFeatureType(ft); setResults(r); }}
              onSendToTwoD={() => sendGrooveMapToTwoD(autoLabels)}
            />
          )}

          {(results || (autoResult && autoResult.counts.accepted > 0)) && (
            <div className="liquid-glass-island rounded-[28px] px-6 py-4 flex flex-wrap items-center gap-3">
              <div className="flex-1 min-w-[240px]">
                <p className="text-sm font-bold text-slate-900">Stenrapport</p>
                <p className="text-xs text-slate-600">
                  Ett artikelutkast om stenen med strykljus, djupkarta, snittpositioner, tvärsnittsprofiler och mått –
                  räknat direkt ur skanningen{autoResult ? ", med runor och ornamentik var för sig" : ""}.
                </p>
              </div>
              <button
                onClick={() => {
                  const input = fromSession({
                    meta, meshId: meshInfo?.mesh_id, autoResult, autoLabels, results, featureType, project: activeProject,
                  });
                  if (!input) { alert("Det finns inga godkända tvärsnitt att rapportera."); return; }
                  setStoneReportInput(input);
                  router.push("/rapporter?typ=sten");
                }}
                className="px-5 py-2.5 bg-[#b7410e] hover:bg-[#9a350b] text-white text-sm font-bold rounded-xl"
              >
                Skapa stenrapport
              </button>
            </div>
          )}

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
