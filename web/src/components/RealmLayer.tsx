"use client";

import { useEffect, useMemo, useState } from "react";
import { divIcon, type PathOptions } from "leaflet";
import { GeoJSON, Marker, Pane } from "react-leaflet";
import type { Feature, FeatureCollection, Geometry } from "geojson";
import { DASH, REALMS, townMark, townsAt, urlOf, type Certainty } from "@/lib/realms";

// The realms' approximate borders at the chosen time (src/lib/realms.ts), drawn under the stones on the point map and as
// outlines over the hexagons on the pattern map. Neither the areas nor the names take the mouse, so that the stones'
// and hexagons' tooltips still work.
interface RealmProps {
  epoch: string; id: string; realm: string; certainty: Certainty; label: string; label_lat: number; label_lon: number;
}
type Realms = FeatureCollection<Geometry, RealmProps>;

// One request per file (the realms, the old lands), shared by every map on the page
const loading = new Map<string, Promise<Realms>>();
const load = (url: string) => {
  if (!loading.has(url)) loading.set(url, fetch(url)
    .then(r => (r.ok ? r.json() : Promise.reject(new Error(`Fel ${r.status}`))))
    .catch(e => { loading.delete(url); throw e; }));
  return loading.get(url)!;
};

const esc = (s: string) => s.replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c] ?? c);

export default function RealmLayer({ epoch, outline = false }: { epoch: string; outline?: boolean }) {
  const [data, setData] = useState<Realms | null>(null);
  const url = urlOf(epoch);
  useEffect(() => {
    let cancelled = false;
    load(url).then(d => { if (!cancelled) setData(d); }).catch(() => {});
    return () => { cancelled = true; };
  }, [url]);
  const shown = useMemo<Realms | null>(() => (data ? { ...data, features: data.features.filter(f => f.properties.epoch === epoch) } : null),
                                       [data, epoch]);
  if (!shown) return null;

  const style = (f?: Feature<Geometry, RealmProps>): PathOptions => {
    const p = f?.properties;
    const color = REALMS[p?.realm ?? ""]?.color ?? "#64748b";
    const core = p?.certainty === "karna";
    return outline
      ? { color, weight: core ? 2.5 : 2, opacity: 1, dashArray: DASH[p?.certainty ?? "karna"], fill: false }
      : { color, weight: core ? 1.5 : 1.2, opacity: 0.9, dashArray: DASH[p?.certainty ?? "karna"], fillColor: color,
          fillOpacity: core ? 0.18 : 0.08 };
  };
  return (
    <>
      <Pane name="realms" style={{ zIndex: outline ? 450 : 350, pointerEvents: "none" }}>
        {/* A white halo under the outlines, so that they stand out against the hexagons */}
        {outline && <GeoJSON key={`halo-${epoch}`} data={shown} interactive={false} style={{ color: "#ffffff", weight: 5, opacity: 0.75, fill: false }} />}
        <GeoJSON key={epoch} data={shown} interactive={false} style={style} />
      </Pane>
      <Pane name="realm-labels" style={{ zIndex: 460, pointerEvents: "none" }}>
        {shown.features.filter(f => f.properties.label).map(f => (
          <Marker key={`${epoch}-${f.properties.id}`} position={[f.properties.label_lat, f.properties.label_lon]}
            interactive={false} keyboard={false}
            icon={divIcon({ className: "realm-label", iconSize: [0, 0],
                            html: `<span style="color:${REALMS[f.properties.realm]?.color ?? "#334155"}${epoch === "land" ? ";font-size:9px;letter-spacing:0.02em" : ""}">${esc(f.properties.label)}</span>` })} />
        ))}
        {townsAt(epoch).map(t => (
          <Marker key={`town-${t.id}`} position={[t.lat, t.lon]} interactive={false} keyboard={false}
            icon={divIcon({ className: "realm-town", iconSize: [0, 0],
                            html: `<span style="position:absolute;transform:translate(-50%,-50%);display:flex;align-items:center;gap:3px;white-space:nowrap;font:600 10px system-ui,sans-serif;color:#7c2d12;text-shadow:0 0 2px #fff,0 0 2px #fff">${townMark(t.type)}<span style="position:absolute;left:12px">${esc(t.name)}</span></span>` })} />
        ))}
      </Pane>
    </>
  );
}
