// src/lib/peelingWorker.ts
// Web Worker for Laplacian Smoothing and Relative Depth Calculation
/// <reference lib="webworker" />

declare const self: DedicatedWorkerGlobalScope;
export {};

self.onmessage = function(e) {
  const { positionArray, indexArray, iterations = 20, smoothFactor = 0.5 } = e.data;
  
  const vertexCount = positionArray.length / 3;
  const adjacency: number[][] = new Array(vertexCount).fill(0).map(() => []);
  
  self.postMessage({ type: 'progress', message: 'Bygger grannskapsgraf...', percent: 10 });

  if (indexArray && indexArray.length > 0) {
      for (let i = 0; i < indexArray.length; i += 3) {
          const a = indexArray[i];
          const b = indexArray[i+1];
          const c = indexArray[i+2];
          
          if (!adjacency[a].includes(b)) adjacency[a].push(b);
          if (!adjacency[a].includes(c)) adjacency[a].push(c);
          if (!adjacency[b].includes(a)) adjacency[b].push(a);
          if (!adjacency[b].includes(c)) adjacency[b].push(c);
          if (!adjacency[c].includes(a)) adjacency[c].push(a);
          if (!adjacency[c].includes(b)) adjacency[c].push(b);
      }
  } else {
      for(let i = 0; i < vertexCount; i++) {
          const a = i * 3;
          const b = i * 3 + 1;
          const c = i * 3 + 2;
          if(adjacency[a] && adjacency[b] && adjacency[c]) {
              adjacency[a].push(b, c);
              adjacency[b].push(a, c);
              adjacency[c].push(a, b);
          }
      }
  }

  self.postMessage({ type: 'progress', message: 'Applicerar Laplacian Smoothing...', percent: 20 });

  const smoothedPositions = new Float32Array(positionArray);
  const tempPositions = new Float32Array(positionArray);
  
  for (let it = 0; it < iterations; it++) {
      for (let i = 0; i < vertexCount; i++) {
          const neighbors = adjacency[i];
          if (!neighbors || neighbors.length === 0) continue;
          
          let sumX = 0, sumY = 0, sumZ = 0;
          for (let j = 0; j < neighbors.length; j++) {
              const nIdx = neighbors[j] * 3;
              sumX += smoothedPositions[nIdx];
              sumY += smoothedPositions[nIdx+1];
              sumZ += smoothedPositions[nIdx+2];
          }
          
          const avgX = sumX / neighbors.length;
          const avgY = sumY / neighbors.length;
          const avgZ = sumZ / neighbors.length;
          
          const i3 = i * 3;
          tempPositions[i3]     = smoothedPositions[i3]     + smoothFactor * (avgX - smoothedPositions[i3]);
          tempPositions[i3+1]   = smoothedPositions[i3+1]   + smoothFactor * (avgY - smoothedPositions[i3+1]);
          tempPositions[i3+2]   = smoothedPositions[i3+2]   + smoothFactor * (avgZ - smoothedPositions[i3+2]);
      }
      
      for(let k = 0; k < smoothedPositions.length; k++) {
          smoothedPositions[k] = tempPositions[k];
      }
      
      self.postMessage({ type: 'progress', message: 'Applicerar utjämning...', percent: 20 + (50 * (it/iterations)) });
  }

  self.postMessage({ type: 'progress', message: 'Beräknar relativt djup...', percent: 80 });

  const relativeDepths = new Float32Array(vertexCount);
  
  for (let i = 0; i < vertexCount; i++) {
      const i3 = i * 3;
      const ox = positionArray[i3];
      const oy = positionArray[i3+1];
      const oz = positionArray[i3+2];
      
      const sx = smoothedPositions[i3];
      const sy = smoothedPositions[i3+1];
      const sz = smoothedPositions[i3+2];
      
      const dx = ox - sx;
      const dy = oy - sy;
      const dz = oz - sz;
      
      const dist = Math.sqrt(dx*dx + dy*dy + dz*dz);
      // Förenkling: vi förutsätter att runor är negativt huggdjup
      relativeDepths[i] = -dist; 
  }
  
  let minRelative = Infinity;
  let maxRelative = -Infinity;
  for (let i = 0; i < vertexCount; i++) {
    if (relativeDepths[i] < minRelative) minRelative = relativeDepths[i];
    if (relativeDepths[i] > maxRelative) maxRelative = relativeDepths[i];
  }

  self.postMessage({ type: 'progress', message: 'Klar!', percent: 100 });
  
  self.postMessage({ 
      type: 'done', 
      relativeDepths: relativeDepths,
      minRelative,
      maxRelative
  }, [relativeDepths.buffer]);
};
