"use client";

import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { API_URL } from "@/lib/api";
import { PUBLIC_SITE } from "@/lib/site";

// What is loading: each request to the analysis engine (bytes received of the expected size, 0 when the size is not
// known) and a page change that has not finished
type Load = { got: number; total: number };
const loads = new Map<number, Load>();
const listeners = new Set<() => void>();
const emit = () => listeners.forEach(f => f());
let nextId = 0;
let patched = false;

// Polls that run in the background should not show the bar
const SKIP = [/\/api\/r\/status/];

function start(total = 0) {
  const id = nextId++;
  loads.set(id, { got: 0, total });
  emit();
  return id;
}
function finish(id: number) {
  if (loads.delete(id)) emit();
}

// Below this size a body arrives at once after its headers, so following its bytes would add work and show nothing
const FOLLOW_BYTES = 64 * 1024;
// A followed body that nobody reads for this long (the page only looked at the status) no longer holds the bar
const IDLE_MS = 10000;

/** Counts the requests to the analysis engine, and their bytes when the server gives the size (Content-Length). */
function patchFetch() {
  // The public website makes no requests to the analysis engine
  if (patched || typeof window === "undefined" || PUBLIC_SITE) return;
  patched = true;
  const original = window.fetch.bind(window);
  window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
    if (!(url.startsWith(API_URL) || url.startsWith("/api/")) || SKIP.some(r => r.test(url))) return original(input, init);
    const id = start();
    let res: Response;
    try {
      res = await original(input, init);
    } catch (e) {
      finish(id);
      throw e;
    }
    // The body is counted after decompression: the server gives the uncompressed size in X-Content-Length (api/cache.py);
    // without it a compressed body's size is unknown
    const total = Number(res.headers.get("x-content-length"))
      || (res.headers.get("content-encoding") ? 0 : Number(res.headers.get("content-length")) || 0);
    // Unknown or small sizes: the load ends with the headers, and the body is left alone
    if (!res.body || total < FOLLOW_BYTES) { finish(id); return res; }
    const load = loads.get(id);
    if (load) load.total = total;
    // Follow the download as the page reads the body: a pass-through stream, not a copy, so the body is held only once
    const reader = res.body.getReader();
    let idle = window.setTimeout(() => finish(id), IDLE_MS);
    const done = () => { window.clearTimeout(idle); finish(id); };
    const body = new ReadableStream<Uint8Array>({
      async pull(controller) {
        window.clearTimeout(idle);
        try {
          const { done: end, value } = await reader.read();
          if (end) { done(); controller.close(); return; }
          const l = loads.get(id);
          if (l && value) { l.got += value.length; emit(); }
          idle = window.setTimeout(() => finish(id), IDLE_MS);
          controller.enqueue(value);
        } catch (e) {
          // aborted or failed: the page handles the error
          done();
          controller.error(e);
        }
      },
      cancel(reason) {
        done();
        return reader.cancel(reason);
      },
    });
    const followed = new Response(body, { status: res.status, statusText: res.statusText, headers: res.headers });
    // Keep what a constructed Response cannot carry over
    Object.defineProperty(followed, "url", { value: res.url });
    Object.defineProperty(followed, "redirected", { value: res.redirected });
    Object.defineProperty(followed, "type", { value: res.type });
    return followed;
  };
}

/** A thin bar at the top while pages and their data load: the real share when the sizes are known, otherwise creeping
 *  towards 90 % until the data has come. A share is also shown in figures when the loading takes more than a second. */
export default function LoadingBar() {
  const pathname = usePathname();
  const [active, setActive] = useState(false);
  const [value, setValue] = useState(0);
  const [visible, setVisible] = useState(false);
  const [slow, setSlow] = useState(false);
  const since = useRef(0);
  const nav = useRef<number | null>(null);

  useEffect(() => {
    patchFetch();
    const update = () => setActive(loads.size > 0);
    listeners.add(update);
    update();
    // A click on a link to another page in the app: loading until the address has changed
    const onClick = (e: MouseEvent) => {
      if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      const a = (e.target as HTMLElement | null)?.closest?.("a");
      if (!a || a.target === "_blank" || a.hasAttribute("download")) return;
      const href = new URL(a.href, window.location.href);
      if (href.origin !== window.location.origin || href.pathname === window.location.pathname) return;
      if (nav.current !== null) finish(nav.current);
      const id = start();
      nav.current = id;
      window.setTimeout(() => finish(id), 15000);
    };
    document.addEventListener("click", onClick, true);
    return () => { listeners.delete(update); document.removeEventListener("click", onClick, true); };
  }, []);

  useEffect(() => {
    if (nav.current !== null) { finish(nav.current); nav.current = null; }
  }, [pathname]);

  useEffect(() => {
    if (!active) {
      if (!visible) return;
      // Done: the bar fills (below) and fades
      const t = window.setTimeout(() => { setVisible(false); setSlow(false); setValue(0); }, 350);
      return () => window.clearTimeout(t);
    }
    since.current = Date.now();
    // Only loads that take a moment show the bar, so quick answers do not flicker
    const show = window.setTimeout(() => setVisible(true), 250);
    const tick = window.setInterval(() => {
      const all = [...loads.values()];
      const known = all.length > 0 && all.every(l => l.total > 0);
      const real = known ? all.reduce((s, l) => s + l.got, 0) / all.reduce((s, l) => s + l.total, 0) : 0;
      setValue(v => Math.min(0.97, known ? Math.max(v, real) : v + (0.9 - v) * 0.04));
      if (Date.now() - since.current > 1000) setSlow(true);
    }, 150);
    return () => { window.clearTimeout(show); window.clearInterval(tick); };
  }, [active]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!visible) return null;
  const pct = active ? Math.round(value * 100) : 100;
  return (
    <>
      <div role="progressbar" aria-label="Laddar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={pct}
        className="fixed inset-x-0 top-0 z-[100] h-[3px] pointer-events-none">
        <div className="h-full bg-[#b7410e] shadow-[0_0_8px_rgba(183,65,14,0.6)] transition-[width,opacity] duration-200 ease-out"
          style={{ width: `${pct}%`, opacity: active ? 1 : 0 }} />
      </div>
      {slow && active && (
        <div className="fixed top-2 right-3 z-[100] pointer-events-none rounded-full border border-slate-900/10 bg-white/90 px-2.5 py-0.5 text-[11px] font-semibold text-slate-600 shadow-sm tabular-nums" aria-hidden="true">
          <span>Laddar</span> <span translate="no">{pct} %</span>
        </div>
      )}
    </>
  );
}
