"use client";
import React, { useState, useMemo, Suspense } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, Environment } from "@react-three/drei";
import * as THREE from "three";
import { CameraCapturer, SnapshotTaker } from "./threeD/capture";
import { MeshModel } from "./threeD/MeshModel";

class ErrorBoundary extends React.Component<{children: React.ReactNode}, {hasError: boolean, error: Error | null}> {
  constructor(props: {children: React.ReactNode}) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-red-50 text-red-500 p-4 overflow-auto rounded-[24px]">
          <pre className="text-xs">{this.state.error?.toString()}</pre>
        </div>
      );
    }
    return this.props.children;
  }
}


export type Vec3 = [number, number, number];

export interface SliceMarker {
  from: Vec3;
  to: Vec3;
  color?: string;
}

export interface ViewDirection {
  toward: Vec3; // from the stone towards the camera
  up: Vec3;     // the screen's up direction
}

export interface ViewerPoint {
  position: Vec3;
  color: string;
}

export interface ThreeDViewerProps {
  file: File | null;
  // All coordinates are in the model's own (centred) coordinate system, as used by the backend.
  // `up` is the averaged surface normal at the clicked points.
  onVectorSelected: (origin: Vec3, direction: Vec3, up?: Vec3) => void;
  onPathSelected?: (points: Vec3[], up?: Vec3) => void;
  // "points": Shift-click points/paths; "single": every Shift-click is reported via onSingleClick;
  // "view": no measuring clicks (e.g. during automatic analysis)
  clickMode?: 'points' | 'single' | 'view';
  onSingleClick?: (point: Vec3, normal: Vec3) => void;
  onClearMarkers?: () => void;
  markers?: SliceMarker[];
  autoPoints?: ViewerPoint[];
  // Updated every frame with the camera's direction and screen-up, in model coordinates
  viewDirRef?: React.MutableRefObject<ViewDirection | null>;
  onAutoSnapRequest?: (points: [number, number, number][]) => Promise<[number, number, number][]>;
  cutoffDepth?: number;
  layerThickness?: number;
  slicerMode?: 'flat' | 'peeling';
  // The file is already centred by the backend (lighter view model of a large scan)
  preCentered?: boolean;
  // Shown instead of the upload hint when no file is displayed yet
  emptyMessage?: string;
}

export default function ThreeDViewer({ file, onVectorSelected, onPathSelected, onAutoSnapRequest, cutoffDepth = 0, layerThickness = 100, slicerMode = 'flat', preCentered = false, emptyMessage,
  clickMode = 'points', onSingleClick, onClearMarkers, markers, autoPoints, viewDirRef }: ThreeDViewerProps) {
  const [resetCounter, setResetCounter] = useState(0);
  const [clearCounter, setClearCounter] = useState(0);
  const [snapCounter, setSnapCounter] = useState(0);
  const [newLineCounter, setNewLineCounter] = useState(0);
  const [faceCounter, setFaceCounter] = useState(0);
  const [lightIntensity, setLightIntensity] = useState(1.5);
  const [ambientIntensity, setAmbientIntensity] = useState(0.5);
  const [showSettings, setShowSettings] = useState(false);
  // Raking light: a low, directional light makes shallow carvings readable
  const [lightAzimuth, setLightAzimuth] = useState(45);
  const [lightElevation, setLightElevation] = useState(45);
  const [lightUpAxis, setLightUpAxis] = useState<'z' | 'y'>('z');
  const [rakingMode, setRakingMode] = useState(false);
  // High-resolution picture of the current view (light, contrast and angle as on screen)
  const [snapCounterImg, setSnapCounterImg] = useState(0);
  const [exportScale, setExportScale] = useState(4);
  const [snapMessage, setSnapMessage] = useState<string | null>(null);
  const lightPosition = useMemo<[number, number, number]>(() => {
    const az = (lightAzimuth * Math.PI) / 180;
    const el = (lightElevation * Math.PI) / 180;
    const h = Math.cos(el) * 1000;
    const v = Math.sin(el) * 1000;
    return lightUpAxis === 'z'
      ? [h * Math.cos(az), h * Math.sin(az), v]
      : [h * Math.cos(az), v, h * Math.sin(az)];
  }, [lightAzimuth, lightElevation, lightUpAxis]);
  const [dragging, setDragging] = useState(false);
  
  const [meshRotation, setMeshRotation] = useState<[number, number, number]>([0,0,0]);

  const [loadingMesh, setLoadingMesh] = useState(false);
  
  const [topografyMode, setTopografyMode] = useState(false);
  const [topoCaptureTrigger] = useState(0);
  const [planeNormal, setPlaneNormal] = useState(new THREE.Vector3(0, 0, 1));
  const [topoOffset, setTopoOffset] = useState(0);
  const [topoSensitivity, setTopoSensitivity] = useState(1.0);
  const [topoOpacity, setTopoOpacity] = useState(0.5);
  
  const [isCompilingTopo] = useState(false);
  
  const toggleTopography = () => {
    setTopografyMode(prev => !prev);
  };

  return (
    <div className="w-full h-full rounded-[24px] overflow-hidden relative cursor-crosshair">
      {!file && (
        <div className="absolute inset-0 z-30 flex flex-col items-center justify-center bg-slate-50/80 text-slate-400 font-medium rounded-[24px]">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-12 h-12 mb-3 opacity-50">
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 7.5l-9-5.25L3 7.5m18 0l-9 5.25m9-5.25v9l-9 5.25M3 7.5l9 5.25M3 7.5v9l9 5.25m0-9v9" />
          </svg>
          {emptyMessage ?? "Ladda upp en 3D-fil för att se stenen"}
        </div>
      )}

      {loadingMesh && (
        <div className="absolute inset-0 z-20 flex items-center justify-center bg-white/70 backdrop-blur-sm rounded-[24px]">
          <div className="flex flex-col items-center text-slate-800 font-bold">
            <div className="w-10 h-10 border-4 border-slate-300 border-t-[#b7410e] rounded-full animate-spin mb-4" />
            Laddar in och behandlar 3D-modell (Kan ta några sekunder)...
          </div>
        </div>
      )}

      {file && (
        <>
          {/* Toolbar: one wrapping row, so the file name and buttons never overlap */}
          <div className="absolute top-3 left-3 right-3 z-10 flex flex-wrap items-start justify-between gap-2 pointer-events-none">
            <div className="max-w-[45%] min-w-0 bg-white/90 backdrop-blur-md px-3 py-2 rounded-xl text-xs font-semibold text-slate-800 shadow-md border border-white/50 flex items-center gap-2" title={file.name}>
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4 text-[#b7410e] flex-shrink-0">
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 7.5l-9-5.25L3 7.5m18 0l-9 5.25m9-5.25v9l-9 5.25M3 7.5l9 5.25M3 7.5v9l9 5.25m0-9v9" />
              </svg>
              <span className="truncate">{file.name}</span>
            </div>

            <div className="relative flex flex-wrap justify-end gap-2 pointer-events-auto ml-auto">
              {clickMode === 'points' ? (
                <>
                  <button type="button" onClick={() => setNewLineCounter(c => c + 1)} className="bg-white/90 backdrop-blur-md px-3 py-2 rounded-xl shadow-md border border-white/50 text-slate-700 hover:bg-white hover:text-[#b7410e] text-xs font-bold whitespace-nowrap transition-all" title="Avsluta nuvarande linje och börja en ny">Ny linje</button>
                  <button type="button" onClick={() => setClearCounter(c => c + 1)} className="bg-white/90 backdrop-blur-md px-3 py-2 rounded-xl shadow-md border border-white/50 text-slate-700 hover:bg-white hover:text-[#b7410e] text-xs font-bold whitespace-nowrap transition-all" title="Ta bort alla utplacerade punkter och linjer">Rensa</button>
                  {onAutoSnapRequest && (
                    <button type="button" onClick={() => setSnapCounter(c => c + 1)} className="bg-white/90 backdrop-blur-md px-3 py-2 rounded-xl shadow-md border border-white/50 text-slate-700 hover:bg-white hover:text-[#b7410e] text-xs font-bold whitespace-nowrap transition-all" title="Flytta banans punkter till spårets botten">Auto-snap</button>
                  )}
                </>
              ) : clickMode === 'single' && onClearMarkers ? (
                <button type="button" onClick={onClearMarkers} className="bg-white/90 backdrop-blur-md px-3 py-2 rounded-xl shadow-md border border-white/50 text-slate-700 hover:bg-white hover:text-[#b7410e] text-xs font-bold whitespace-nowrap transition-all" title="Ta bort alla snitt som lagts med ett klick">Rensa snitt</button>
              ) : null}

              <div className="flex bg-white/90 backdrop-blur-md rounded-xl shadow-md border border-white/50 overflow-hidden text-xs font-bold divide-x divide-slate-200">
                {(['X', 'Y', 'Z'] as const).map((axis, i) => (
                  <button key={axis} type="button"
                    onClick={() => setMeshRotation(prev => prev.map((v, k) => (k === i ? v + Math.PI / 2 : v)) as [number, number, number])}
                    className="px-2.5 py-2 text-slate-700 hover:bg-white hover:text-[#b7410e] transition-all"
                    title={`Rotera 90° runt ${axis}-axeln`}>
                    ↻{axis}
                  </button>
                ))}
              </div>

              <button type="button" onClick={() => setShowSettings(!showSettings)}
                className={`bg-white/90 backdrop-blur-md p-2 rounded-xl shadow-md border transition-all flex items-center justify-center ${showSettings ? "text-[#b7410e] border-[#b7410e]/30" : "text-slate-700 border-white/50 hover:bg-white"}`}
                title="Ljus och strykljus">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v2.25m6.364.386-1.591 1.591M21 12h-2.25m-.386 6.364-1.591-1.591M12 18.75V21m-4.773-4.227-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0Z" />
                </svg>
              </button>

              <button type="button" onClick={toggleTopography} disabled={isCompilingTopo}
                className={`bg-white/90 backdrop-blur-md p-2 rounded-xl shadow-md border transition-all flex items-center justify-center ${topografyMode ? "text-[#b7410e] border-[#b7410e]/30 bg-orange-50" : "text-slate-700 border-white/50 hover:bg-white"}`}
                title="Topografi (djupfärgning)">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 6.75V15m6-6v8.25m.503 3.498 4.875-2.437c.381-.19.622-.58.622-1.006V4.82c0-.836-.88-1.38-1.628-1.006l-3.869 1.934c-.317.159-.69.159-1.006 0L9.503 3.252a1.125 1.125 0 0 0-1.006 0L3.622 5.689C3.24 5.88 3 6.27 3 6.695V19.18c0 .836.88 1.38 1.628 1.006l3.869-1.934c.317-.159.69-.159 1.006 0l4.994 2.497c.317.158.69.158 1.006 0Z" />
                </svg>
              </button>

              <button type="button" onClick={() => { setSnapMessage("Renderar bilden …"); setSnapCounterImg(c => c + 1); }}
                className="bg-white/90 backdrop-blur-md p-2 rounded-xl shadow-md border transition-all flex items-center justify-center text-slate-700 border-white/50 hover:text-[#b7410e] hover:bg-white"
                title="Ladda ner vyn som bild i hög upplösning">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3" />
                </svg>
              </button>

              <button type="button" onClick={() => { setResetCounter(c => c + 1); setMeshRotation([0, 0, 0]); }}
                className="bg-white/90 backdrop-blur-md p-2 rounded-xl shadow-md border transition-all flex items-center justify-center text-slate-700 border-white/50 hover:text-[#b7410e] hover:bg-white"
                title="Återställ vy">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
                </svg>
              </button>

          {showSettings && (
            <div className="absolute right-0 top-full mt-2 bg-white/95 backdrop-blur-md p-4 rounded-xl shadow-lg border border-white/50 w-60 max-h-[70vh] overflow-y-auto pointer-events-auto animate-in fade-in slide-in-from-top-2">
              <div className="mb-4">
                  <label className="flex justify-between text-[10px] font-bold text-slate-500 uppercase mb-2">
                    <span>Direktljus (Ljusstyrka)</span>
                    <span>{lightIntensity.toFixed(1)}</span>
                  </label>
                  <input 
                    type="range" min="0" max="5" step="0.1" 
                    value={lightIntensity} onChange={e => setLightIntensity(+e.target.value)} 
                    className="w-full accent-slate-900 cursor-pointer" 
                  />
                </div>
                <div className="mb-4 border-b border-slate-200 pb-4">
                  <label className="flex items-center justify-between text-[10px] font-bold text-slate-700 uppercase mb-3">
                    <span>Strykljus</span>
                    <input type="checkbox" checked={rakingMode} onChange={e => {
                      setRakingMode(e.target.checked);
                      if (e.target.checked && lightElevation > 20) setLightElevation(10);
                    }} />
                  </label>
                  <label className="flex justify-between text-[10px] font-bold text-slate-500 uppercase mb-1">
                    <span>Ljusriktning</span><span>{lightAzimuth}°</span>
                  </label>
                  <input type="range" min="0" max="359" step="1" value={lightAzimuth}
                    onChange={e => setLightAzimuth(+e.target.value)} className="w-full accent-slate-900 cursor-pointer mb-2" />
                  <label className="flex justify-between text-[10px] font-bold text-slate-500 uppercase mb-1">
                    <span>Ljushöjd</span><span>{lightElevation}°</span>
                  </label>
                  <input type="range" min="1" max="90" step="1" value={lightElevation}
                    onChange={e => setLightElevation(+e.target.value)} className="w-full accent-slate-900 cursor-pointer mb-2" />
                  <div className="flex gap-1 text-[10px] font-bold">
                    <span className="text-slate-500 uppercase mr-1 self-center">Uppåt:</span>
                    {(['z', 'y'] as const).map(ax => (
                      <button key={ax} type="button" onClick={() => setLightUpAxis(ax)}
                        className={`px-2 py-0.5 rounded ${lightUpAxis === ax ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-600'}`}>
                        {ax.toUpperCase()}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="mb-4 border-b border-slate-200 pb-4">
                  <div className="text-[10px] font-bold text-slate-500 uppercase mb-2">Bildens upplösning</div>
                  <div className="flex gap-1 text-[10px] font-bold">
                    {[2, 4, 8].map(k => (
                      <button key={k} type="button" onClick={() => setExportScale(k)}
                        className={`px-2 py-0.5 rounded ${exportScale === k ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-600'}`}>
                        {k}×
                      </button>
                    ))}
                  </div>
                  <p className="mt-1 text-[10px] text-slate-500 leading-snug">Gånger skärmens upplösning, högst 8192 bildpunkter på längden.</p>
                </div>
                <div>
                  <label className="flex justify-between text-[10px] font-bold text-slate-500 uppercase mb-2">
                    <span>Omgivningsljus (Kontrast)</span>
                    <span>{ambientIntensity.toFixed(1)}</span>
                  </label>
                  <input 
                    type="range" min="0" max="3" step="0.1" 
                    value={ambientIntensity} onChange={e => setAmbientIntensity(+e.target.value)} 
                    className="w-full accent-slate-900 cursor-pointer" 
                  />
                </div>
                
                {topografyMode && (
                  <>
                    <div className="mt-4 mb-4 border-t border-slate-200 pt-4">
                      <label className="flex justify-between text-[10px] font-bold text-[#b7410e] uppercase mb-2">
                        <span>Topo Nivå (Offset)</span>
                        <span>{topoOffset.toFixed(2)}</span>
                      </label>
                      <input 
                        type="range" min="-1" max="1" step="0.01" 
                        value={topoOffset} onChange={e => setTopoOffset(+e.target.value)} 
                        className="w-full accent-[#b7410e] cursor-pointer" 
                      />
                    </div>
                    <div>
                      <label className="flex justify-between text-[10px] font-bold text-[#b7410e] uppercase mb-2">
                        <span>Topo Känslighet</span>
                        <span>{topoSensitivity.toFixed(1)}</span>
                      </label>
                      <input 
                        type="range" min="1" max="100" step="1" 
                        value={topoSensitivity} onChange={e => setTopoSensitivity(+e.target.value)} 
                        className="w-full accent-[#b7410e] cursor-pointer" 
                      />
                    </div>
                    <div className="mt-4">
                      <label className="flex justify-between text-[10px] font-bold text-[#b7410e] uppercase mb-2">
                        <span>Topo Opacitet</span>
                        <span>{topoOpacity.toFixed(2)}</span>
                      </label>
                      <input 
                        type="range" min="0.1" max="1.0" step="0.05" 
                        value={topoOpacity} onChange={e => setTopoOpacity(+e.target.value)} 
                        className="w-full accent-[#b7410e] cursor-pointer" 
                      />
                    </div>
                  </>
                )}
              </div>
            )}
            </div>
          </div>

          {snapMessage && (
            <div className="absolute bottom-14 right-3 z-10 max-w-sm bg-white/95 backdrop-blur-md px-3 py-2 rounded-xl text-[11px] font-semibold text-slate-700 border border-white/50 shadow-md">
              {snapMessage}
            </div>
          )}
          <div className="absolute bottom-3 left-3 right-3 z-10 flex justify-end items-end gap-2 pointer-events-none">
            {clickMode === 'view' && file && (
              <button type="button" onClick={() => setFaceCounter(c => c + 1)}
                title="Vrider vyn så att du ser rakt på stenens bredaste sida (stenens tunnaste riktning). Tryck igen för andra sidan."
                className="pointer-events-auto bg-slate-900 hover:bg-black text-white px-3 py-2 rounded-xl text-[11px] font-bold shadow-md">
                Vänd ristade sidan mot mig
              </button>
            )}
            <div className="bg-white/85 backdrop-blur-md px-3 py-2 rounded-xl text-[11px] font-semibold text-slate-600 border border-white/50 leading-relaxed text-right">
              Dra: rotera · Högerdra: panorera · Scroll: zooma ·{" "}
              {clickMode === 'single'
                ? <strong className="text-slate-800">Shift + klick mitt i ett spår: mät ett snitt</strong>
                : clickMode === 'view'
                ? <strong className="text-slate-800">Vrid den ristade sidan mot dig innan analysen</strong>
                : <strong className="text-slate-800">Shift + klick: lägg till mätpunkt (Alt + Shift: ny linje)</strong>}
            </div>
          </div>
        </>
      )}

      <ErrorBoundary>
        <Canvas camera={{ fov: 45, near: 0.1, far: 10000000 }} gl={{ preserveDrawingBuffer: true }}>
          <ambientLight intensity={rakingMode ? Math.min(ambientIntensity, 0.08) : ambientIntensity} />
          <directionalLight position={lightPosition} intensity={rakingMode ? Math.max(lightIntensity, 2.5) : lightIntensity} />
          {/* Keep loading inside the 3D scene: react-three-fiber otherwise lifts suspense to the page,
              which remounts the whole viewer and loses the WebGL context */}
          <Suspense fallback={null}>
          {!rakingMode && <Environment preset="city" />}
          
          <SnapshotTaker trigger={snapCounterImg} scale={exportScale} name={file?.name ?? 'vy'}
            onDone={msg => { setSnapMessage(msg); window.setTimeout(() => setSnapMessage(null), 8000); }} />

          <CameraCapturer 
            trigger={topoCaptureTrigger} 
            onCapture={(dir) => setPlaneNormal(dir)} 
          />

          {file && (
            <MeshModel 
              file={file} 
              onVectorSelected={onVectorSelected} 
              onPathSelected={onPathSelected}
              onAutoSnapRequest={onAutoSnapRequest}
              resetCounter={resetCounter} 
              clearCounter={clearCounter}
              snapCounter={snapCounter}
              newLineCounter={newLineCounter}
              setDragging={setDragging} 
              setLoading={setLoadingMesh} 
              topografyMode={topografyMode}
              planeNormal={planeNormal}
              topoOffset={topoOffset}
              topoSensitivity={topoSensitivity}
              topoOpacity={topoOpacity}
              cutoffDepth={cutoffDepth}
              layerThickness={layerThickness}
              meshRotation={meshRotation}
              slicerMode={slicerMode}
              preCentered={preCentered}
              clickMode={clickMode}
              onSingleClick={onSingleClick}
              markers={markers}
              autoPoints={autoPoints}
              viewDirRef={viewDirRef}
              faceCounter={faceCounter}
            />
          )}
          </Suspense>
          <OrbitControls makeDefault enabled={!dragging} />
        </Canvas>
      </ErrorBoundary>
    </div>
  );
}
