"use client";
import React, { useState, useEffect, useEffectEvent, useMemo, useRef } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Environment, Bounds, TransformControls, useBounds } from '@react-three/drei';
import * as THREE from 'three';
import { STLLoader, OBJLoader, PLYLoader, mergeBufferGeometries } from 'three-stdlib';

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


const peelingVertexShader = `
  attribute float relativeDepth;
  varying float vDepth;
  varying float vRelativeDepth;
  void main() {
    vec4 worldPosition = modelMatrix * vec4(position, 1.0);
    vDepth = worldPosition.y;
    vRelativeDepth = relativeDepth;
    
    vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
    gl_Position = projectionMatrix * mvPosition;
  }
`;

const peelingFragmentShader = `
  varying float vDepth;
  varying float vRelativeDepth;
  uniform float uMinDepth;
  uniform float uMaxDepth;
  uniform float uMinRelativeDepth;
  uniform float uMaxRelativeDepth;
  
  uniform float uCutoffDepth;
  uniform float uLayerThickness;
  uniform float uOpacity;
  uniform int uSlicerMode;

  vec3 depthToColor(float depth, float cutoff, float minD, float maxD) {
    float t = clamp((cutoff - depth) / ((maxD - minD) * 0.1), 0.0, 1.0);
    return mix(vec3(0.9, 0.9, 0.9), vec3(0.1, 0.1, 0.2), t);
  }

  void main() {
    float activeDepth = vDepth;
    float minD = uMinDepth;
    float maxD = uMaxDepth;
    
    if (uSlicerMode == 1) {
      activeDepth = vRelativeDepth;
      minD = uMinRelativeDepth;
      maxD = uMaxRelativeDepth;
    }
  
    // 0 = högst upp (MaxDepth), 100 = längst ner (MinDepth)
    float sliceDepth = mix(maxD, minD, uCutoffDepth / 100.0);
    float thickness = (maxD - minD) * (uLayerThickness / 100.0);

    // 1. Kapa av toppen (Allt som är högre upp i världen än sliceDepth slängs)
    if (activeDepth > sliceDepth) {
      discard;
    }
    
    // 2. Kapa av botten (Skikttjocklek)
    if (activeDepth < (sliceDepth - thickness)) {
      discard;
    }

    vec3 color = depthToColor(activeDepth, sliceDepth, minD, maxD);
    
    gl_FragColor = vec4(color, uOpacity);
  }
`;


interface ThreeDViewerProps {
  file: File | null;
  onVectorSelected: (origin: [number, number, number], direction: [number, number, number]) => void;
  onPathSelected?: (points: [number, number, number][]) => void;
  onAutoSnapRequest?: (points: [number, number, number][]) => Promise<[number, number, number][]>;
  cutoffDepth?: number;
  layerThickness?: number;
  slicerMode?: 'flat' | 'peeling';
  // The file is already centred by the backend (lighter view model of a large scan)
  preCentered?: boolean;
}

function SplineLine({ points, color = "red" }: { points: THREE.Vector3[], color?: string }) {
  const geometry = useMemo(() => {
    if (points.length < 2) return new THREE.BufferGeometry();
    
    // If only 2 points, draw straight line. Otherwise, draw a smooth curve.
    let curvePoints = points;
    if (points.length > 2) {
      const curve = new THREE.CatmullRomCurve3(points);
      curvePoints = curve.getPoints(points.length * 10);
    }
    
    return new THREE.BufferGeometry().setFromPoints(curvePoints);
  }, [points]);

  if (points.length < 2) return null;

  return (
    // @ts-expect-error - line geometry is not fully typed in three-fiber
    <line geometry={geometry}>
      <lineBasicMaterial color={color} linewidth={5} depthTest={false} transparent={true} />
    </line>
  );
}

interface DraggablePointProps {
  position: THREE.Vector3;
  color: string;
  size: number;
  onDragStart?: () => void;
  onDragEnd: (pos: THREE.Vector3) => void;
  setDragging: (dragging: boolean) => void;
}

function DraggablePoint({ position, color, size, onDragStart, onDragEnd, setDragging }: DraggablePointProps) {
  const meshRef = useRef<THREE.Mesh>(null);
  
  return (
    <TransformControls 
      position={position} 
      mode="translate" 
      size={0.5}
      showY={true}
      showX={true}
      showZ={true}
      onMouseDown={() => {
        setDragging(true);
        if (onDragStart) onDragStart();
      }}
      onMouseUp={() => {
        setDragging(false);
        if (meshRef.current) {
          const worldPos = new THREE.Vector3();
          meshRef.current.getWorldPosition(worldPos);
          onDragEnd(worldPos);
        }
      }}
    >
      <mesh ref={meshRef}>
        <sphereGeometry args={[size, 16, 16]} />
        <meshBasicMaterial color={color} depthTest={false} transparent={true} />
      </mesh>
    </TransformControls>
  );
}

function setUniforms(material: THREE.ShaderMaterial, values: Record<string, unknown>) {
  for (const [name, value] of Object.entries(values)) {
    material.uniforms[name].value = value;
  }
}

function StoneMesh({ geometry, onClick, resetCounter, topografyMode, planeNormal, offset, sensitivity,
  topoOpacity,
  cutoffDepth,
  layerThickness,
  slicerMode,
  relativeDepthRange,
  meshRotation
}: { 
  geometry: THREE.BufferGeometry, 
  onClick: (e: import('@react-three/fiber').ThreeEvent<MouseEvent>) => void, 
  resetCounter: number,
  topografyMode: boolean,
  planeNormal: THREE.Vector3,
  offset: number,
  sensitivity: number,
  topoOpacity: number,
  cutoffDepth: number,
  layerThickness: number,
  slicerMode: 'flat' | 'peeling',
  relativeDepthRange: { min: number, max: number },
  meshRotation: [number, number, number]
}) {
  const bounds = useBounds();
  useEffect(() => {
    if (geometry) {
      setTimeout(() => {
        bounds.refresh().fit();
      }, 50);
    }
  }, [geometry, resetCounter, bounds]);

  const depthRange = useMemo(() => {
    if (geometry) {
      geometry.computeBoundingBox();
      const box = geometry.boundingBox;
      if (box) {
        const corners = [
          new THREE.Vector3(box.min.x, box.min.y, box.min.z),
          new THREE.Vector3(box.min.x, box.min.y, box.max.z),
          new THREE.Vector3(box.min.x, box.max.y, box.min.z),
          new THREE.Vector3(box.min.x, box.max.y, box.max.z),
          new THREE.Vector3(box.max.x, box.min.y, box.min.z),
          new THREE.Vector3(box.max.x, box.min.y, box.max.z),
          new THREE.Vector3(box.max.x, box.max.y, box.min.z),
          new THREE.Vector3(box.max.x, box.max.y, box.max.z),
        ];
        
        let min = Infinity;
        let max = -Infinity;
        const euler = new THREE.Euler(meshRotation[0], meshRotation[1], meshRotation[2]);
        
        for (const corner of corners) {
          const worldCorner = corner.clone().applyEuler(euler);
          const d = worldCorner.y;
          if (d < min) min = d;
          if (d > max) max = d;
        }
        
        return { min, max };
      }
    }
    return { min: -10, max: 10 };
  }, [geometry, meshRotation]);

  // Create the shader once to prevent freezes; uniforms are synced in an effect below.
  const [customMaterial] = useState(() => {
    return new THREE.ShaderMaterial({
      vertexShader: peelingVertexShader,
      fragmentShader: peelingFragmentShader,
      transparent: true,
      depthWrite: false,
      polygonOffset: true,
      polygonOffsetFactor: -1,
      polygonOffsetUnits: -1,
      uniforms: {
        uPlaneNormal: { value: planeNormal },
        uOffset: { value: offset },
        uSensitivity: { value: sensitivity },
        uOpacity: { value: topoOpacity },
        uMinDepth: { value: depthRange.min },
        uMaxDepth: { value: depthRange.max },
        uMinRelativeDepth: { value: relativeDepthRange.min },
        uMaxRelativeDepth: { value: relativeDepthRange.max },
        uCutoffDepth: { value: cutoffDepth },
        uLayerThickness: { value: layerThickness },
        uSlicerMode: { value: slicerMode === 'peeling' ? 1 : 0 }
      }
    });
  });

  useEffect(() => () => customMaterial.dispose(), [customMaterial]);

  useEffect(() => {
    setUniforms(customMaterial, {
      uPlaneNormal: planeNormal,
      uOffset: offset,
      uSensitivity: sensitivity,
      uOpacity: topoOpacity,
      uMinDepth: depthRange.min,
      uMaxDepth: depthRange.max,
      uMinRelativeDepth: relativeDepthRange.min,
      uMaxRelativeDepth: relativeDepthRange.max,
      uCutoffDepth: cutoffDepth,
      uLayerThickness: layerThickness,
      uSlicerMode: slicerMode === 'peeling' ? 1 : 0,
    });
  }, [customMaterial, planeNormal, offset, sensitivity, topoOpacity, depthRange, cutoffDepth, layerThickness, slicerMode, relativeDepthRange]);

  const isSlicing = cutoffDepth > 0;

  return (
    <group>
      <mesh geometry={geometry} onClick={onClick} visible={!topografyMode && !isSlicing}>
        <meshStandardMaterial color="#a0a5aa" roughness={0.7} metalness={0.0} />
      </mesh>
      
      <mesh geometry={geometry} onClick={onClick} visible={topografyMode || isSlicing}>
        <primitive object={customMaterial} attach="material" />
      </mesh>
    </group>
  );
}

function MeshModel({ 
  file, onVectorSelected, onPathSelected, onAutoSnapRequest, resetCounter, setDragging, setLoading, clearCounter, snapCounter, newLineCounter,
  topografyMode, planeNormal, topoOffset, topoSensitivity, topoOpacity, cutoffDepth, layerThickness,
  meshRotation, slicerMode = 'flat', preCentered = false
}: ThreeDViewerProps & { 
  resetCounter: number, setDragging: (d: boolean) => void, setLoading: (l: boolean) => void, clearCounter: number, snapCounter: number, newLineCounter: number,
  topografyMode: boolean, planeNormal: THREE.Vector3, topoOffset: number, topoSensitivity: number, topoOpacity: number, cutoffDepth: number, layerThickness: number,
  meshRotation: [number, number, number], slicerMode?: 'flat' | 'peeling'
}) {
  const [url, setUrl] = useState<string | null>(null);
  const [lines, setLines] = useState<THREE.Vector3[][]>([]);
  const [activeLineIndex, setActiveLineIndex] = useState<number>(-1);
  const [geometry, setGeometry] = useState<THREE.BufferGeometry | null>(null);
  const [relativeDepthRange, setRelativeDepthRange] = useState({ min: -1, max: 0 });

  const [prevClearCounter, setPrevClearCounter] = useState(clearCounter);
  if (clearCounter !== prevClearCounter) {
    setPrevClearCounter(clearCounter);
    setLines([]);
    setActiveLineIndex(-1);
  }

  const [prevNewLineCounter, setPrevNewLineCounter] = useState(newLineCounter);
  if (newLineCounter !== prevNewLineCounter) {
    setPrevNewLineCounter(newLineCounter);
    setActiveLineIndex(-1);
  }

  const snapActiveLine = useEffectEvent(() => {
    if (activeLineIndex >= 0 && activeLineIndex < lines.length) {
      const doSnap = async () => {
        const activeLine = lines[activeLineIndex];
        if (activeLine.length > 0 && onAutoSnapRequest) {
          try {
            const pts = activeLine.map(p => [p.x, p.y, p.z] as [number, number, number]);
            const snappedPts = await onAutoSnapRequest(pts);
            setLines(prev => {
              const newLines = [...prev];
              newLines[activeLineIndex] = snappedPts.map(p => new THREE.Vector3(p[0], p[1], p[2]));
              return newLines;
            });
          } catch (e) {
            console.error("Auto-snap failed", e);
          }
        }
      };
      doSnap();
    }
  });

  useEffect(() => {
    if (snapCounter > 0) snapActiveLine();
  }, [snapCounter]);

  useEffect(() => {
    if (file) {
      const objectUrl = URL.createObjectURL(file);
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setUrl(objectUrl);
      setLines([]); 
      setActiveLineIndex(-1);
      return () => URL.revokeObjectURL(objectUrl);
    }
  }, [file]);

  const extension = file?.name.toLowerCase().split('.').pop();

  useEffect(() => {
    if (!url) return;
    setLoading(true);

    const finish = (geo: THREE.BufferGeometry | null) => {
      if (geo) {
        geo.computeVertexNormals();
        // Centre like the backend does, so clicked coordinates match the analysis
        if (!preCentered) geo.center();
        setGeometry(geo);
      }
      setLoading(false);
    };
    const fail = (err: unknown) => {
      console.error(err);
      setLoading(false);
    };

    if (extension === 'stl') {
      new STLLoader().load(url, geo => finish(geo as THREE.BufferGeometry), undefined, fail);
    } else if (extension === 'ply') {
      new PLYLoader().load(url, geo => finish(geo as THREE.BufferGeometry), undefined, fail);
    } else if (extension === 'obj') {
      new OBJLoader().load(url, (obj) => {
        // Merge all meshes, as the backend analyses the whole file
        const parts: THREE.BufferGeometry[] = [];
        obj.traverse((child) => {
          if (child instanceof THREE.Mesh) {
            const g = (child.geometry as THREE.BufferGeometry).clone();
            g.applyMatrix4(child.matrixWorld);
            for (const name of Object.keys(g.attributes)) {
              if (name !== 'position') g.deleteAttribute(name);
            }
            parts.push(g.index ? g.toNonIndexed() : g);
          }
        });
        finish(parts.length > 1 ? mergeBufferGeometries(parts) : parts[0] ?? null);
      }, undefined, fail);
    } else {
      setLoading(false);
      alert("Filformatet stöds inte! Ladda upp en .stl-, .obj- eller .ply-fil.");
    }
  }, [url, extension, preCentered, setLoading]);

  const boundingSphereRadius = useMemo(() => {
    if (!geometry) return 1;
    geometry.computeBoundingSphere();
    return geometry.boundingSphere?.radius || 1;
  }, [geometry]);

  useEffect(() => {
    if (geometry && !geometry.attributes.relativeDepth) {
      setLoading(true);
      const worker = new Worker(new URL('../lib/peelingWorker.ts', import.meta.url));
      
      const positionArray = geometry.attributes.position.array;
      const indexArray = geometry.index ? geometry.index.array : null;

      worker.postMessage({
        positionArray,
        indexArray,
        iterations: 5,
        smoothFactor: 0.5
      });

      worker.onmessage = (e) => {
        if (e.data.type === 'progress') {
          console.log(e.data.message);
        } else if (e.data.type === 'done') {
          geometry.setAttribute('relativeDepth', new THREE.BufferAttribute(e.data.relativeDepths, 1));
          setRelativeDepthRange({ min: e.data.minRelative, max: e.data.maxRelative });
          setLoading(false);
          worker.terminate();
        }
      };

      worker.onerror = (err) => {
        console.error("Worker error:", err);
        setLoading(false);
        worker.terminate();
      };

      return () => worker.terminate();
    }
  }, [geometry, setLoading]);
  
  const pointSize = boundingSphereRadius * 0.02;

  const notifySelection = useEffectEvent(() => {
    if (activeLineIndex >= 0 && activeLineIndex < lines.length) {
      const activeLine = lines[activeLineIndex];
      if (activeLine.length === 2) {
        const p1 = activeLine[0];
        const p2 = activeLine[1];
        const origin = new THREE.Vector3().addVectors(p1, p2).multiplyScalar(0.5);
        const direction = new THREE.Vector3().subVectors(p2, p1).normalize();
        
        onVectorSelected(
          [origin.x, origin.y, origin.z],
          [direction.x, direction.y, direction.z]
        );
      } else if (activeLine.length > 2 && onPathSelected) {
        const pointsArray = activeLine.map(p => [p.x, p.y, p.z] as [number, number, number]);
        onPathSelected(pointsArray);
      }
    }
  });

  useEffect(() => {
    notifySelection();
  }, [lines, activeLineIndex]);

  const handleClick = async (e: import('@react-three/fiber').ThreeEvent<MouseEvent>) => {
    if (!e.shiftKey) return;
    
    e.stopPropagation();
    const p = e.point;    if (e.altKey) {
      setLines(prev => {
        const newLines = [...prev, [p.clone()]];
        setActiveLineIndex(newLines.length - 1);
        return newLines;
      });
    } else {
      setLines(prev => {
        if (activeLineIndex >= 0 && activeLineIndex < prev.length) {
          const newLines = [...prev];
          const activeLine = [...newLines[activeLineIndex]];
          activeLine.push(p.clone());
          newLines[activeLineIndex] = activeLine;
          return newLines;
        } else {
          const newLines = [[p.clone()]];
          setActiveLineIndex(0);
          return newLines;
        }
      });
    }
  };

  if (!geometry) return null;

  return (
    <group rotation={meshRotation}>
      {geometry && (
        <Bounds fit margin={1.2}>
          <StoneMesh 
            geometry={geometry} 
            onClick={handleClick} 
            resetCounter={resetCounter} 
            topografyMode={topografyMode}
            planeNormal={planeNormal}
            offset={topoOffset}
            sensitivity={topoSensitivity}
            topoOpacity={topoOpacity}
            cutoffDepth={cutoffDepth}
            layerThickness={layerThickness}
            slicerMode={slicerMode}
            relativeDepthRange={relativeDepthRange}
            meshRotation={meshRotation}
          />
        </Bounds>
      )}
      
      {lines.map((line, lineIdx) => {
        const isActive = lineIdx === activeLineIndex;
        const color = isActive ? "#b7410e" : "#64748b";
        
        return (
          <group key={lineIdx}>
            <SplineLine points={line} color={color} />
            {line.map((p, pIdx) => (
              <DraggablePoint
                key={`${lineIdx}-${pIdx}`}
                position={p}
                size={pointSize}
                color={color}
                setDragging={setDragging}
                onDragStart={() => setActiveLineIndex(lineIdx)}
                onDragEnd={(newPos: THREE.Vector3) => {
                  setLines(prev => {
                    const newLines = [...prev];
                    const modifiedLine = [...newLines[lineIdx]];
                    modifiedLine[pIdx] = newPos.clone();
                    newLines[lineIdx] = modifiedLine;
                    return newLines;
                  });
                }}
              />
            ))}
          </group>
        );
      })}
    </group>
  );
}

export default function ThreeDViewer({ file, onVectorSelected, onPathSelected, onAutoSnapRequest, cutoffDepth = 0, layerThickness = 100, slicerMode = 'flat', preCentered = false }: ThreeDViewerProps) {
  const [resetCounter, setResetCounter] = useState(0);
  const [clearCounter, setClearCounter] = useState(0);
  const [snapCounter, setSnapCounter] = useState(0);
  const [newLineCounter, setNewLineCounter] = useState(0);
  const [lightIntensity, setLightIntensity] = useState(1.5);
  const [ambientIntensity, setAmbientIntensity] = useState(0.5);
  const [showSettings, setShowSettings] = useState(false);
  // Raking light: a low, directional light makes shallow carvings readable
  const [lightAzimuth, setLightAzimuth] = useState(45);
  const [lightElevation, setLightElevation] = useState(45);
  const [lightUpAxis, setLightUpAxis] = useState<'z' | 'y'>('z');
  const [rakingMode, setRakingMode] = useState(false);
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
          Ladda upp en 3D-fil för att se stenen
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
          <div className="absolute top-4 left-4 z-10 bg-white/90 backdrop-blur-md px-4 py-2.5 rounded-2xl text-xs font-semibold text-slate-800 shadow-md border border-white/50 pointer-events-none flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4 text-[#b7410e]">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 0 0 6 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0 1 18 16.5h-2.25m-7.5 0h7.5m-7.5 0-1 3m8.5-3 1 3m0 0 .5 1.5m-.5-1.5h-9.5m0 0-.5 1.5m.75-9 3-3 2.148 2.148A12.061 12.061 0 0 1 16.5 7.605" />
            </svg>
            {file.name}
          </div>

          <div className="absolute top-4 right-4 z-10 flex gap-2">
            <button 
              onClick={() => setNewLineCounter(c => c + 1)}
              className="bg-white/90 backdrop-blur-md px-3 py-2.5 rounded-xl transition-all flex items-center justify-center shadow-md border text-slate-700 border-white/50 hover:bg-white text-xs font-bold"
              title="Avsluta nuvarande linje och börja på en ny runa"
            >
              Ny Linje
            </button>

            <button 
              onClick={() => setClearCounter(c => c + 1)}
              className="bg-white/90 backdrop-blur-md px-3 py-2.5 rounded-xl transition-all flex items-center justify-center shadow-md border text-slate-700 border-white/50 hover:bg-white text-xs font-bold"
              title="Ta bort alla utplacerade linjer"
            >
              Rensa Allt
            </button>
            
            {onAutoSnapRequest && (
              <button 
                onClick={() => setSnapCounter(c => c + 1)}
                className="bg-white/90 backdrop-blur-md px-3 py-2.5 rounded-xl transition-all flex items-center justify-center shadow-md border text-slate-700 border-white/50 hover:text-[#b7410e] hover:bg-white text-xs font-bold"
                title="Fäst banan mot djupaste botten"
              >
                Auto-Snap
              </button>
            )}

            <div className="flex bg-white/90 backdrop-blur-md rounded-xl shadow-md border border-white/50 overflow-hidden text-xs font-bold divide-x divide-slate-200">
              <button 
                onClick={() => setMeshRotation(prev => [prev[0] + Math.PI/2, prev[1], prev[2]])}
                className="px-3 py-2.5 text-slate-700 hover:bg-white hover:text-[#b7410e] transition-all"
                title="Rotera 90° runt X-axeln"
              >
                Vänd X
              </button>
              <button 
                onClick={() => setMeshRotation(prev => [prev[0], prev[1] + Math.PI/2, prev[2]])}
                className="px-3 py-2.5 text-slate-700 hover:bg-white hover:text-[#b7410e] transition-all"
                title="Rotera 90° runt Y-axeln"
              >
                Vänd Y
              </button>
              <button 
                onClick={() => setMeshRotation(prev => [prev[0], prev[1], prev[2] + Math.PI/2])}
                className="px-3 py-2.5 text-slate-700 hover:bg-white hover:text-[#b7410e] transition-all"
                title="Rotera 90° runt Z-axeln"
              >
                Vänd Z
              </button>
            </div>

            <button 
              onClick={() => setShowSettings(!showSettings)}
              className={`bg-white/90 backdrop-blur-md p-2.5 rounded-xl transition-all flex items-center justify-center shadow-md border ${showSettings ? "text-[#b7410e] border-[#b7410e]/30" : "text-slate-700 border-white/50 hover:bg-white"}`}
              title="Ljussättning (Kontrast/Ljusstyrka)"
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v2.25m6.364.386-1.591 1.591M21 12h-2.25m-.386 6.364-1.591-1.591M12 18.75V21m-4.773-4.227-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0Z" />
              </svg>
            </button>

            <button 
              onClick={toggleTopography}
              disabled={isCompilingTopo}
              className={`bg-white/90 backdrop-blur-md p-2.5 rounded-xl transition-all flex items-center justify-center shadow-md border ${topografyMode ? "text-[#b7410e] border-[#b7410e]/30 bg-orange-50" : "text-slate-700 border-white/50 hover:bg-white"} ${isCompilingTopo ? "opacity-70 cursor-wait" : ""}`}
              title="Topografi (Djupkarta)"
            >
              {isCompilingTopo ? (
                <div className="w-5 h-5 border-2 border-slate-300 border-t-[#b7410e] rounded-full animate-spin" />
              ) : (
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 6.75V15m6-6v8.25m.503 3.498 4.875-2.437c.381-.19.622-.58.622-1.006V4.82c0-.836-.88-1.38-1.628-1.006l-3.869 1.934c-.317.159-.69.159-1.006 0L9.503 3.252a1.125 1.125 0 0 0-1.006 0L3.622 5.689C3.24 5.88 3 6.27 3 6.695V19.18c0 .836.88 1.38 1.628 1.006l3.869-1.934c.317-.159.69-.159 1.006 0l4.994 2.497c.317.158.69.158 1.006 0Z" />
                </svg>
              )}
            </button>

            <button 
              onClick={() => {
                setResetCounter(c => c + 1);
                setMeshRotation([0,0,0]);
              }}
              className="bg-white/90 backdrop-blur-md p-2.5 rounded-xl text-slate-700 hover:text-[#b7410e] hover:bg-white shadow-md border border-white/50 transition-all flex items-center justify-center"
              title="Återställ Vy"
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
              </svg>
            </button>
          </div>

          {showSettings && (
            <div className="absolute top-20 right-4 z-10 bg-white/90 backdrop-blur-md p-4 rounded-xl shadow-lg border border-white/50 w-56 animate-in fade-in slide-in-from-top-2">
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

          <div className="absolute bottom-4 right-4 z-10 bg-white/80 backdrop-blur-md px-3 py-2 rounded-xl text-[10px] font-bold text-slate-500 uppercase tracking-wide border border-white/50 pointer-events-none">
            🖱️ Vänsterklick: Rotera &nbsp;&bull;&nbsp; 🖱️ Högerklick: Panorera &nbsp;&bull;&nbsp; 📜 Scroll: Zooma &nbsp;&bull;&nbsp; ⌨️ Shift + Klick: Lägg till mätpunkt
          </div>
        </>
      )}

      <ErrorBoundary>
        <Canvas camera={{ fov: 45, near: 0.1, far: 10000000 }} gl={{ preserveDrawingBuffer: true }}>
          <ambientLight intensity={rakingMode ? Math.min(ambientIntensity, 0.08) : ambientIntensity} />
          <directionalLight position={lightPosition} intensity={rakingMode ? Math.max(lightIntensity, 2.5) : lightIntensity} />
          {!rakingMode && <Environment preset="city" />}
          
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
            />
          )}
          <OrbitControls makeDefault enabled={!dragging} />
        </Canvas>
      </ErrorBoundary>
    </div>
  );
}

import { useThree } from '@react-three/fiber';

function CameraCapturer({ trigger, onCapture }: { trigger: number, onCapture: (dir: THREE.Vector3) => void }) {
  const { camera } = useThree();
  useEffect(() => {
    if (trigger > 0) {
      const dir = new THREE.Vector3();
      camera.getWorldDirection(dir);
      onCapture(dir);
    }
  }, [trigger, camera, onCapture]);
  return null;
}

