"use client";

import "leaflet/dist/leaflet.css";
import { useEffect } from "react";
import Link from "next/link";
import { CircleMarker, MapContainer, Popup, TileLayer, useMap } from "react-leaflet";

export interface MapPoint {
  signum: string;
  lat: number;
  lon: number;
  period: string | null;
  style: string | null;
  carvers: string;
  lost: boolean;
  measured?: boolean;
}

interface Props {
  points: MapPoint[];
  colorFor: (p: MapPoint) => string;
  selected?: string | null;
}

function FlyTo({ point }: { point: MapPoint | undefined }) {
  const map = useMap();
  useEffect(() => {
    if (point) map.flyTo([point.lat, point.lon], 11, { duration: 0.8 });
  }, [map, point]);
  return null;
}

export default function RuneMap({ points, colorFor, selected }: Props) {
  const selectedPoint = selected ? points.find(p => p.signum === selected) : undefined;
  return (
    <MapContainer center={[59.3, 16.5]} zoom={6} preferCanvas className="w-full h-full rounded-[28px]" scrollWheelZoom>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>-bidragsgivare'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <FlyTo point={selectedPoint} />
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
                {p.style && <div>Stilgrupp: {p.style}</div>}
                {p.carvers && <div>Ristare: {p.carvers}</div>}
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
