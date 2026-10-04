/* eslint-disable @next/next/no-img-element */

"use client";

import { useState, useEffect, useRef } from "react";
import { db, ProjectData } from "@/lib/db";
import { useAnalysis } from "@/components/AnalysisContext";
import { useSettings } from "@/components/SettingsContext";
import { useAuth } from "@/components/AuthContext";
import ReactCrop, { type Crop } from 'react-image-crop';
import 'react-image-crop/dist/ReactCrop.css';
import { API_URL } from "@/lib/api";

export default function PhoneticsPage() {
  const [projects, setProjects] = useState<ProjectData[]>([]);
  const [selectedProject, setSelectedProject] = useState<ProjectData | null>(null);
  
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imageBase64, setImageBase64] = useState<string>("");
  
  const [crop, setCrop] = useState<Crop>();
  const [completedCrop, setCompletedCrop] = useState<Crop | null>(null);
  const [brightness, setBrightness] = useState(100);
  const [contrast, setContrast] = useState(100);
  const [channel, setChannel] = useState<'all' | 'r' | 'g' | 'b'>('all');
  const imgRef = useRef<HTMLImageElement>(null);
  // Rendered image size, tracked so marker overlays reposition on resize
  const [imgSize, setImgSize] = useState({ width: 1, height: 1 });
  useEffect(() => {
    const img = imgRef.current;
    if (!img) return;
    const observer = new ResizeObserver(() => {
      setImgSize({ width: img.width || 1, height: img.height || 1 });
    });
    observer.observe(img);
    return () => observer.disconnect();
  }, [imageBase64]);
  
  const [isDrawingMode, setIsDrawingMode] = useState(false);
  const isDrawingRef = useRef(false);
  const drawCanvasRef = useRef<HTMLCanvasElement>(null);

  const [loading, setLoading] = useState(false);
  const [isRendering3D, setIsRendering3D] = useState(false);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [results, setResults] = useState<import("@/lib/db").LinguisticResultData | null>(null);

  const [region, setRegion] = useState("");
  const [epoch, setEpoch] = useState("");
  
  const { geminiKey, openaiKey, addUsedTokens } = useSettings();
  const { 
    latest2DFile, 
    latest2DImage,
    latest3DMeta,
    setLatest3DMeta,
    activeProjectId,
    setActiveProjectId,
    setLatestLinguisticResults
  } = useAnalysis();


  const { user } = useAuth();

  useEffect(() => {
    const load = async () => {
      setProjects(await db.getProjects());
    };
    load();
  }, [user]);

  const handleProjectSelect = (id: string) => {
    const proj = projects.find(p => p.id === id);
    if (proj) {
      setSelectedProject(proj);
      setActiveProjectId(proj.id);
      if (proj.metaText) {
        setLatest3DMeta({ ...latest3DMeta, text: proj.metaText });
      }
      setResults(null);
    }
  };

  const handleSaveProject = async () => {
    if (!results) return;
    
    let projectIdToSaveTo = activeProjectId || selectedProject?.id;
    
    // Auto-grouping by signum
    if (!projectIdToSaveTo && latest3DMeta.text) {
      const existingProj = await db.getProjectBySignum(latest3DMeta.text);
      if (existingProj) {
        projectIdToSaveTo = existingProj.id;
      }
    }

    let projectUpdate: Partial<ProjectData> = {
      linguisticResults: results,
    };
    
    if (!projectIdToSaveTo) {
      // New project
      projectUpdate = {
        ...projectUpdate,
        name: latest3DMeta.text || (imageFile ? imageFile.name : "Nytt Projekt (Fonetik)"),
        fileName: imageFile ? imageFile.name : "Bild",
        metaStone: latest3DMeta.stone || "Okänd",
        metaWeathering: latest3DMeta.weathering || "Låg",
        metaText: latest3DMeta.text || "",
        slices: [],
      };
    } else {
      projectUpdate.id = projectIdToSaveTo;
      if (latest3DMeta.text) {
         projectUpdate.metaText = latest3DMeta.text;
         projectUpdate.name = latest3DMeta.text;
      }
    }
    
    const saved = await db.saveProject(projectUpdate);
    setActiveProjectId(saved.id);
    setSelectedProject(saved);
    setLatestLinguisticResults(results);
    alert(`Fonetik-data sparat till projekt: ${saved.name}`);
  };
  
  const resetImageState = () => {
    setCrop(undefined);
    setCompletedCrop(null);
    setBrightness(100);
    setContrast(100);
    setChannel('all');
    if (drawCanvasRef.current) {
      const ctx = drawCanvasRef.current.getContext('2d');
      ctx?.clearRect(0, 0, drawCanvasRef.current.width, drawCanvasRef.current.height);
    }
  };

  const handle3DUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    setIsRendering3D(true);
    setResults(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("resolution", "800");
      
      const res = await fetch(`${API_URL}/api/3d/render_depth_map`, {
        method: "POST",
        body: formData,
      });
      
      if (!res.ok) throw new Error("API fel vid rendering");
      
      const data = await res.json();
      setImageBase64(data.image_base64);
    } catch (err) {
      console.error(err);
      alert("Kunde inte rendera 3D-filen.");
    } finally {
      setIsRendering3D(false);
    }
  };

  const handlePointerDown = (e: React.PointerEvent<HTMLCanvasElement>) => {
    if (!isDrawingMode || !drawCanvasRef.current || !imgRef.current) return;
    isDrawingRef.current = true;
    const canvas = drawCanvasRef.current;
    const img = imgRef.current;
    
    if (canvas.width !== img.naturalWidth || canvas.height !== img.naturalHeight) {
      canvas.width = img.naturalWidth;
      canvas.height = img.naturalHeight;
    }
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    
    const x = (e.clientX - rect.left) * scaleX;
    const y = (e.clientY - rect.top) * scaleY;
    
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.strokeStyle = 'rgba(239, 68, 68, 0.5)'; // Semi-transparent red
    ctx.lineWidth = Math.max(10, canvas.width / 80);
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
  };

  const handlePointerMove = (e: React.PointerEvent<HTMLCanvasElement>) => {
    if (!isDrawingMode || !isDrawingRef.current || !drawCanvasRef.current) return;
    const canvas = drawCanvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    
    const x = (e.clientX - rect.left) * scaleX;
    const y = (e.clientY - rect.top) * scaleY;
    
    ctx.lineTo(x, y);
    ctx.stroke();
  };

  const handlePointerUp = () => {
    isDrawingRef.current = false;
  };

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setImageFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImageBase64(reader.result as string);
        resetImageState();
      };
      reader.readAsDataURL(file);
    }
  };

  const handleUseLatest2DImage = () => {
    if (latest2DFile && latest2DImage) {
      setImageFile(latest2DFile);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImageBase64(reader.result as string);
        resetImageState();
      };
      reader.readAsDataURL(latest2DFile);
    }
  };

  const getProcessedImageBase64 = async (): Promise<string | null> => {
    const image = imgRef.current;
    if (!image) return null;

    const canvas = document.createElement("canvas");
    const scaleX = image.naturalWidth / image.width;
    const scaleY = image.naturalHeight / image.height;

    const isCropped = completedCrop && completedCrop.width > 0 && completedCrop.height > 0;
    const cropWidth = isCropped ? completedCrop.width * scaleX : image.naturalWidth;
    const cropHeight = isCropped ? completedCrop.height * scaleY : image.naturalHeight;
    const cropX = isCropped ? completedCrop.x * scaleX : 0;
    const cropY = isCropped ? completedCrop.y * scaleY : 0;

    canvas.width = cropWidth;
    canvas.height = cropHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return null;

    ctx.filter = `brightness(${brightness}%) contrast(${contrast}%)`;
    ctx.drawImage(
      image,
      cropX,
      cropY,
      cropWidth,
      cropHeight,
      0,
      0,
      cropWidth,
      cropHeight
    );

    ctx.filter = 'none'; // reset filter for overlay

    if (drawCanvasRef.current && drawCanvasRef.current.width > 0) {
      const dCanvas = drawCanvasRef.current;
      // The draw canvas is natural size, just like the uncropped image
      ctx.drawImage(
        dCanvas,
        cropX, cropY, cropWidth, cropHeight,
        0, 0, cropWidth, cropHeight
      );
    }

    if (channel !== 'all') {
      const imageData = ctx.getImageData(0, 0, cropWidth, cropHeight);
      const data = imageData.data;
      for (let i = 0; i < data.length; i += 4) {
        let val = 0;
        if (channel === 'r') val = data[i];
        else if (channel === 'g') val = data[i+1];
        else if (channel === 'b') val = data[i+2];
        
        data[i] = val;
        data[i+1] = val;
        data[i+2] = val;
      }
      ctx.putImageData(imageData, 0, 0);
    }

    return canvas.toDataURL("image/jpeg", 0.95);
  };

  const handleAnalyze = async () => {
    if (!imageBase64) {
      alert("Ladda upp en referensbild först.");
      return;
    }
    
    setLoading(true);
    setResults(null);

    const processedBase64 = await getProcessedImageBase64();
    if (!processedBase64) {
      alert("Kunde inte processa bilden.");
      setLoading(false);
      return;
    }

    try {
      const res = await fetch(`${API_URL}/api/phonetics/analyze`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "X-Gemini-Api-Key": geminiKey
        },
        body: JSON.stringify({
          image_base64: processedBase64,
          signum: selectedProject?.metaText || "Okänt",
          region: region || undefined,
          epoch: epoch || undefined,
        })
      });
      
      if (!res.ok) throw new Error("API fel vid fonetisk analys");
      
      const data = await res.json();
      setResults(data);
      if (data.tokens_used) {
        addUsedTokens(data.tokens_used);
      }
    } catch (err) {
      console.error(err);
      alert("Något gick fel med den språkliga analysen.");
    } finally {
      setLoading(false);
    }
  };

  const handlePlayAudio = async () => {
    if (!results || !results.phonetic_ipa) return;
    setIsPlayingAudio(true);
    try {
      const res = await fetch(`${API_URL}/api/phonetics/speak`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-OpenAI-Api-Key": openaiKey
        },
        body: JSON.stringify({ text: results.normalization })
      });
      
      if (!res.ok) {
        throw new Error("Kunde inte generera ljud. Kolla din OpenAI API-nyckel.");
      }
      
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audio.play();
      
      audio.onended = () => {
        setIsPlayingAudio(false);
      };
    } catch (e) {
      console.error(e);
      alert("Kunde inte spela upp ljudet. Har du lagt in en giltig OpenAI-nyckel i inställningarna?");
      setIsPlayingAudio(false);
    }
  };

  return (
    <>
      <svg width="0" height="0" className="absolute pointer-events-none">
        <filter id="channel-r">
          <feColorMatrix type="matrix" values="1 0 0 0 0  1 0 0 0 0  1 0 0 0 0  0 0 0 1 0" />
        </filter>
        <filter id="channel-g">
          <feColorMatrix type="matrix" values="0 1 0 0 0  0 1 0 0 0  0 1 0 0 0  0 0 0 1 0" />
        </filter>
        <filter id="channel-b">
          <feColorMatrix type="matrix" values="0 0 1 0 0  0 0 1 0 0  0 0 1 0 0  0 0 0 1 0" />
        </filter>
      </svg>
      <div className="flex flex-col h-full w-full max-w-7xl mx-auto p-4 md:p-6 relative z-10 overflow-y-auto">
        <div className="mb-8">
          <h2 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">Språk & Fonetik</h2>
          <p className="text-slate-600 text-[16px] leading-relaxed max-w-3xl font-medium">
            Ladda upp ett 2D-foto av runstenen för att låta Vitki Vision-AI läsa och tolka texten opartiskt. 
            Resultatet inkluderar fornöstnordisk normalisering och IPA-rekonstruktion.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="liquid-glass-island rounded-[36px] p-8 h-fit space-y-8">
            <div>
              <label className="block text-slate-500 text-[12px] mb-2 font-bold uppercase tracking-wider">
                Välj Projekt (Valfritt)
              </label>
              <select 
                className="w-full liquid-glass-input-wrapper rounded-xl px-4 py-2.5 text-slate-900 text-sm font-semibold outline-none"
                onChange={(e) => handleProjectSelect(e.target.value)}
                value={selectedProject?.id || ""}
              >
                <option value="" disabled>Välj ett sparat projekt...</option>
                {projects.map(p => (
                  <option key={p.id} value={p.id}>{p.name} ({p.metaText || "Inget signum"})</option>
                ))}
              </select>
            </div>
            
            <div className="flex gap-4">
              <div className="flex-1">
                <label className="block text-slate-500 text-[12px] mb-2 font-bold uppercase tracking-wider">
                  Region (Dialekt)
                </label>
                <select 
                  className="w-full liquid-glass-input-wrapper rounded-xl px-4 py-2.5 text-slate-900 text-sm font-semibold outline-none"
                  value={region}
                  onChange={(e) => setRegion(e.target.value)}
                >
                  <option value="">Auto-detektera...</option>
                  <option value="Svealand">Svealand (Södermanland, Uppland, Västmanland)</option>
                  <option value="Götaland">Götaland (Östergötland, Västergötland, Småland)</option>
                  <option value="Gotland">Gotland (Gutniska)</option>
                  <option value="Skåneland">Skåneland (Dansk påverkan)</option>
                  <option value="Norge">Norge</option>
                </select>
              </div>
              
              <div className="flex-1">
                <label className="block text-slate-500 text-[12px] mb-2 font-bold uppercase tracking-wider">
                  Epok (Tid)
                </label>
                <select 
                  className="w-full liquid-glass-input-wrapper rounded-xl px-4 py-2.5 text-slate-900 text-sm font-semibold outline-none"
                  value={epoch}
                  onChange={(e) => setEpoch(e.target.value)}
                >
                  <option value="">Auto-detektera...</option>
                  <option value="Urnordisk tid (150-800)">Urnordisk tid (150-800 e.Kr)</option>
                  <option value="Tidig Vikingatid (800-950)">Tidig Vikingatid (800-950)</option>
                  <option value="Sen Vikingatid (950-1100)">Sen Vikingatid (950-1100)</option>
                  <option value="Medeltid (1100-1500)">Medeltid (1100-1500)</option>
                  <option value="Eftermedeltida (1500+)">Eftermedeltida (1500+)</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-slate-500 text-[12px] mb-2 font-bold uppercase tracking-wider">
                1. Ladda upp referensbild (Foto)
              </label>
              <div className="relative overflow-hidden flex flex-col gap-3">
                <input 
                  type="file" 
                  accept="image/*"
                  onChange={handleImageUpload}
                  className="w-full text-slate-900 text-xs file:mr-4 file:py-2 file:px-5 file:rounded-full file:border-0 file:font-semibold transition-all cursor-pointer bg-white border border-slate-200 rounded-2xl p-2"
                />
                {latest2DFile && (
                  <button 
                    onClick={handleUseLatest2DImage}
                    className="text-xs font-semibold text-[#b7410e] hover:text-[#91320b] flex items-center gap-1 transition-colors self-start bg-[#b7410e]/10 py-1.5 px-3 rounded-full"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
                    </svg>
                    Använd fil från 2D-analysen
                  </button>
                )}
              </div>
              
              <div className="mt-4 pt-4 border-t border-slate-900/5">
                <label className="block text-slate-500 text-[12px] mb-2 font-bold uppercase tracking-wider">
                  ...eller generera från 3D-skanning
                </label>
                <div className="relative overflow-hidden flex flex-col gap-3">
                  <input 
                    type="file" 
                    accept=".obj,.stl"
                    onChange={handle3DUpload}
                    disabled={isRendering3D}
                    className="w-full text-slate-900 text-xs file:mr-4 file:py-2 file:px-5 file:rounded-full file:border-0 file:font-semibold transition-all cursor-pointer bg-white border border-slate-200 rounded-2xl p-2 disabled:opacity-50"
                  />
                  {isRendering3D && (
                    <div className="text-xs font-semibold text-emerald-600 flex items-center gap-2">
                      <div className="w-3 h-3 border-2 border-emerald-200 border-t-emerald-600 rounded-full animate-spin" />
                      Renderar 2D-djupkarta från 3D-modell...
                    </div>
                  )}
                </div>
              </div>
            </div>

            {imageBase64 && (
              <div className="flex flex-col gap-4 w-full">
                <div className="flex gap-6 w-full">
                  <div className="flex-1 flex flex-col gap-2">
                    <div className="flex justify-between items-center">
                      <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Ljusstyrka</label>
                      <span className="text-[10px] font-bold text-slate-700 bg-slate-100 px-2 py-0.5 rounded-full">{brightness}%</span>
                    </div>
                    <input type="range" min="50" max="200" value={brightness} onChange={e => setBrightness(Number(e.target.value))} className="w-full accent-emerald-600" />
                  </div>
                  <div className="flex-1 flex flex-col gap-2">
                    <div className="flex justify-between items-center">
                      <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Kontrast</label>
                      <span className="text-[10px] font-bold text-slate-700 bg-slate-100 px-2 py-0.5 rounded-full">{contrast}%</span>
                    </div>
                    <input type="range" min="50" max="250" value={contrast} onChange={e => setContrast(Number(e.target.value))} className="w-full accent-emerald-600" />
                  </div>
                </div>
                <div className="flex flex-col gap-2">
                  <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Färgkanal (RGB Separation)</label>
                  <div className="flex gap-2 bg-slate-100 p-1.5 rounded-xl border border-slate-200">
                    <button type="button" onClick={() => setChannel('all')} className={`flex-1 py-1.5 text-xs font-bold rounded-lg transition-colors ${channel === 'all' ? 'bg-white shadow-sm text-slate-800' : 'text-slate-500 hover:bg-slate-200/50'}`}>⚪️ RGB</button>
                    <button type="button" onClick={() => setChannel('r')} className={`flex-1 py-1.5 text-xs font-bold rounded-lg transition-colors ${channel === 'r' ? 'bg-white shadow-sm text-red-600' : 'text-slate-500 hover:bg-slate-200/50'}`}>🔴 Röd</button>
                    <button type="button" onClick={() => setChannel('g')} className={`flex-1 py-1.5 text-xs font-bold rounded-lg transition-colors ${channel === 'g' ? 'bg-white shadow-sm text-emerald-600' : 'text-slate-500 hover:bg-slate-200/50'}`}>🟢 Grön</button>
                    <button type="button" onClick={() => setChannel('b')} className={`flex-1 py-1.5 text-xs font-bold rounded-lg transition-colors ${channel === 'b' ? 'bg-white shadow-sm text-blue-600' : 'text-slate-500 hover:bg-slate-200/50'}`}>🔵 Blå</button>
                  </div>
                </div>
                <div className="flex flex-col gap-2 mt-2">
                  <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Läs-väg (Förbättra precision)</label>
                  <div className="flex gap-2">
                    <button 
                      onClick={() => setIsDrawingMode(!isDrawingMode)}
                      className={`flex-1 py-2 px-4 rounded-xl font-bold text-xs transition-colors shadow-sm border ${isDrawingMode ? 'bg-[#b7410e] text-white border-[#b7410e]' : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'}`}
                    >
                      {isDrawingMode ? '🖌️ Ritläge Aktivt' : '✏️ Rita Läs-väg (Markeringspenna)'}
                    </button>
                    {isDrawingMode && (
                      <button 
                        onClick={() => {
                           if (drawCanvasRef.current) {
                             const ctx = drawCanvasRef.current.getContext('2d');
                             ctx?.clearRect(0, 0, drawCanvasRef.current.width, drawCanvasRef.current.height);
                           }
                        }}
                        className="px-4 py-2 bg-slate-100 text-slate-600 hover:bg-slate-200 rounded-xl font-bold text-xs transition-colors border border-slate-200"
                      >
                        Rensa
                      </button>
                    )}
                  </div>
                </div>
              </div>
            )}
            
            <button 
              onClick={handleAnalyze}
              disabled={loading || !imageBase64}
              className="w-full py-3.5 bg-slate-900 hover:bg-black active:scale-[0.98] disabled:opacity-40 text-white font-semibold text-sm rounded-2xl transition-all shadow-lg flex justify-center items-center gap-2"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Analyserar Bilden...
                </>
              ) : "Genomför Språkanalys"}
            </button>
          </div>
          
          <div className="lg:col-span-2 flex flex-col gap-8">
            {loading && (
              <div className="liquid-glass-island rounded-[36px] h-full flex flex-col items-center justify-center border border-emerald-900/10 p-8 text-center bg-white/40 backdrop-blur-md mb-8 py-24">
                <div className="w-16 h-16 border-4 border-slate-200 border-t-emerald-600 rounded-full animate-spin mb-6" />
                <h3 className="text-xl font-bold text-slate-800 mb-2 animate-pulse">Analyserar Fonetiskt...</h3>
                <p className="text-sm text-slate-500 max-w-sm">Vitki läser runorna (OCR), filtrerar bruset och rekonstruerar den troliga fornöstnordiska ljudbilden. Detta kan ta en liten stund.</p>
              </div>
            )}

            {imageBase64 && !loading && (
               <div className="liquid-glass-island rounded-[36px] p-4 shadow-sm border border-slate-900/10 relative">
                 <div className="relative flex justify-center w-full bg-slate-900/5 rounded-3xl p-4 overflow-hidden">
                   <ReactCrop
                     crop={crop}
                     onChange={(_, percentCrop) => setCrop(percentCrop)}
                     onComplete={(c) => setCompletedCrop(c)}
                     className="relative max-h-[600px]"
                     locked={isDrawingMode}
                   >
                     <img 
                       ref={imgRef}
                       src={imageBase64} 
                       alt="Runestone reference" 
                       className="w-auto h-auto max-h-[500px] object-contain" 
                       style={{ filter: `brightness(${brightness}%) contrast(${contrast}%) ${channel !== 'all' ? `url(#channel-${channel})` : ''}` }}
                     />
                     <canvas 
                       ref={drawCanvasRef}
                       className={`absolute top-0 left-0 w-full h-full ${isDrawingMode ? 'pointer-events-auto cursor-crosshair' : 'pointer-events-none'}`}
                       style={{ zIndex: 45 }}
                       onPointerDown={handlePointerDown}
                       onPointerMove={handlePointerMove}
                       onPointerUp={handlePointerUp}
                       onPointerOut={handlePointerUp}
                     />
                     {results?.markers?.map((marker, idx) => {
                        let ymin, xmin, ymax, xmax;
                        if (marker.polygon && marker.polygon.length > 0) {
                          ymin = Math.min(...marker.polygon.map(p => p[0])) / 1000;
                          xmin = Math.min(...marker.polygon.map(p => p[1])) / 1000;
                          ymax = Math.max(...marker.polygon.map(p => p[0])) / 1000;
                          xmax = Math.max(...marker.polygon.map(p => p[1])) / 1000;
                        } else if (marker.box_2d && marker.box_2d.length === 4) {
                          ymin = marker.box_2d[0] / 1000;
                          xmin = marker.box_2d[1] / 1000;
                          ymax = marker.box_2d[2] / 1000;
                          xmax = marker.box_2d[3] / 1000;
                        } else {
                          return null;
                        }
  
                        let left, top, width, height;
                        if (completedCrop && completedCrop.width > 0 && completedCrop.height > 0) {
                          const domW = imgSize.width;
                          const domH = imgSize.height;
                          
                          const cropLeftPct = completedCrop.x / domW;
                          const cropTopPct = completedCrop.y / domH;
                          const cropWidthPct = completedCrop.width / domW;
                          const cropHeightPct = completedCrop.height / domH;
  
                          left = (cropLeftPct + xmin * cropWidthPct) * 100;
                          top = (cropTopPct + ymin * cropHeightPct) * 100;
                          width = (xmax - xmin) * cropWidthPct * 100;
                          height = (ymax - ymin) * cropHeightPct * 100;
                        } else {
                          left = xmin * 100;
                          top = ymin * 100;
                          width = (xmax - xmin) * 100;
                          height = (ymax - ymin) * 100;
                        }

                       return (
                         <div
                           key={idx}
                           className={`absolute group hover:z-50 transition-all rounded ${!marker.polygon ? 'border-2 border-emerald-500 bg-emerald-500/20 hover:bg-emerald-500/40' : ''}`}
                           style={{
                             top: `${top}%`,
                             left: `${left}%`,
                             height: `${height}%`,
                             width: `${width}%`
                           }}
                         >
                           {marker.polygon && (
                             <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="absolute inset-0 w-full h-full overflow-visible pointer-events-none">
                               <polygon
                                 points={marker.polygon.map(p => {
                                   const px = p[1] / 1000;
                                   const py = p[0] / 1000;
                                   const xRel = ((px - xmin) / (xmax - xmin || 1)) * 100;
                                   const yRel = ((py - ymin) / (ymax - ymin || 1)) * 100;
                                   return `${xRel},${yRel}`;
                                 }).join(' ')}
                                 className="fill-emerald-500/20 stroke-emerald-500 stroke-[1] group-hover:fill-emerald-500/40 transition-all pointer-events-auto cursor-pointer"
                                 vectorEffect="non-scaling-stroke"
                               />
                             </svg>
                           )}
                           {/* Tooltip */}
                           <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 hidden group-hover:flex flex-col items-center z-50 w-64 pointer-events-none">
                             <div className="bg-slate-900 text-white text-xs rounded-xl p-3 shadow-xl border border-slate-700 w-full text-center">
                               <strong className="block text-emerald-400 mb-1">{marker.label}</strong>
                               <span className="text-slate-300 leading-relaxed">{marker.description}</span>
                             </div>
                             <div className="w-3 h-3 bg-slate-900 rotate-45 -mt-1.5 border-r border-b border-slate-700"></div>
                           </div>
                         </div>
                       )
                     })}
                   </ReactCrop>
                 </div>
               </div>
            )}
            
            {results && !loading && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                
                <div className="liquid-glass-island rounded-[32px] p-6 shadow-sm border border-slate-900/10 bg-white">
                  <div className="text-slate-500 text-[11px] uppercase tracking-wider font-bold mb-2">Translitterering</div>
                  <div className="text-lg font-serif italic text-slate-900">{results.transliteration}</div>
                </div>
                
                <div className="liquid-glass-island rounded-[32px] p-6 shadow-sm border border-slate-900/10 bg-white">
                  <div className="text-slate-500 text-[11px] uppercase tracking-wider font-bold mb-2">Fornöstnordisk Normalisering</div>
                  <div className="text-lg font-serif font-bold text-[#b7410e]">{results.normalization}</div>
                </div>

                {results.sound_laws_applied && results.sound_laws_applied.length > 0 && (
                  <div className="liquid-glass-island rounded-[32px] p-6 shadow-sm border border-slate-900/10 bg-white md:col-span-2">
                    <div className="text-slate-500 text-[11px] uppercase tracking-wider font-bold mb-2">Tillämpade Ljudlagar (Chain of Thought)</div>
                    <div className="flex flex-wrap gap-2 mt-3">
                      {results.sound_laws_applied.map((law, idx) => (
                        <div key={idx} className="bg-slate-100 text-slate-700 text-xs font-semibold px-3 py-1.5 rounded-lg border border-slate-200">
                          {law}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                <div className="bg-slate-50 p-5 rounded-2xl border border-slate-100 flex flex-col items-center justify-center relative md:col-span-2">
                  <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-2">Fonetisk Rekonstruktion (Så lät det)</h3>
                  <div className="text-2xl text-slate-800 font-mono bg-white px-6 py-3 rounded-xl border border-slate-200 shadow-sm text-center w-full">
                    [{results.phonetic_ipa}]
                  </div>
                  <button
                    onClick={handlePlayAudio}
                    disabled={isPlayingAudio}
                    className={`mt-4 px-6 py-2 rounded-xl font-bold flex items-center gap-2 transition-all ${isPlayingAudio ? 'bg-slate-200 text-slate-400' : 'bg-slate-800 text-white hover:bg-slate-700 shadow-lg'}`}
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {isPlayingAudio ? "Spelar upp..." : "Spela Upp"}
                  </button>
                </div>
                
                <div className="liquid-glass-island rounded-[32px] p-6 shadow-sm border border-slate-900/10 md:col-span-2 bg-slate-50">
                  <div className="text-slate-500 text-[11px] uppercase tracking-wider font-bold mb-2">Modern Svensk Översättning</div>
                  <div className="text-[15px] font-medium text-slate-800 leading-relaxed">{results.translation}</div>
                </div>
                
                <div className="liquid-glass-island rounded-[32px] p-8 shadow-sm border border-slate-900/10 md:col-span-2">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="bg-[#b7410e] text-white p-2 rounded-xl">
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25" />
                      </svg>
                    </div>
                    <h3 className="text-sm font-bold uppercase tracking-wider text-slate-500">Lingvistisk AI-Analys (Baserat på bild)</h3>
                  </div>
                  <p className="text-[15px] font-medium text-slate-700 leading-relaxed">
                    {results.linguistic_analysis}
                  </p>
                </div>

                {results.academic_reading && (
                  <div className="liquid-glass-island rounded-[32px] p-8 shadow-sm border border-emerald-900/10 md:col-span-2 bg-emerald-50/30">
                    <h3 className="text-sm font-bold uppercase tracking-wider text-emerald-700 mb-2">Vedertagen Forskning (Känd data för signum)</h3>
                    <p className="text-[15px] font-medium text-slate-800 leading-relaxed">
                      {results.academic_reading}
                    </p>
                  </div>
                )}

                {results.comparison && (
                  <div className="liquid-glass-island rounded-[32px] p-8 shadow-sm border border-amber-900/10 md:col-span-2 bg-amber-50/30">
                    <h3 className="text-sm font-bold uppercase tracking-wider text-amber-700 mb-2">Jämförelse (AI vs Forskning)</h3>
                    <p className="text-[15px] font-medium text-slate-800 leading-relaxed">
                      {results.comparison}
                    </p>
                  </div>
                )}

                {/* Signum and Save */}
                <div className="liquid-glass-island rounded-[36px] p-6 border border-white/50 mt-4 md:col-span-2 flex items-center justify-between gap-4">
                  <div className="flex-1">
                    <label className="block text-slate-500 text-[10px] font-bold uppercase tracking-wider mb-1">
                      Koppla till Signum (t.ex. Sö 112)
                    </label>
                    <input 
                      type="text" 
                      placeholder="Ange Signum..." 
                      value={latest3DMeta.text}
                      onChange={e => setLatest3DMeta({...latest3DMeta, text: e.target.value})}
                      className="w-full liquid-glass-input-wrapper rounded-xl px-4 py-2.5 text-slate-900 text-sm font-semibold outline-none placeholder:text-slate-400"
                    />
                  </div>
                  <button 
                    onClick={handleSaveProject}
                    className="px-6 py-4 bg-[#b7410e] hover:bg-[#9a350b] text-white font-bold rounded-2xl shadow-lg transition-transform active:scale-95 flex items-center gap-2 mt-4 flex-shrink-0"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M17.593 3.322c1.1.128 1.907 1.077 1.907 2.185V21L12 17.25 4.5 21V5.507c0-1.108.806-2.057 1.907-2.185a48.507 48.507 0 0111.186 0z" />
                    </svg>
                    Spara i Projekt
                  </button>
                </div>

              </div>
            )}
            
            {!results && !loading && !imageBase64 && (
              <div className="liquid-glass-island rounded-[36px] p-12 h-full flex flex-col items-center justify-center text-center text-slate-400 border border-slate-900/5 border-dashed">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-16 h-16 mb-4 opacity-50">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 001.5-1.5V6a1.5 1.5 0 00-1.5-1.5H3.75A1.5 1.5 0 002.25 6v12a1.5 1.5 0 001.5 1.5Zm10.5-11.25h.008v.008h-.008V8.25Zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0Z" />
                </svg>
                <h3 className="text-lg font-bold text-slate-500 mb-2">Ingen bild analyserad</h3>
                <p className="text-sm max-w-sm">Ladda upp ett foto av runstenens ristningsyta för att låta AI:n läsa och fonetiskt rekonstruera språket.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
