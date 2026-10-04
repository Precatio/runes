// Image helpers for the 2D analysis (downscaling, persistent data URLs)

export function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error("Kunde inte läsa bilden."));
    img.src = src;
  });
}

// Draws (a region of) an image scaled so that its longest side is at most maxSide
export function drawScaled(
  img: CanvasImageSource & { naturalWidth?: number; naturalHeight?: number; width: number; height: number },
  maxSide: number,
  region?: { x: number; y: number; w: number; h: number },
): HTMLCanvasElement {
  const srcW = region?.w ?? (img.naturalWidth || img.width);
  const srcH = region?.h ?? (img.naturalHeight || img.height);
  const scale = Math.min(1, maxSide / Math.max(srcW, srcH));
  const canvas = document.createElement("canvas");
  canvas.width = Math.max(1, Math.round(srcW * scale));
  canvas.height = Math.max(1, Math.round(srcH * scale));
  const ctx = canvas.getContext("2d")!;
  ctx.drawImage(img, region?.x ?? 0, region?.y ?? 0, srcW, srcH, 0, 0, canvas.width, canvas.height);
  return canvas;
}

// A small, persistent copy of an image (blob: URLs stop working after a reload)
export async function persistentDataURL(src: string, maxSide = 1600, quality = 0.85): Promise<string> {
  if (src.startsWith("data:") && src.length < 1_500_000) return src;
  const img = await loadImage(src);
  return drawScaled(img, maxSide).toDataURL("image/jpeg", quality);
}

export function canvasToBlob(canvas: HTMLCanvasElement, type = "image/jpeg", quality = 0.9): Promise<Blob> {
  return new Promise((resolve, reject) =>
    canvas.toBlob(b => (b ? resolve(b) : reject(new Error("Kunde inte skapa bild."))), type, quality),
  );
}

export async function dataURLToFile(dataUrl: string, name: string): Promise<File> {
  const blob = await (await fetch(dataUrl)).blob();
  return new File([blob], name, { type: blob.type || "image/png" });
}
