// The map's layer of realms: approximate borders of the Nordic peoples and kingdoms at three times
// (definitions and sources in realms.json; geometry built by scripts/build_realms.R into public/geo/riken.geojson).
// Without Leaflet, so that the explanation can be rendered on the server.
import defs from "./realms.json";
import land from "./historiska_land.json";
import stader from "./vikingastader.json";

export type Certainty = "karna" | "los" | "omstridd";
export interface RealmRegion { id: string; name: string; realm: string; certainty: Certainty; label: string; blocks?: string[]; harad?: string[]; note: string }
export interface RealmEpoch { key: string; label: string; title: string; text: string; regions: RealmRegion[]; sources?: string[]; url?: string }

export const REALMS: Record<string, { label: string; color: string }> = { ...defs.realms, ...land.realms };
export const CERTAINTY: Record<Certainty, string> = defs.certainty;
export const LAND_URL = "/geo/land.geojson";
// Smålands små land och Upplands folkland (historiska_land.json, built by scripts/build_historiska_land.R)
export const EPOCHS = [...(defs.epochs as RealmEpoch[]), { ...(land.epoch as RealmEpoch), url: LAND_URL }];
export const REALM_UNKNOWN = defs.unknown;
export const REALM_SOURCES = defs.sources;
export const REALMS_URL = "/geo/riken.geojson";

export const epochOf = (key: string | undefined) => EPOCHS.find(e => e.key === key);
export const urlOf = (key: string | undefined) => epochOf(key)?.url ?? REALMS_URL;

/** The line of a region: solid for a core area, dashed for a loose or uncertain one, dotted where realms contested it. */
export const DASH: Record<Certainty, string | undefined> = { karna: undefined, los: "7 5", omstridd: "2 5" };

// Viking Age trading places, central places and the first towns (vikingastader.json), shown with the border layer:
// at a time (890, 1025, 1200) the places that existed then; with the small lands, all of them
export interface Town { id: string; name: string; type: string; lat: number; lon: number; from: number; to: number | null; period: string; note: string }
export const TOWNS = stader.places as Town[];
export const TOWN_TYPES: Record<string, { label: string; symbol: string }> = stader.types;
export const TOWN_SOURCES: string[] = stader.sources;
export const townsAt = (key: string | undefined): Town[] => {
  if (!key) return [];
  const year = Number(key);
  return Number.isFinite(year) ? TOWNS.filter(t => t.from <= year && (t.to === null || t.to >= year)) : TOWNS;
};

// A town's mark: a dot for an early town, a ring for a trading place, a square for a central place (TOWN_TYPES)
export const townMark = (type: string, size = 9) => {
  const c = "#b7410e";
  if (type === "stad") return `<span style="display:inline-block;width:${size}px;height:${size}px;border-radius:50%;background:${c};border:1.5px solid #fff;box-shadow:0 0 0 1px ${c}"></span>`;
  if (type === "centralplats") return `<span style="display:inline-block;width:${size}px;height:${size}px;background:#fff;border:2px solid ${c}"></span>`;
  return `<span style="display:inline-block;width:${size}px;height:${size}px;border-radius:50%;background:#fff;border:2px solid ${c}"></span>`;
};
