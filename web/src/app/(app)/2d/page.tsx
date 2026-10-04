/* eslint-disable @next/next/no-img-element */
"use client";

import { useState, useRef, useEffect } from "react";
import ReactCrop, { type Crop } from 'react-image-crop';
import 'react-image-crop/dist/ReactCrop.css';
import { useSettings } from "@/components/SettingsContext";
import { useAnalysis } from "@/components/AnalysisContext";
import Link from "next/link";
import RuneCanvasBackground from "@/components/RuneCanvasBackground";
import { db, PaleographicCrop, ProjectData } from "@/lib/db";
import type { KSamsokResult } from "@/lib/ksamsok";
import { API_URL } from "@/lib/api";

export default function TwoDPage() {
  const [loading, setLoading] = useState(false);
  const [savedCrops, setSavedCrops] = useState<PaleographicCrop[]>([]);
  const [crop, setCrop] = useState<Crop>();
  const [completedCrop, setCompletedCrop] = useState<Crop | null>(null);
  const [analyzedCrop, setAnalyzedCrop] = useState<Crop | null>(null);
  const [brightness, setBrightness] = useState(100);
  const [contrast, setContrast] = useState(100);
  const [channel, setChannel] = useState<'all' | 'r' | 'g' | 'b'>('all');
  const [cropTag, setCropTag] = useState("R-runa");
  
  // K-Samsök State
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<KSamsokResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  
  // Matching State
  const [comparingTo, setComparingTo] = useState<PaleographicCrop | null>(null);

  const imgRef = useRef<HTMLImageElement>(null);
  const { 
    latest2DResults: result, 
    setLatest2DResults: setResult, 
    latest2DImage: imagePreview, 
    setLatest2DImage: setImagePreview,
    latest2DFile: file,
    setLatest2DFile: setFile,
    latest3DMeta,
    setLatest3DMeta,
    activeProjectId,
    setActiveProjectId
  } = useAnalysis();

  const { geminiKey, addUsedTokens } = useSettings();

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
  }, [imagePreview]);

  useEffect(() => {
    const fetchCrops = async () => {
      if (activeProjectId) {
        const allProjs = await db.getProjects();
        const proj = allProjs.find(p => p.id === activeProjectId);
        if (proj && proj.paleographicCrops) {
          setSavedCrops(proj.paleographicCrops);
        }
      }
    };
    fetchCrops();
  }, [activeProjectId]);

  const handleSaveProject = async () => {
    if (!result) return;
    
    let projectIdToSaveTo = activeProjectId;
    
    // Auto-grouping by signum
    if (!projectIdToSaveTo && latest3DMeta.text) {
      const existingProj = await db.getProjectBySignum(latest3DMeta.text);
      if (existingProj) {
        projectIdToSaveTo = existingProj.id;
      }
    }

    let projectUpdate: Partial<ProjectData> = {
      twoDResults: result,
      twoDImage: imagePreview || undefined,
    };
    
    if (!projectIdToSaveTo) {
      // New project
      projectUpdate = {
        ...projectUpdate,
        name: latest3DMeta.text || (file ? file.name : "Nytt Projekt (2D)"),
        fileName: file ? file.name : "Bild",
        metaStone: latest3DMeta.stone || "Okänd",
        metaWeathering: latest3DMeta.weathering || "Låg",
        metaText: latest3DMeta.text || "",
        slices: [],
      };
    } else {
      projectUpdate.id = projectIdToSaveTo;
      if (latest3DMeta.text) {
         projectUpdate.metaText = latest3DMeta.text;
         projectUpdate.name = latest3DMeta.text; // Update name as well if they typed it
      }
    }
    
    const saved = await db.saveProject(projectUpdate);
    setActiveProjectId(saved.id);
    alert(`2D-data sparat till projekt: ${saved.name}`);
  };

  const handleSaveCrop = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!completedCrop || completedCrop.width === 0 || completedCrop.height === 0) {
      alert("Du måste markera en runa på bilden först.");
      return;
    }

    const processedBlob = await getProcessedImageBlob();
    if (!processedBlob) {
      alert("Kunde inte processa bildutsnittet.");
      return;
    }

    const reader = new FileReader();
    reader.readAsDataURL(processedBlob);
    reader.onloadend = async () => {
      const base64data = reader.result as string;
      const domW = imgRef.current?.width || 1;
      const domH = imgRef.current?.height || 1;
      
      let featureVector: number[] | undefined = undefined;
      try {
        const response = await fetch(`${API_URL}/api/2d/extract_features`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ image_base64: base64data }),
        });
        
        if (response.ok) {
          const data = await response.json();
          featureVector = data.feature_vector;
          console.log("Got feature vector of length", featureVector?.length);
        } else {
          console.error("Failed to extract features:", await response.text());
        }
      } catch (e) {
        console.error("Error calling extract_features:", e);
      }
      
      const newCrop: PaleographicCrop = {
        id: crypto.randomUUID(),
        tag: cropTag,
        imageBase64: base64data,
        coordinates: [
          completedCrop.x / domW, 
          completedCrop.y / domH, 
          (completedCrop.x + completedCrop.width) / domW, 
          (completedCrop.y + completedCrop.height) / domH
        ],
        featureVector,
        createdAt: new Date().toISOString()
      };

      let projectIdToSaveTo = activeProjectId;
      if (!projectIdToSaveTo && latest3DMeta.text) {
        const existingProj = await db.getProjectBySignum(latest3DMeta.text);
        if (existingProj) {
          projectIdToSaveTo = existingProj.id;
        }
      }

      let projectUpdate: Partial<ProjectData> = {
        paleographicCrops: [newCrop]
      };

      if (!projectIdToSaveTo) {
        projectUpdate = {
          name: latest3DMeta.text || (file ? file.name : "Nytt Projekt (Paleografi)"),
          fileName: file ? file.name : "Bild",
          metaStone: latest3DMeta.stone || "Okänd",
          slices: [],
          paleographicCrops: [newCrop]
        };
      } else {
        projectUpdate.id = projectIdToSaveTo;
        // get existing crops
        const allProjs = await db.getProjects();
        const existing = allProjs.find(p => p.id === projectIdToSaveTo);
        if (existing && existing.paleographicCrops) {
          projectUpdate.paleographicCrops = [...existing.paleographicCrops, newCrop];
        }
      }
      
      const saved = await db.saveProject(projectUpdate);
      setActiveProjectId(saved.id);
      
      // Update local state directly to show it
      if (saved.paleographicCrops) {
        setSavedCrops(saved.paleographicCrops);
      }
      
      alert(`Utsnitt sparat! Du har nu ${saved.paleographicCrops?.length || 1} st sparade runor i detta projekt.`);
      setCropTag("");
    };
  };

  const handleSearchKSamsok = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery) return;
    
    setIsSearching(true);
    try {
      const res = await fetch(`/api/ksamsok?q=${encodeURIComponent(searchQuery)}`);
      const data = await res.json();
      if (data.results) {
        setSearchResults(data.results);
      }
    } catch (e) {
      console.error(e);
      alert("Fel vid sökning på K-Samsök");
    } finally {
      setIsSearching(false);
    }
  };

  const loadKSamsokImage = async (url: string) => {
    setLoading(true);
    try {
      const proxyUrl = `/api/proxy-image?url=${encodeURIComponent(url)}`;
      const res = await fetch(proxyUrl);
      if (!res.ok) throw new Error("Kunde inte hämta bilden");
      
      const blob = await res.blob();
      const objectUrl = URL.createObjectURL(blob);
      setImagePreview(objectUrl);
      setFile(new File([blob], "ksamsok_image.jpg", { type: blob.type }));
      
      // Use the search query as signum if we don't have one
      if (!latest3DMeta.text) {
        setLatest3DMeta({ ...latest3DMeta, text: searchQuery.toUpperCase() });
      }
      
      setSearchResults([]); // Hide results after picking
    } catch (e) {
      console.error(e);
      alert("Fel vid inläsning av bild från K-Samsök. Bilden kanske inte tillåter extern åtkomst.");
    } finally {
      setLoading(false);
    }
  };

  const cosineSimilarity = (A: number[], B: number[]) => {
    let dotproduct = 0;
    let mA = 0;
    let mB = 0;
    for(let i = 0; i < A.length; i++){
        dotproduct += (A[i] * B[i]);
        mA += (A[i]*A[i]);
        mB += (B[i]*B[i]);
    }
    mA = Math.sqrt(mA);
    mB = Math.sqrt(mB);
    if (mA === 0 || mB === 0) return 0;
    return (dotproduct)/((mA)*(mB));
  };

  // Sort crops based on similarity to comparingTo
  const displayCrops = [...savedCrops].sort((a, b) => {
    if (!comparingTo || !comparingTo.featureVector) return 0;
    const simA = a.featureVector ? cosineSimilarity(comparingTo.featureVector, a.featureVector) : 0;
    const simB = b.featureVector ? cosineSimilarity(comparingTo.featureVector, b.featureVector) : 0;
    return simB - simA; // Highest similarity first
  });

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      const url = URL.createObjectURL(selectedFile);
      setImagePreview(url);
      setResult(null);
      setCrop(undefined);
      setCompletedCrop(null);
      setBrightness(100);
      setContrast(100);
      setChannel('all');
    }
  };

  const getProcessedImageBlob = async (): Promise<Blob | null> => {
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

    return new Promise((resolve) => {
      canvas.toBlob((blob) => {
        resolve(blob);
      }, file?.type || "image/jpeg", 0.95);
    });
  };

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    
    setLoading(true);
    setResult(null);

    const processedBlob = await getProcessedImageBlob();
    if (!processedBlob) {
      alert("Kunde inte processa bilden.");
      setLoading(false);
      return;
    }

    setAnalyzedCrop(completedCrop);
    const formData = new FormData();
    formData.append("file", processedBlob, file.name);

    try {
      const res = await fetch(`${API_URL}/api/2d/analyze`, {
        method: "POST",
        headers: {
          "X-Gemini-Api-Key": geminiKey
        },
        body: formData,
      });

      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`Analys misslyckades: ${res.status} - ${errorText}`);
      }

      const data = await res.json();
      setResult(data);
      if (data.tokens_used) {
        addUsedTokens(data.tokens_used);
      }
    } catch (err: unknown) {
      console.error(err);
      alert(`Något gick fel vid 2D-analysen: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setLoading(false);
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
      <RuneCanvasBackground />
      <div className="flex flex-col h-full w-full max-w-7xl mx-auto p-4 md:p-6 relative z-10 overflow-y-auto">
        <div className="mb-8">
          <Link href="/start" className="inline-flex items-center text-slate-500 hover:text-slate-900 font-semibold mb-4 transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4 mr-1">
              <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
            </svg>
            Tillbaka
          </Link>
          <h2 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">2D-Bildanalys (Grafometri / Paleografi)</h2>
          <p className="text-slate-600 text-[16px] leading-relaxed max-w-3xl font-medium mb-6">
            Ladda upp ett 2D-foto av en runsten. Vitki AI (Gemini Vision) kommer att identifiera ornamentikens form, försöka extrahera runor och uppskatta stenen till en av Gräslunds stilgrupper.
          </p>
          
          {/* K-Samsök Sökfält */}
          <div className="w-full max-w-2xl bg-white p-4 rounded-[24px] shadow-sm border border-slate-200">
            <form onSubmit={handleSearchKSamsok} className="flex gap-2">
              <input 
                type="text" 
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Sök K-Samsök (t.ex. 'U 11' eller 'Runsten Uppland')" 
                className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-sm font-semibold text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#b7410e]/50"
              />
              <button 
                type="submit" 
                disabled={isSearching}
                className="px-6 py-3 bg-[#b7410e] hover:bg-[#96350b] text-white font-bold text-sm rounded-xl transition-all shadow-sm disabled:opacity-50"
              >
                {isSearching ? 'Söker...' : 'Sök Bild'}
              </button>
            </form>
            
            {searchResults.length > 0 && (
              <div className="mt-4 border-t border-slate-100 pt-4">
                <p className="text-xs font-bold text-slate-500 mb-2 uppercase tracking-wider">Sökresultat ({searchResults.length})</p>
                <div className="flex gap-3 overflow-x-auto pb-2 custom-scrollbar">
                  {searchResults.map((res, i) => (
                    <div key={i} onClick={() => loadKSamsokImage(res.url)} className="flex-shrink-0 w-24 h-24 rounded-xl overflow-hidden cursor-pointer border-2 border-transparent hover:border-[#b7410e] transition-all relative group bg-slate-100">
                      <img src={res.thumbnail} alt="Thumbnail" className="w-full h-full object-cover" />
                      <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center p-2">
                        <span className="text-[9px] text-white font-bold text-center leading-tight line-clamp-3">{res.description}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>


        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 h-full">
          {/* Vänster: Uppladdning & Bild */}
          <div className="liquid-glass-island rounded-[36px] p-8 flex flex-col items-center justify-center border border-white/50 relative">
            {!imagePreview ? (
              <label className="flex flex-col items-center justify-center w-full h-[400px] border-2 border-dashed border-slate-300 rounded-3xl cursor-pointer hover:bg-slate-50/50 transition-colors relative group">
                <div className="flex flex-col items-center justify-center pt-5 pb-6 text-slate-500 group-hover:text-[#b7410e] transition-colors">
                  <svg className="w-12 h-12 mb-4" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 20 16">
                      <path stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 13h3a3 3 0 0 0 0-6h-.025A5.56 5.56 0 0 0 16 6.5 5.5 5.5 0 0 0 5.207 5.021C5.137 5.017 5.071 5 5 5a4 4 0 0 0 0 8h2.167M10 15V6m0 0L8 8m2-2 2 2"/>
                  </svg>
                  <p className="mb-2 text-sm font-semibold">Klicka eller dra för att ladda upp</p>
                  <p className="text-xs">PNG, JPG eller WEBP (Max 5MB)</p>
                </div>
                <input type="file" className="hidden" accept="image/*" onChange={handleImageChange} />
              </label>
            ) : (
              <div className="w-full flex flex-col items-center">
                <div className="relative w-full rounded-3xl overflow-hidden bg-slate-900/5 flex items-center justify-center p-4">
                  <ReactCrop
                    crop={crop}
                    onChange={(_, percentCrop) => setCrop(percentCrop)}
                    onComplete={(c) => setCompletedCrop(c)}
                    className="max-h-[500px] relative"
                  >
                    <img 
                      ref={imgRef}
                      src={imagePreview} 
                      alt="Uppladdad runsten" 
                      style={{ filter: `brightness(${brightness}%) contrast(${contrast}%) ${channel !== 'all' ? `url(#channel-${channel})` : ''}` }}
                      className="w-auto h-auto max-h-[460px] object-contain shadow-sm" 
                    />
                    {result?.markers && result.markers.map((m, i) => {
                      let ymin, xmin, ymax, xmax;
                      if (m.polygon && m.polygon.length > 0) {
                        ymin = Math.min(...m.polygon.map(p => p[0])) / 1000;
                        xmin = Math.min(...m.polygon.map(p => p[1])) / 1000;
                        ymax = Math.max(...m.polygon.map(p => p[0])) / 1000;
                        xmax = Math.max(...m.polygon.map(p => p[1])) / 1000;
                      } else if (m.box_2d && m.box_2d.length === 4) {
                        ymin = m.box_2d[0] / 1000;
                        xmin = m.box_2d[1] / 1000;
                        ymax = m.box_2d[2] / 1000;
                        xmax = m.box_2d[3] / 1000;
                      } else {
                        return null;
                      }

                      let left, top, width, height;
                      if (analyzedCrop && analyzedCrop.width > 0 && analyzedCrop.height > 0) {
                        const domW = imgSize.width;
                        const domH = imgSize.height;
                        
                        // Convert analyzedCrop from px to pct if needed, or if it's already pct, use it.
                        // Assuming analyzedCrop is in pixels (default ReactCrop behavior).
                        const cropLeftPct = analyzedCrop.x / domW;
                        const cropTopPct = analyzedCrop.y / domH;
                        const cropWidthPct = analyzedCrop.width / domW;
                        const cropHeightPct = analyzedCrop.height / domH;

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

                      const handleHotspotClick = (e: React.MouseEvent) => {
                        e.stopPropagation();
                        const newCrop = {
                          unit: '%' as const,
                          x: left,
                          y: top,
                          width: width,
                          height: height
                        };
                        setCrop(newCrop);
                        setCompletedCrop(newCrop);
                        if (m.label) {
                          setCropTag(m.label.replace("Runtyp - ", ""));
                        }
                      };

                      return (
                        <div
                          key={i}
                          onClick={handleHotspotClick}
                          className={`absolute group cursor-pointer transition-all z-40 rounded ${!m.polygon ? 'border-2 border-[#b7410e] bg-[#b7410e]/10 hover:bg-[#b7410e]/40' : ''}`}
                          style={{
                            left: `${left}%`,
                            top: `${top}%`,
                            width: `${width}%`,
                            height: `${height}%`
                          }}
                        >
                          {m.polygon && (
                            <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="absolute inset-0 w-full h-full overflow-visible pointer-events-none">
                              <polygon
                                points={m.polygon.map(p => {
                                  const px = p[1] / 1000;
                                  const py = p[0] / 1000;
                                  const xRel = ((px - xmin) / (xmax - xmin || 1)) * 100;
                                  const yRel = ((py - ymin) / (ymax - ymin || 1)) * 100;
                                  return `${xRel},${yRel}`;
                                }).join(' ')}
                                className="fill-[#b7410e]/10 stroke-[#b7410e] stroke-[1] group-hover:fill-[#b7410e]/40 transition-all pointer-events-auto"
                                vectorEffect="non-scaling-stroke"
                              />
                            </svg>
                          )}
                          <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 w-56 bg-slate-900 text-white text-xs p-3 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 shadow-xl border border-white/10">
                            <span className="font-bold block mb-1 text-[#b7410e]">{m.label}</span>
                            {m.description}
                          </div>
                        </div>
                      );
                    })}
                  </ReactCrop>
                  <label className="absolute top-4 right-4 bg-slate-900/80 hover:bg-black text-white text-xs font-bold px-3 py-1.5 rounded-full cursor-pointer transition-colors z-10 shadow-lg backdrop-blur-md">
                    Byt bild
                    <input type="file" className="hidden" accept="image/*" onChange={handleImageChange} />
                  </label>
                </div>
                
                {/* Image Controls */}
                <div className="flex flex-col gap-4 mt-6 w-full px-2">
                  <div className="flex gap-6 w-full">
                    <div className="flex-1 flex flex-col gap-2">
                      <div className="flex justify-between items-center">
                        <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Ljusstyrka</label>
                        <span className="text-[10px] font-bold text-slate-700 bg-slate-100 px-2 py-0.5 rounded-full">{brightness}%</span>
                      </div>
                      <input type="range" min="50" max="200" value={brightness} onChange={e => setBrightness(Number(e.target.value))} className="w-full accent-[#b7410e]" />
                    </div>
                    <div className="flex-1 flex flex-col gap-2">
                      <div className="flex justify-between items-center">
                        <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Kontrast</label>
                        <span className="text-[10px] font-bold text-slate-700 bg-slate-100 px-2 py-0.5 rounded-full">{contrast}%</span>
                      </div>
                      <input type="range" min="50" max="250" value={contrast} onChange={e => setContrast(Number(e.target.value))} className="w-full accent-[#b7410e]" />
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
                </div>
              </div>
            )}
            
            <form onSubmit={handleAnalyze} className="w-full mt-6">
              <button 
                type="submit" 
                disabled={loading || !file}
                className="w-full py-3.5 bg-slate-900 hover:bg-black active:scale-[0.98] disabled:opacity-40 text-white font-semibold text-sm rounded-2xl transition-all shadow-lg flex justify-center items-center gap-2"
              >
                {loading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Analyserar...
                  </>
                ) : (
                  <>
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
                    </svg>
                    Kör AI-Bildanalys
                  </>
                )}
              </button>
            </form>

            <form onSubmit={handleSaveCrop} className="w-full mt-4 flex gap-2">
              <input 
                type="text" 
                value={cropTag} 
                onChange={(e) => setCropTag(e.target.value)} 
                placeholder="Tagga runa (t.ex. R-runa)"
                className="flex-1 bg-white/50 border border-slate-200 rounded-xl px-4 py-3 text-sm font-semibold text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#b7410e]/50"
              />
              <button 
                type="submit" 
                className="px-6 py-3 bg-white border border-slate-200 hover:border-[#b7410e]/30 hover:bg-[#b7410e]/5 text-[#b7410e] font-bold text-sm rounded-xl transition-all shadow-sm"
              >
                Spara Grafometriskt Utsnitt
              </button>
            </form>
          </div>

          {/* Höger: Resultat */}
          <div className="flex flex-col gap-6">
            
            {/* Sparade Utsnitt (Grafometri) */}
            {savedCrops.length > 0 && (
              <div className="liquid-glass-island rounded-[36px] p-6 border border-[#b7410e]/20 bg-gradient-to-br from-white/80 to-white/40 shadow-sm animate-in fade-in duration-500">
                <h3 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5 text-[#b7410e]">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 0 1 6 3.75h2.25A2.25 2.25 0 0 1 10.5 6v2.25a2.25 2.25 0 0 1-2.25 2.25H6a2.25 2.25 0 0 1-2.25-2.25V6ZM3.75 15.75A2.25 2.25 0 0 1 6 13.5h2.25a2.25 2.25 0 0 1 2.25 2.25V18a2.25 2.25 0 0 1-2.25 2.25H6A2.25 2.25 0 0 1 3.75 18v-2.25ZM13.5 6a2.25 2.25 0 0 1 2.25-2.25H18A2.25 2.25 0 0 1 20.25 6v2.25A2.25 2.25 0 0 1 18 10.5h-2.25a2.25 2.25 0 0 1-2.25-2.25V6ZM13.5 15.75a2.25 2.25 0 0 1 2.25-2.25H18a2.25 2.25 0 0 1 2.25 2.25V18A2.25 2.25 0 0 1 18 20.25h-2.25A2.25 2.25 0 0 1 13.5 18v-2.25Z" />
                  </svg>
                  Grafometriska Profiler ({savedCrops.length})
                  {comparingTo && (
                    <button 
                      onClick={() => setComparingTo(null)}
                      className="ml-auto text-xs bg-slate-200 hover:bg-slate-300 text-slate-700 px-3 py-1 rounded-full transition-colors"
                    >
                      Avbryt Jämförelse
                    </button>
                  )}
                </h3>
                <div className="grid grid-cols-3 sm:grid-cols-4 gap-3">
                  {displayCrops.map(crop => {
                    const isComparing = comparingTo?.id === crop.id;
                    const hasVector = !!crop.featureVector;
                    let simStr = "";
                    if (comparingTo && comparingTo.featureVector && crop.featureVector && !isComparing) {
                       const sim = cosineSimilarity(comparingTo.featureVector, crop.featureVector);
                       simStr = `${(sim * 100).toFixed(1)}% match`;
                    }
                    
                    return (
                      <div key={crop.id} className={`flex flex-col items-center bg-white border-2 rounded-2xl overflow-hidden shadow-sm hover:shadow-md transition-all group relative ${isComparing ? 'border-[#b7410e] shadow-[#b7410e]/20 ring-2 ring-[#b7410e]/50' : 'border-slate-200 hover:border-[#b7410e]/30'}`}>
                        <div className="w-full h-24 bg-slate-50 flex items-center justify-center p-2 relative">
                          <img src={crop.imageBase64} alt={crop.tag} className="max-w-full max-h-full object-contain" />
                          
                          {/* Similarity Badge */}
                          {simStr && (
                            <div className="absolute top-1 right-1 bg-[#b7410e] text-white text-[9px] font-bold px-1.5 py-0.5 rounded-md shadow-sm z-10">
                              {simStr}
                            </div>
                          )}
                          
                          {/* Hover Overlay for Comparing */}
                          {!isComparing && hasVector && (
                            <div className="absolute inset-0 bg-white/80 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                              <button 
                                onClick={() => setComparingTo(crop)}
                                className="bg-slate-900 text-white text-[10px] font-bold px-2 py-1.5 rounded-lg shadow-sm hover:scale-105 transition-transform"
                              >
                                Jämför
                              </button>
                            </div>
                          )}
                        </div>
                        <div className={`w-full px-2 py-1.5 text-center ${isComparing ? 'bg-[#b7410e]' : 'bg-slate-900'}`}>
                          <span className="text-[10px] font-bold text-white block truncate">{crop.tag}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {loading ? (
              <div className="liquid-glass-island rounded-[36px] h-full flex flex-col items-center justify-center border border-white/50 p-8 text-center bg-white/40 backdrop-blur-md">
                <div className="w-16 h-16 border-4 border-slate-200 border-t-[#b7410e] rounded-full animate-spin mb-6" />
                <h3 className="text-xl font-bold text-slate-800 mb-2 animate-pulse">Analyserar Bilden...</h3>
                <p className="text-sm text-slate-500 max-w-sm">Vitki AI extraherar paleografiska drag och bygger visuella bevis. Detta kan ta upp till 30 sekunder beroende på komplexitet.</p>
              </div>
            ) : result ? (
              <div className="space-y-6 animate-in slide-in-from-right-4 duration-500 h-full">
                {/* Style Group Header */}
                <div className="liquid-glass-island rounded-[36px] p-8 border border-[#b7410e]/20 bg-gradient-to-br from-white/50 to-[#b7410e]/5 shadow-sm">
                  <div className="text-slate-500 text-[12px] uppercase tracking-wider font-bold mb-2">Identifierad Stilgrupp (Gräslund)</div>
                  <div className="flex items-end gap-4">
                    <h3 className="text-5xl font-black text-[#b7410e] drop-shadow-sm">{result.predicted_style}</h3>
                    <div className="mb-2 bg-slate-900 text-white text-xs font-bold px-3 py-1 rounded-full">
                      {result.confidence}% Sannolikhet
                    </div>
                  </div>
                </div>
                
                {/* Reasoning */}
                <div className="liquid-glass-island rounded-[36px] p-8 border border-white/50 flex-1">
                  <div className="text-slate-500 text-[12px] uppercase tracking-wider font-bold mb-4 flex items-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25" />
                    </svg>
                    Epigrafisk Motivering
                  </div>
                  <p className="text-slate-700 text-sm font-medium leading-relaxed">
                    {result.reasoning}
                  </p>
                </div>
                
                {/* Rune Types */}
                {result.rune_types && (
                  <div className="liquid-glass-island rounded-[36px] p-8 border border-white/50">
                    <div className="text-slate-500 text-[12px] uppercase tracking-wider font-bold mb-2 flex items-center gap-2">
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
                      </svg>
                      Runtyper & Paleografi
                    </div>
                    <p className="text-slate-700 text-sm font-medium leading-relaxed">
                      {result.rune_types}
                    </p>
                  </div>
                )}
                {/* Signum and Save */}
                <div className="liquid-glass-island rounded-[36px] p-6 border border-white/50 mt-4 flex items-center justify-between gap-4">
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
            ) : (
              <div className="liquid-glass-island rounded-[36px] h-full flex flex-col items-center justify-center border border-white/50 p-8 text-center text-slate-400">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-16 h-16 mb-4 opacity-50">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09l2.846.813-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
                </svg>
                <p className="font-semibold text-lg text-slate-500 mb-2">Väntar på bild...</p>
                <p className="text-sm max-w-sm">Ladda upp ett foto av en runsten och klicka på Kör AI-Bildanalys för att låta Vitki extrahera stilgrupp och text.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
