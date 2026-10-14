"use client";

import { useEffect, useMemo, useState } from "react";
import { divIcon, type PathOptions } from "leaflet";
import { GeoJSON, Marker, Pane } from "react-leaflet";
import type { Feature, FeatureCollection, Geometry } from "geojson";
import { DASH, REALMS, REALMS_URL, type Certainty } from "@/lib/realms";

// The realms' approximate borders at the chosen time (src/lib/realms.ts), drawn under the stones on the point map and as
// outlines over the hexagons on the pattern map. Neither the areas nor the names take the mouse, so that the stones'
// and hexagons' tooltips still work.
interface RealmProps {
  epoch: string; id: string; realm: string; certainty: Certainty; label: string; label_lat: number; label_lon: number;
}
type Realms = FeatureCollection<Geometry, RealmProps>;

let loading: Promise<Realms> | null = null;
const load = () => (loading ??= fetch(REALMS_URL)
  .then(r => (r.ok ? r.json() : Promise.reject(new Error(`Fel ${r.status}`))))
  .catch(e => { loading = null; throw e; }));

const esc = (s: string) => s.replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c] ?? c);

export default function RealmLayer({ epoch, outline = false }: { epoch: string; outline?: boolean }) {
  const [data, setData] = useState<Realms | null>(null);
  useEffect(() => {
    let cancelled = false;
    load().then(d => { if (!cancelled) setData(d); }).catch(() => {});
    return () => { cancelled = true; };
  }, []);
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
                            html: `<span style="color:${REALMS[f.properties.realm]?.color ?? "#334155"}">${esc(f.properties.label)}</span>` })} />
        ))}
      </Pane>
    </>
  );
}
