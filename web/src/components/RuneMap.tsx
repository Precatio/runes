"use client";

import "leaflet/dist/leaflet.css";
import { useEffect } from "react";
import { latLngBounds } from "leaflet";
import Link from "next/link";
import { CircleMarker, MapContainer, Popup, TileLayer, useMap } from "react-leaflet";
import RealmLayer from "@/components/RealmLayer";

export interface MapPoint {
  signum: string;
  lat: number;
  lon: number;
  period: string | null;
  style: string | null;
  carvers: string;
  lost: boolean;
  province: string;
  object: string;
  material: string;
  cross: boolean;
  carverStatus: string; // S, A, ? or empty
  categories: string[];
  runestone: boolean;
  measured?: boolean;
  note?: string; // e.g. the selected language trait's value
}

interface Props {
  points: MapPoint[];
  colorFor: (p: MapPoint) => string;
  selected?: string | null;
  // Changes when the filters change; the map then zooms to the visible points (not when empty)
  fitKey?: string;
  // The time whose realms are drawn under the stones (src/lib/realms.ts), or none
  realm?: string;
}

function FlyTo({ point }: { point: MapPoint | undefined }) {
  const map = useMap();
  useEffect(() => {
    if (point) map.flyTo([point.lat, point.lon], 11, { duration: 0.8 });
  }, [map, point]);
  return null;
}

function FitToPoints({ points, fitKey }: { points: MapPoint[]; fitKey?: string }) {
  const map = useMap();
  useEffect(() => {
    if (!fitKey || !points.length) return;
    map.flyToBounds(latLngBounds(points.map(p => [p.lat, p.lon] as [number, number])), { padding: [40, 40], maxZoom: 11, duration: 0.6 });
    // Only when the filters change, not on every render of the same points
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [map, fitKey, points.length]);
  return null;
}

export default function RuneMap({ points, colorFor, selected, fitKey, realm }: Props) {
  const selectedPoint = selected ? points.find(p => p.signum === selected) : undefined;
  return (
    <MapContainer center={[59.3, 16.5]} zoom={6} preferCanvas className="w-full h-full rounded-[28px]" scrollWheelZoom>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>-bidragsgivare'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {realm && <RealmLayer epoch={realm} />}
      <FlyTo point={selectedPoint} />
      {!selectedPoint && <FitToPoints points={points} fitKey={fitKey} />}
      {points.map(p => {
        const isSelected = p.signum === selected;
        return (
          <CircleMarker
            key={p.signum}
            center={[p.lat, p.lon]}
            radius={isSelected ? 9 : p.measured ? 6 : 4}
            pathOptions={{
              color: isSelected ? "#0f172a" : p.measured ? "#0f172a" : colorFor(p),
              weight: isSelected || p.measured ? 2 : 1,
              fillColor: colorFor(p),
              fillOpacity: p.lost ? 0.25 : 0.8,
              dashArray: p.lost ? "2 2" : undefined,
            }}
          >
            <Popup>
              <div className="text-sm space-y-0.5">
                <div className="font-bold">{p.signum}{p.lost && " (försvunnen)"}</div>
                {p.object && <div className="text-slate-600">{p.object}{p.material ? `, ${p.material}` : ""}{p.cross ? ", kors" : ""}</div>}
                {p.style && <div>Stilgrupp: {p.style}</div>}
                {p.carvers && <div>Ristare: {p.carvers}</div>}
                {p.note && <div>{p.note}</div>}
                {p.measured && <div>Uppmätt i korpusen</div>}
                <Link href={`/inskrifter?signum=${encodeURIComponent(p.signum)}`} className="text-[#b7410e] font-semibold">
                  Visa inskrift →
                </Link>
              </div>
            </Popup>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
