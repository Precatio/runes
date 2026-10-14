// The map's layer of realms: approximate borders of the Nordic peoples and kingdoms at three times
// (definitions and sources in realms.json; geometry built by scripts/build_realms.R into public/geo/riken.geojson).
// Without Leaflet, so that the explanation can be rendered on the server.
import defs from "./realms.json";

export type Certainty = "karna" | "los" | "omstridd";
export interface RealmRegion { id: string; name: string; realm: string; certainty: Certainty; label: string; blocks: string[]; note: string }
export interface RealmEpoch { key: string; label: string; title: string; text: string; regions: RealmRegion[] }

export const REALMS: Record<string, { label: string; color: string }> = defs.realms;
export const CERTAINTY: Record<Certainty, string> = defs.certainty;
export const EPOCHS = defs.epochs as RealmEpoch[];
export const REALM_UNKNOWN = defs.unknown;
export const REALM_SOURCES = defs.sources;
export const REALMS_URL = "/geo/riken.geojson";

export const epochOf = (key: string | undefined) => EPOCHS.find(e => e.key === key);

/** The line of a region: solid for a core area, dashed for a loose or uncertain one, dotted where realms contested it. */
export const DASH: Record<Certainty, string | undefined> = { karna: undefined, los: "7 5", omstridd: "2 5" };
