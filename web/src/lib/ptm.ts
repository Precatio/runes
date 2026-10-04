// Polynomial Texture Maps (PTM 1.2, Malzbender et al. 2001) – parser and relighting.
// Supported formats: PTM_FORMAT_LRGB and PTM_FORMAT_RGB (the ones RTIBuilder writes).
//
// Per pixel, luminance under a light direction (lu, lv) is
//   L = a0·lu² + a1·lv² + a2·lu·lv + a3·lu + a4·lv + a5,   a_i = (raw_i − bias_i) · scale_i

export interface PTM {
  format: "LRGB" | "RGB";
  width: number;
  height: number;
  // LRGB: 6 coefficients per pixel; RGB: 6 per pixel and channel (R block, G block, B block)
  coeffs: Float32Array;
  rgb?: Uint8Array; // LRGB only
}

const decoder = new TextDecoder("ascii");

export function parsePTM(buffer: ArrayBuffer): PTM {
  const bytes = new Uint8Array(buffer);
  const tokens: string[] = [];
  let pos = 0;
  // Header: version, format, width, height, 6 scales, 6 biases (whitespace separated)
  while (tokens.length < 16 && pos < bytes.length) {
    while (pos < bytes.length && /\s/.test(String.fromCharCode(bytes[pos]))) pos++;
    const start = pos;
    while (pos < bytes.length && !/\s/.test(String.fromCharCode(bytes[pos]))) pos++;
    tokens.push(decoder.decode(bytes.subarray(start, pos)));
  }
  pos++; // single whitespace before binary data
  if (!tokens[0]?.startsWith("PTM_1.2")) throw new Error("Inte en PTM 1.2-fil.");
  const formatToken = tokens[1];
  const format = formatToken === "PTM_FORMAT_LRGB" ? "LRGB" : formatToken === "PTM_FORMAT_RGB" ? "RGB" : null;
  if (!format) throw new Error(`PTM-formatet ${formatToken} stöds inte (endast LRGB och RGB).`);
  const width = parseInt(tokens[2], 10);
  const height = parseInt(tokens[3], 10);
  const scale = tokens.slice(4, 10).map(Number);
  const bias = tokens.slice(10, 16).map(Number);
  if (!(width > 0 && height > 0) || scale.some(Number.isNaN) || bias.some(Number.isNaN)) {
    throw new Error("Ogiltigt PTM-huvud.");
  }

  const n = width * height;
  const blocks = format === "LRGB" ? 1 : 3;
  const needed = n * 6 * blocks + (format === "LRGB" ? n * 3 : 0);
  if (bytes.length - pos < needed) throw new Error("PTM-filen är ofullständig.");

  const coeffs = new Float32Array(n * 6 * blocks);
  // PTM stores rows bottom-to-top; flip so that row 0 is the top of the image
  for (let b = 0; b < blocks; b++) {
    const base = pos + b * n * 6;
    for (let y = 0; y < height; y++) {
      const srcRow = height - 1 - y;
      for (let x = 0; x < width; x++) {
        const src = base + (srcRow * width + x) * 6;
        const dst = (b * n + y * width + x) * 6;
        for (let i = 0; i < 6; i++) coeffs[dst + i] = (bytes[src + i] - bias[i]) * scale[i];
      }
    }
  }

  let rgb: Uint8Array | undefined;
  if (format === "LRGB") {
    const base = pos + n * 6;
    rgb = new Uint8Array(n * 3);
    for (let y = 0; y < height; y++) {
      const srcRow = height - 1 - y;
      rgb.set(bytes.subarray(base + srcRow * width * 3, base + (srcRow + 1) * width * 3), y * width * 3);
    }
  }
  return { format, width, height, coeffs, rgb };
}

// Diffuse gain (Malzbender et al. 2001): steepens the reflectance function around each
// pixel's estimated normal, which exaggerates surface relief such as shallow carvings.
function applyDiffuseGain(a: number[], gain: number): number[] {
  const [a0, a1, a2, a3, a4, a5] = a;
  const det = 4 * a0 * a1 - a2 * a2;
  if (Math.abs(det) < 1e-9) return a;
  let lu0 = (a2 * a4 - 2 * a1 * a3) / det;
  let lv0 = (a2 * a3 - 2 * a0 * a4) / det;
  const len = Math.hypot(lu0, lv0);
  if (len > 1) { lu0 /= len; lv0 /= len; }
  const g = gain;
  const b3 = (1 - g) * (2 * a0 * lu0 + a2 * lv0) + a3;
  const b4 = (1 - g) * (2 * a1 * lv0 + a2 * lu0) + a4;
  const b5 = (1 - g) * (a0 * lu0 * lu0 + a1 * lv0 * lv0 + a2 * lu0 * lv0) + (a3 - b3) * lu0 + (a4 - b4) * lv0 + a5;
  return [g * a0, g * a1, g * a2, b3, b4, b5];
}

function evalPoly(c: Float32Array | number[], o: number, lu: number, lv: number) {
  return c[o] * lu * lu + c[o + 1] * lv * lv + c[o + 2] * lu * lv + c[o + 3] * lu + c[o + 4] * lv + c[o + 5];
}

export interface RelightOptions {
  lu: number;
  lv: number;
  diffuseGain?: number; // 1 = off
  grayscale?: boolean;
}

export function relight(ptm: PTM, out: ImageData, { lu, lv, diffuseGain = 1, grayscale = false }: RelightOptions) {
  const { width, height, coeffs } = ptm;
  const n = width * height;
  const data = out.data;
  const useGain = diffuseGain > 1.001;
  for (let p = 0; p < n; p++) {
    let r: number, g: number, b: number;
    if (ptm.format === "LRGB") {
      let L: number;
      if (useGain) {
        const a = applyDiffuseGain(Array.from(coeffs.subarray(p * 6, p * 6 + 6)), diffuseGain);
        L = evalPoly(a, 0, lu, lv);
      } else {
        L = evalPoly(coeffs, p * 6, lu, lv);
      }
      L = Math.max(0, L);
      if (grayscale) {
        r = g = b = L * 255;
      } else {
        r = ptm.rgb![p * 3] * L;
        g = ptm.rgb![p * 3 + 1] * L;
        b = ptm.rgb![p * 3 + 2] * L;
      }
    } else {
      const ch = [0, 1, 2].map(k => {
        const o = (k * n + p) * 6;
        const v = useGain
          ? evalPoly(applyDiffuseGain(Array.from(coeffs.subarray(o, o + 6)), diffuseGain), 0, lu, lv)
          : evalPoly(coeffs, o, lu, lv);
        return Math.max(0, v);
      });
      [r, g, b] = ch;
      if (grayscale) r = g = b = 0.299 * r + 0.587 * g + 0.114 * b;
    }
    const q = p * 4;
    data[q] = r > 255 ? 255 : r;
    data[q + 1] = g > 255 ? 255 : g;
    data[q + 2] = b > 255 ? 255 : b;
    data[q + 3] = 255;
  }
}
