import { useState, useEffect, useEffectEvent, useMemo, useRef } from "react";
import { Bounds } from "@react-three/drei";
import * as THREE from "three";
import { STLLoader, OBJLoader, PLYLoader, mergeBufferGeometries } from "three-stdlib";
import type { ThreeDViewerProps, Vec3 } from "../ThreeDViewer";
import { FaceCarvedSide, StoneMesh, ViewDirTracker, averageNormal } from "./stone";
import { DraggablePoint, MarkerLine, PointCloud, SplineLine } from "./markers";

export function MeshModel({ 
  file, onVectorSelected, onPathSelected, onAutoSnapRequest, resetCounter, setDragging, setLoading, clearCounter, snapCounter, newLineCounter,
  topografyMode, planeNormal, topoOffset, topoSensitivity, topoOpacity, cutoffDepth, layerThickness,
  meshRotation, slicerMode = 'flat', preCentered = false,
  clickMode = 'points', onSingleClick, markers, autoPoints, viewDirRef, faceCounter = 0
}: ThreeDViewerProps & { 
  faceCounter?: number,
  resetCounter: number, setDragging: (d: boolean) => void, setLoading: (l: boolean) => void, clearCounter: number, snapCounter: number, newLineCounter: number,
  topografyMode: boolean, planeNormal: THREE.Vector3, topoOffset: number, topoSensitivity: number, topoOpacity: number, cutoffDepth: number, layerThickness: number,
  meshRotation: [number, number, number], slicerMode?: 'flat' | 'peeling'
}) {
  const [url, setUrl] = useState<string | null>(null);
  const [lines, setLines] = useState<THREE.Vector3[][]>([]);
  // Surface normal at each clicked point (parallel to `lines`), used as the slice's up vector
  const [normals, setNormals] = useState<THREE.Vector3[][]>([]);
  const groupRef = useRef<THREE.Group>(null);
  const [activeLineIndex, setActiveLineIndex] = useState<number>(-1);
  const [geometry, setGeometry] = useState<THREE.BufferGeometry | null>(null);
  // A replaced scan (e.g. the lighter view model or another project) keeps its GPU buffers until disposed
  useEffect(() => () => geometry?.dispose(), [geometry]);
  const [relativeDepthRange, setRelativeDepthRange] = useState({ min: -1, max: 0 });

  const [prevClearCounter, setPrevClearCounter] = useState(clearCounter);
  if (clearCounter !== prevClearCounter) {
    setPrevClearCounter(clearCounter);
    setLines([]);
    setNormals([]);
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
      setNormals([]);
      setActiveLineIndex(-1);
      return () => URL.revokeObjectURL(objectUrl);
    }
  }, [file]);

  const extension = file?.name.toLowerCase().split('.').pop();

  useEffect(() => {
    if (!url) return;
    setLoading(true);
    // A newer file may replace this one mid-load (e.g. a lighter view model); ignore stale results
    let cancelled = false;

    const finish = (geo: THREE.BufferGeometry | null) => {
      if (cancelled) return;
      if (geo) {
        geo.computeVertexNormals();
        // Centre like the backend does, so clicked coordinates match the analysis
        if (!preCentered) geo.center();
        setGeometry(geo);
      }
      setLoading(false);
    };
    const fail = (err: unknown) => {
      if (cancelled) return;
      console.error("Kunde inte läsa 3D-filen", err);
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
    return () => { cancelled = true; };
  }, [url, extension, preCentered, setLoading]);

  const boundingSphereRadius = useMemo(() => {
    if (!geometry) return 1;
    geometry.computeBoundingSphere();
    return geometry.boundingSphere?.radius || 1;
  }, [geometry]);

  useEffect(() => {
    if (geometry && !geometry.attributes.relativeDepth) {
      setLoading(true);
      const worker = new Worker(new URL('../../lib/peelingWorker.ts', import.meta.url));
      
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
          [direction.x, direction.y, direction.z],
          averageNormal(normals[activeLineIndex] ?? []),
        );
      } else if (activeLine.length > 2 && onPathSelected) {
        const pointsArray = activeLine.map(p => [p.x, p.y, p.z] as Vec3);
        onPathSelected(pointsArray, averageNormal(normals[activeLineIndex] ?? []));
      }
    }
  });

  useEffect(() => {
    notifySelection();
  }, [lines, activeLineIndex]);

  // World coordinates -> the model's own coordinates (undoes the "Vänd X/Y/Z" rotation)
  const toLocal = (world: THREE.Vector3) =>
    groupRef.current ? groupRef.current.worldToLocal(world.clone()) : world.clone();

  const handleClick = (e: import('@react-three/fiber').ThreeEvent<MouseEvent>) => {
    if (!e.shiftKey || clickMode === 'view') return;
    e.stopPropagation();
    const p = toLocal(e.point);
    // The face normal is in the mesh's object space, which equals the model coordinates
    const n = e.face?.normal ? e.face.normal.clone().normalize() : new THREE.Vector3(0, 0, 1);

    if (clickMode === 'single') {
      onSingleClick?.([p.x, p.y, p.z], [n.x, n.y, n.z]);
      return;
    }

    const startNew = e.altKey || activeLineIndex < 0 || activeLineIndex >= lines.length;
    if (startNew) {
      const index = lines.length;
      setLines([...lines, [p]]);
      setNormals([...normals, [n]]);
      setActiveLineIndex(index);
    } else {
      setLines(lines.map((line, i) => (i === activeLineIndex ? [...line, p] : line)));
      setNormals(normals.map((ns, i) => (i === activeLineIndex ? [...ns, n] : ns)));
    }
  };

  if (!geometry) return null;

  return (
    <group rotation={meshRotation} ref={groupRef}>
      <ViewDirTracker groupRef={groupRef} viewDirRef={viewDirRef} />
      <FaceCarvedSide counter={faceCounter} geometry={geometry} groupRef={groupRef} />
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
                toLocal={toLocal}
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

      {markers?.map((m, i) => (
        <MarkerLine key={`marker-${i}`} from={m.from} to={m.to} color={m.color ?? "#16a34a"} />
      ))}
      {autoPoints && autoPoints.length > 0 && <PointCloud points={autoPoints} size={pointSize * 0.6} />}
    </group>
  );
}
