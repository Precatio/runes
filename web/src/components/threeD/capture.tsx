import { useEffect } from "react";
import { useThree } from "@react-three/fiber";
import * as THREE from "three";

// Renders the current view again at `scale` times the screen's resolution (at most 8192 px on the long side) and saves
// it as a PNG: the same angle, light and contrast as on screen, for reading traces or for a figure. The canvas is
// copied the moment toBlob is called, so the normal size can be restored straight after.
export function SnapshotTaker({ trigger, scale, name, onDone }: { trigger: number; scale: number; name: string; onDone: (msg: string) => void }) {
  const { gl, scene, camera, size } = useThree();
  useEffect(() => {
    if (!trigger) return;
    const prev = gl.getPixelRatio();
    const maxDim = Math.min(gl.capabilities.maxTextureSize || 8192, 8192);
    const ratio = Math.min(prev * scale, maxDim / Math.max(size.width, size.height));
    const base = name.replace(/\.[^.]+$/, '').replace(/[^\wåäöÅÄÖ.-]+/g, '_');
    try {
      gl.setPixelRatio(ratio);
      gl.setSize(size.width, size.height, false);
      gl.render(scene, camera);
      const w = gl.domElement.width, h = gl.domElement.height;
      gl.domElement.toBlob(blob => {
        if (!blob) { onDone('Bilden kunde inte sparas (för stor för grafikkortet?). Prova en lägre upplösning.'); return; }
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `${base}_vy_${w}x${h}.png`;
        a.click();
        window.setTimeout(() => URL.revokeObjectURL(a.href), 10000);
        onDone(`Bilden sparades: ${w} × ${h} bildpunkter. Ange vem som skannat stenen när du använder bilden.`);
      }, 'image/png');
    } catch {
      onDone('Bilden kunde inte sparas. Prova en lägre upplösning.');
    } finally {
      gl.setPixelRatio(prev);
      gl.setSize(size.width, size.height, false);
    }
  }, [trigger]); // eslint-disable-line react-hooks/exhaustive-deps
  return null;
}

export function CameraCapturer({ trigger, onCapture }: { trigger: number, onCapture: (dir: THREE.Vector3) => void }) {
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
