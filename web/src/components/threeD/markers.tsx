import { useEffect, useMemo, useRef } from "react";
import { TransformControls } from "@react-three/drei";
import * as THREE from "three";
import type { Vec3, ViewerPoint } from "../ThreeDViewer";

export function SplineLine({ points, color = "red" }: { points: THREE.Vector3[], color?: string }) {
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
  // R3F only disposes on unmount, not when a prop's geometry is swapped, so free each replaced line geometry here
  useEffect(() => () => geometry.dispose(), [geometry]);

  if (points.length < 2) return null;

  return (
    // @ts-expect-error - line geometry is not fully typed in three-fiber
    <line geometry={geometry}>
      <lineBasicMaterial color={color} linewidth={5} depthTest={false} transparent={true} />
    </line>
  );
}

// A straight marker line; the points are rebuilt only when the coordinates change, not on every viewer render
export function MarkerLine({ from, to, color }: { from: Vec3; to: Vec3; color: string }) {
  const [fx, fy, fz] = from;
  const [tx, ty, tz] = to;
  const points = useMemo(() => [new THREE.Vector3(fx, fy, fz), new THREE.Vector3(tx, ty, tz)], [fx, fy, fz, tx, ty, tz]);
  return <SplineLine points={points} color={color} />;
}

interface DraggablePointProps {
  position: THREE.Vector3;
  color: string;
  size: number;
  onDragStart?: () => void;
  onDragEnd: (pos: THREE.Vector3) => void;
  setDragging: (dragging: boolean) => void;
  toLocal: (world: THREE.Vector3) => THREE.Vector3;
}

export function DraggablePoint({ position, color, size, onDragStart, onDragEnd, setDragging, toLocal }: DraggablePointProps) {
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
          onDragEnd(toLocal(worldPos));
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

export function PointCloud({ points, size }: { points: ViewerPoint[]; size: number }) {
  const geometry = useMemo(() => {
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(points.flatMap(p => p.position), 3));
    const color = new THREE.Color();
    g.setAttribute('color', new THREE.Float32BufferAttribute(points.flatMap(p => color.set(p.color).toArray()), 3));
    return g;
  }, [points]);
  useEffect(() => () => geometry.dispose(), [geometry]);
  return (
    <points geometry={geometry}>
      <pointsMaterial size={size} vertexColors depthTest={false} transparent sizeAttenuation />
    </points>
  );
}
