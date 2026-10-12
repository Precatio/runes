"use client";

import "leaflet/dist/leaflet.css";
import { useMemo } from "react";
import { MapContainer, Polygon, TileLayer, Tooltip } from "react-leaflet";
import type { LatLngBoundsExpression } from "leaflet";
import { colorOf, TOO_FEW, type PatternStone } from "@/lib/patternMap";

// An equal-area-enough projection for Sweden: kilometres east and north of a reference meridian at 62° N
const LAT0 = 62, LON0 = 16, KX = 111.32 * Math.cos((LAT0 * Math.PI) / 180), KY = 110.57;
const toKm = (lat: number, lon: number) => [(lon - LON0) * KX, lat * KY] as const;
const toLatLon = (x: number, y: number) => [y / KY, x / KX + LON0] as [number, number];

export interface Hex { id: string; corners: [number, number][]; n: number; k: number; examples: string[] }

/** Pointy-top hexagons of the given width (km across the flats); each counts its stones and those with the pattern. */
export function hexbin(stones: PatternStone[], key: string, widthKm: number): Hex[] {
  const size = widthKm / Math.sqrt(3);
  const cells = new Map<string, Hex & { q: number; r: number }>();
  for (const st of stones) {
    const val = st.v[key];
    if (val === null || val === undefined) continue;
    const [x, y] = toKm(st.lat, st.lon);
    const qf = ((Math.sqrt(3) / 3) * x - y / 3) / size, rf = ((2 / 3) * y) / size;
    // Cube rounding to the nearest hexagon
    let q = Math.round(qf), r = Math.round(rf);
    const s = Math.round(-qf - rf);
    const dq = Math.abs(q - qf), dr = Math.abs(r - rf), ds = Math.abs(s - (-qf - rf));
    if (dq > dr && dq > ds) q = -r - s; else if (dr > ds) r = -q - s;
    const id = `${q},${r}`;
    let cell = cells.get(id);
    if (!cell) {
      const cx = size * Math.sqrt(3) * (q + r / 2), cy = size * 1.5 * r;
      const corners = Array.from({ length: 6 }, (_, i) => {
        const a = (Math.PI / 180) * (60 * i - 30);
        return toLatLon(cx + size * Math.cos(a), cy + size * Math.sin(a));
      });
      cell = { id, q, r, corners, n: 0, k: 0, examples: [] };
      cells.set(id, cell);
    }
    cell.n += 1;
    if (val === 1) { cell.k += 1; if (cell.examples.length < 5) cell.examples.push(st.s); }
  }
  return [...cells.values()];
}

/** The extent of the stones, so that both maps of a split view show the same area. */
export function boundsOf(stones: PatternStone[]): LatLngBoundsExpression {
  if (!stones.length) return [[55.3, 11.0], [61.0, 19.0]];
  // The 1st to 99th percentile, so that a few distant stones (Jämtland, Hälsingland) do not zoom the map out
  const q = (xs: number[], p: number) => xs.sort((a, b) => a - b)[Math.floor(p * (xs.length - 1))];
  const lats = stones.map(s => s.lat), lons = stones.map(s => s.lon);
  return [[q(lats, 0.01), q(lons, 0.01)], [q(lats, 0.99), q(lons, 0.99)]];
}

/** One map of hexagons coloured by the share of stones with the pattern; too few stones are shown grey. */
export function HexMap({ hexes, minStones, label, title, bounds }: {
  hexes: Hex[]; minStones: number; label: string; title?: string; bounds: LatLngBoundsExpression;
}) {
  return (
    <div className="relative w-full h-full">
      {title && (
        <div className="absolute top-3 left-1/2 -translate-x-1/2 z-[500] rounded-full bg-white/95 px-3 py-1 text-xs font-bold text-slate-800 shadow">
          {title}
        </div>
      )}
      <MapContainer bounds={bounds} boundsOptions={{ padding: [12, 12] }} className="w-full h-full rounded-[22px]" scrollWheelZoom>
        {/* A grey, faded base map, so that the hexagons carry the colour */}
        <TileLayer className="pattern-basemap"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>-bidragsgivare'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {hexes.map(h => {
          const enough = h.n >= minStones;
          const share = h.n ? h.k / h.n : 0;
          return (
            <Polygon key={h.id} positions={h.corners}
              pathOptions={{ color: "#fcfcfb", weight: 1.5, fillColor: enough ? colorOf(share) : TOO_FEW, fillOpacity: enough ? 0.85 : 0.6,
                             dashArray: enough ? undefined : "3 3" }}>
              <Tooltip sticky>
                <div className="text-xs">
                  <div className="font-bold">{h.n === 1 ? "1 sten" : `${h.n} stenar`}</div>
                  <div><span className="font-semibold">{label}:</span> {`${h.k} har mönstret (${Math.round(share * 100)} %)`}</div>
                  {!enough && <div className="text-slate-500">För få stenar för en säker andel</div>}
                  {h.examples.length > 0 && <div className="text-slate-500">t.ex. <span translate="no">{h.examples.join(", ")}</span></div>}
                </div>
              </Tooltip>
            </Polygon>
          );
        })}
      </MapContainer>
    </div>
  );
}

export default function PatternMaps({ stones, patternKey, label, widthKm, minStones, split }: {
  stones: PatternStone[]; patternKey: string; label: string; widthKm: number; minStones: number; split: boolean;
}) {
  const early = useMemo(() => stones.filter(s => s.y !== null && s.y < 1050), [stones]);
  const late = useMemo(() => stones.filter(s => s.y !== null && s.y >= 1050), [stones]);
  const bounds = useMemo(() => boundsOf(stones), [stones]);
  const all = useMemo(() => hexbin(stones, patternKey, widthKm), [stones, patternKey, widthKm]);
  const hexEarly = useMemo(() => hexbin(early, patternKey, widthKm), [early, patternKey, widthKm]);
  const hexLate = useMemo(() => hexbin(late, patternKey, widthKm), [late, patternKey, widthKm]);
  if (!split) return <HexMap hexes={all} minStones={minStones} label={label} bounds={bounds} />;
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 h-full">
      <div className="min-h-[50dvh] md:min-h-0"><HexMap hexes={hexEarly} minStones={minStones} label={label} bounds={bounds} title="Före ca 1050 (RAK–Pr2)" /></div>
      <div className="min-h-[50dvh] md:min-h-0"><HexMap hexes={hexLate} minStones={minStones} label={label} bounds={bounds} title="Efter ca 1050 (Pr3–Pr5)" /></div>
    </div>
  );
}
