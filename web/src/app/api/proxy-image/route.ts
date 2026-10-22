import { NextResponse } from 'next/server';
import sharp from 'sharp';

// Only proxy images from known cultural-heritage hosts (K-samsök sources).
// Extend with a comma-separated list in PROXY_IMAGE_ALLOWED_HOSTS.
const DEFAULT_ALLOWED_HOSTS = [
  'kulturarvsdata.se',
  'raa.se',
  'digitaltmuseum.se',
  'digitaltmuseum.org',
  'alvin-portal.org',
  'shm.se',
  'wikimedia.org',
];
const ALLOWED_HOSTS = [
  ...DEFAULT_ALLOWED_HOSTS,
  ...(process.env.PROXY_IMAGE_ALLOWED_HOSTS || '')
    .split(',')
    .map(h => h.trim().toLowerCase())
    .filter(Boolean),
];
const MAX_BYTES = 60 * 1024 * 1024;  // archival TIFFs from the National Heritage Board can be large
const FETCH_TIMEOUT_MS = 20000;
// Formats a browser (and the canvas used by the 2D analysis) can show as they are
const WEB_FORMATS = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];
// Formats whose decoders (librsvg, libheif) have had security advisories and that the K-samsök images do not need
const REJECTED_FORMATS = ['image/svg+xml', 'image/heif', 'image/heic', 'image/heif-sequence', 'image/heic-sequence', 'image/avif'];
// Largest image sharp may decode (100 MP is about 400 MB of RGBA)
const MAX_INPUT_PIXELS = 100_000_000;
const MAX_REDIRECTS = 3;
// A host that just failed to answer is not retried for a minute, so twenty thumbnails do not each wait for it
const DOWN_FOR_MS = 60000;
const downHosts = new Map<string, number>();

function isAllowedUrl(raw: string): URL | null {
  let url: URL;
  try {
    url = new URL(raw);
  } catch {
    return null;
  }
  if (url.protocol !== 'https:' && url.protocol !== 'http:') return null;
  if (url.username || url.password) return null;
  if (url.port && url.port !== '80' && url.port !== '443') return null;
  const host = url.hostname.toLowerCase();
  const allowed = ALLOWED_HOSTS.some(h => host === h || host.endsWith(`.${h}`));
  return allowed ? url : null;
}

// Read a body up to `max` bytes; a server that sends more than that (even without a Content-Length) is cut off
async function readCapped(response: Response, max: number): Promise<Uint8Array<ArrayBuffer> | null> {
  if (!response.body) return new Uint8Array(0);
  const reader = response.body.getReader();
  const chunks: Uint8Array[] = [];
  let size = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    size += value.byteLength;
    if (size > max) {
      await reader.cancel().catch(() => {});
      return null;
    }
    chunks.push(value);
  }
  const out = new Uint8Array(size);
  let at = 0;
  for (const c of chunks) { out.set(c, at); at += c.byteLength; }
  return out;
}

// sharp picks the decoder from the bytes, not the Content-Type, so also refuse SVG/XML text and
// ISO-BMFF (HEIF/HEIC/AVIF) files that arrive under another declared type
function isRejectedContent(buf: Uint8Array): boolean {
  const head = new TextDecoder().decode(buf.subarray(0, 512)).trimStart();  // the decoder drops a UTF-8 BOM
  if (head.startsWith('<')) return true;
  return buf.byteLength >= 12 && buf[4] === 0x66 && buf[5] === 0x74 && buf[6] === 0x79 && buf[7] === 0x70; // 'ftyp'
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const imageUrl = searchParams.get('url');
  // Optional width: thumbnails are scaled down; other formats (e.g. TIFF) are always converted to JPEG
  const width = Math.min(4000, Math.max(0, Number(searchParams.get('w') || 0))) || null;

  if (!imageUrl) {
    return new NextResponse('Missing url parameter', { status: 400 });
  }

  const initial = isAllowedUrl(imageUrl);
  if (!initial) {
    return new NextResponse('Host not allowed', { status: 403 });
  }
  let target: URL = initial;
  const down = downHosts.get(initial.hostname);
  if (down && Date.now() - down < DOWN_FOR_MS) {
    return new NextResponse('Image server did not respond', { status: 504 });
  }

  try {
    // Follow redirects manually so every hop is checked against the allowlist.
    let response: Response | null = null;
    for (let hop = 0; hop <= MAX_REDIRECTS; hop++) {
      response = await fetch(target, {
        redirect: 'manual',
        headers: { 'User-Agent': 'Vitki/1.0 (image proxy)' },
        signal: AbortSignal.timeout(FETCH_TIMEOUT_MS),
      });
      if (response.status < 300 || response.status >= 400) break;
      const location = response.headers.get('location');
      const next = location ? isAllowedUrl(new URL(location, target).toString()) : null;
      if (!next) {
        return new NextResponse('Redirect target not allowed', { status: 403 });
      }
      target = next;
      response = null;
    }

    if (!response || !response.ok) {
      throw new Error(`Failed to fetch image: ${response?.statusText ?? 'too many redirects'}`);
    }

    const contentType = response.headers.get('content-type') || '';
    if (!contentType.startsWith('image/')) {
      return new NextResponse('Not an image', { status: 415 });
    }
    const type = contentType.split(';')[0].trim().toLowerCase();
    if (REJECTED_FORMATS.includes(type)) {
      return new NextResponse('Image format not supported', { status: 415 });
    }
    const declaredLength = Number(response.headers.get('content-length') || 0);
    if (declaredLength > MAX_BYTES) {
      return new NextResponse('Image too large', { status: 413 });
    }

    const buffer = await readCapped(response, MAX_BYTES);
    if (!buffer) {
      return new NextResponse('Image too large', { status: 413 });
    }

    if (isRejectedContent(buffer)) {
      return new NextResponse('Image format not supported', { status: 415 });
    }
    if (!width && WEB_FORMATS.includes(type)) {
      return new NextResponse(buffer, {
        headers: { 'Content-Type': contentType, 'Cache-Control': 'public, max-age=31536000' },
      });
    }
    // TIFF and other archival formats, and thumbnails: decode and re-encode as JPEG
    let img = sharp(Buffer.from(buffer.buffer, buffer.byteOffset, buffer.byteLength), { limitInputPixels: MAX_INPUT_PIXELS }).rotate();
    if (width) img = img.resize({ width, withoutEnlargement: true });
    const jpeg = await img.flatten({ background: '#ffffff' }).jpeg({ quality: 85 }).toBuffer();
    return new NextResponse(new Uint8Array(jpeg), {
      headers: { 'Content-Type': 'image/jpeg', 'Cache-Control': 'public, max-age=31536000' },
    });
  } catch (error) {
    const cause = (error as { cause?: { code?: string } })?.cause?.code ?? '';
    const timedOut = (error instanceof Error && (error.name === 'TimeoutError' || error.name === 'AbortError'))
      || cause.includes('TIMEOUT') || cause === 'ECONNREFUSED' || cause === 'ENOTFOUND';
    if (timedOut) downHosts.set(target.hostname, Date.now());
    console.error('Image proxy error:', error);
    return new NextResponse(timedOut ? 'Image server did not respond' : 'Failed to proxy image', { status: timedOut ? 504 : 502 });
  }
}
