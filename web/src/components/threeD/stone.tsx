import React, { useState, useEffect, useMemo } from "react";
import { useFrame, useThree } from "@react-three/fiber";
import { useBounds } from "@react-three/drei";
import * as THREE from "three";
import { peelingFragmentShader, peelingVertexShader, setUniforms } from "./shaders";
import type { Vec3, ViewDirection } from "../ThreeDViewer";

export function StoneMesh({ geometry, onClick, resetCounter, topografyMode, planeNormal, offset, sensitivity,
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

// The stone's carved side as a direction in the model's own coordinates: the direction in which the stone is thinnest
// (least spread of its vertices; the cross product of the two directions of greatest spread), turned towards the side
// most of the surface faces – the same estimate the analysis engine uses when no view is given
// (api/routers/threed.py, _estimated_normal).
function carvedSideNormal(geometry: THREE.BufferGeometry): THREE.Vector3 | null {
  const pos = geometry.getAttribute('position');
  if (!pos || pos.count < 3) return null;
  const step = Math.max(1, Math.floor(pos.count / 200000));
  const mean = new THREE.Vector3(), v = new THREE.Vector3();
  let n = 0;
  for (let i = 0; i < pos.count; i += step) { mean.add(v.fromBufferAttribute(pos, i)); n++; }
  mean.divideScalar(n);
  const C = [0, 0, 0, 0, 0, 0, 0, 0, 0];
  for (let i = 0; i < pos.count; i += step) {
    v.fromBufferAttribute(pos, i).sub(mean);
    const a = [v.x, v.y, v.z];
    for (let r = 0; r < 3; r++) for (let c = 0; c < 3; c++) C[r * 3 + c] += a[r] * a[c];
  }
  const apply = (x: THREE.Vector3) => new THREE.Vector3(C[0] * x.x + C[1] * x.y + C[2] * x.z, C[3] * x.x + C[4] * x.y + C[5] * x.z, C[6] * x.x + C[7] * x.y + C[8] * x.z);
  const power = (start: THREE.Vector3, away?: THREE.Vector3) => {
    let x = start.clone().normalize();
    for (let k = 0; k < 100; k++) {
      if (away) x.sub(away.clone().multiplyScalar(x.dot(away)));
      x = apply(x);
      if (away) x.sub(away.clone().multiplyScalar(x.dot(away)));
      if (x.lengthSq() === 0) return null;
      x.normalize();
    }
    return x;
  };
  const e1 = power(new THREE.Vector3(1, 0.3, 0.2));
  const e2 = e1 && power(new THREE.Vector3(0.2, 1, 0.3), e1);
  if (!e1 || !e2) return null;
  const normal = new THREE.Vector3().crossVectors(e1, e2).normalize();
  const nrm = geometry.getAttribute('normal');
  if (nrm) {
    let side = 0;
    for (let i = 0; i < nrm.count; i += step) side += v.fromBufferAttribute(nrm, i).dot(normal);
    if (side < 0) normal.negate();
  }
  return normal;
}

// Turns the camera to look straight at the carved side; pressed again while already facing it, the other side
export function FaceCarvedSide({ counter, geometry, groupRef }: {
  counter: number; geometry: THREE.BufferGeometry; groupRef: React.RefObject<THREE.Group | null>;
}) {
  const { camera, controls } = useThree();
  useEffect(() => {
    if (!counter || !groupRef.current) return;
    const local = carvedSideNormal(geometry);
    if (!local) return;
    const world = local.applyQuaternion(groupRef.current.getWorldQuaternion(new THREE.Quaternion())).normalize();
    const orbit = controls as unknown as { target: THREE.Vector3; update: () => void } | null;
    const target = orbit?.target ?? new THREE.Vector3();
    const toCamera = camera.position.clone().sub(target);
    const dist = toCamera.length() || 1;
    if (toCamera.normalize().dot(world) > 0.995) world.negate(); // already facing it: show the other side
    camera.position.copy(target).add(world.multiplyScalar(dist));
    camera.lookAt(target);
    orbit?.update();
  }, [counter]); // eslint-disable-line react-hooks/exhaustive-deps -- only on a new press
  return null;
}

export function ViewDirTracker({ groupRef, viewDirRef }: {
  groupRef: React.RefObject<THREE.Group | null>;
  viewDirRef?: React.MutableRefObject<ViewDirection | null>;
}) {
  const { camera } = useThree();
  const tmp = useMemo(() => ({ dir: new THREE.Vector3(), up: new THREE.Vector3(), q: new THREE.Quaternion() }), []);
  useFrame(() => {
    if (!viewDirRef || !groupRef.current) return;
    camera.getWorldDirection(tmp.dir);
    tmp.dir.negate(); // from the stone towards the camera
    tmp.up.set(0, 1, 0).applyQuaternion(camera.quaternion); // screen up in world space
    groupRef.current.getWorldQuaternion(tmp.q).invert();
    tmp.dir.applyQuaternion(tmp.q).normalize();
    tmp.up.applyQuaternion(tmp.q).normalize();
    viewDirRef.current = { toward: [tmp.dir.x, tmp.dir.y, tmp.dir.z], up: [tmp.up.x, tmp.up.y, tmp.up.z] };
  });
  return null;
}

export function averageNormal(normals: THREE.Vector3[]): Vec3 | undefined {
  if (normals.length === 0) return undefined;
  const sum = new THREE.Vector3();
  for (const n of normals) sum.add(n);
  if (sum.lengthSq() === 0) return undefined;
  sum.normalize();
  return [sum.x, sum.y, sum.z];
}
