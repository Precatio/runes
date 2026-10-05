import { NextResponse } from 'next/server';

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
const MAX_BYTES = 25 * 1024 * 1024;
const MAX_REDIRECTS = 3;

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

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const imageUrl = searchParams.get('url');

  if (!imageUrl) {
    return new NextResponse('Missing url parameter', { status: 400 });
  }

  const initial = isAllowedUrl(imageUrl);
  if (!initial) {
    return new NextResponse('Host not allowed', { status: 403 });
  }
  let target: URL = initial;

  try {
    // Follow redirects manually so every hop is checked against the allowlist.
    let response: Response | null = null;
    for (let hop = 0; hop <= MAX_REDIRECTS; hop++) {
      response = await fetch(target, {
        redirect: 'manual',
        headers: { 'User-Agent': 'Bifrost/1.0 (image proxy)' },
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
    const declaredLength = Number(response.headers.get('content-length') || 0);
    if (declaredLength > MAX_BYTES) {
      return new NextResponse('Image too large', { status: 413 });
    }

    const buffer = await response.arrayBuffer();
    if (buffer.byteLength > MAX_BYTES) {
      return new NextResponse('Image too large', { status: 413 });
    }

    return new NextResponse(buffer, {
      headers: {
        'Content-Type': contentType,
        'Cache-Control': 'public, max-age=31536000',
      },
    });
  } catch (error) {
    console.error('Image proxy error:', error);
    return new NextResponse('Failed to proxy image', { status: 500 });
  }
}
