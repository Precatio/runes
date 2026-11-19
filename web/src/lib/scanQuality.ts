// A simple quality class per scan (God, Godtagbar, Svag), from what the groove analysis already records:
// the scan's point spacing (mesh_point_spacing_mm, the median edge length), the share of holes inside the stone's
// outline on the analysis grid (hole_fraction, from 2026-11-19), and the surface noise (noise_mm), which is shown but
// not graded. The same rule as src/scan_quality.py (tests/test_scan_quality.py runs both); kept free of imports.
//
// Where the limits come from (set before any hole fraction was computed, not fitted to the test of 2026-11-19):
// - Point spacing God ≤ 0.5 mm: the Vitki protocol's existing recommendation (src/protocol.MAX_MESH_SPACING_MM).
//   Godtagbar ≤ 1.0 mm: twice that. In the robustness study (METHODS 2e) a scan thinned to half its triangles (point
//   spacing about 1.4 times) moved the stone's V-angle a median 0.9°, a quarter of them (about twice) 2.8° (at most 9.1°).
// - Holes God ≤ 2 %, Godtagbar ≤ 10 %: round conventions, not calibrated. Every hole also takes the analysis' edge
//   zone around it out of the measurement, so holes cost more surface than their own area.
// - Noise (noise_mm) is not graded: it is the spread of the surface around the reference surface at the 20 mm scale
//   (1.4826 × MAD), so it measures the stone's own unevenness (grain, weathering) more than the scanner. Added scanner
//   noise of 0.15 mm (the test of 2026-11-19, D1) raised it by only about 0.05 mm, while it differs between scans from
//   0.07 to 0.83 mm. It still sets the analysis' depth threshold (3 × noise), so it is shown beside the class.

export const SPACING_GOOD_MM = 0.5;
export const SPACING_OK_MM = 1.0;
export const HOLES_GOOD = 0.02;
export const HOLES_OK = 0.10;

export type ScanClass = "god" | "godtagbar" | "svag" | "okänd";

export interface ScanQualityPart {
  key: "punktavstånd" | "hål" | "brus";
  value: number | null;
  klass: ScanClass | null; // null: shown, not graded (noise)
  text: string;
}

export interface ScanQuality {
  klass: ScanClass;
  label: string;
  parts: ScanQualityPart[];
  text: string; // what the class is built on, in plain words
}

export const SCAN_CLASS_LABEL: Record<ScanClass, string> = {
  god: "God", godtagbar: "Godtagbar", svag: "Svag", "okänd": "Okänd",
};

const RANK: Record<ScanClass, number> = { god: 0, godtagbar: 1, svag: 2, "okänd": -1 };

const num = (v: unknown): number | null => (typeof v === "number" && Number.isFinite(v) ? v : null);
const dec = (v: number, d: number) => v.toFixed(d).replace(".", ",");

export function spacingClass(mm: number | null): ScanClass {
  if (mm === null) return "okänd";
  return mm <= SPACING_GOOD_MM ? "god" : mm <= SPACING_OK_MM ? "godtagbar" : "svag";
}

export function holesClass(share: number | null): ScanClass {
  if (share === null) return "okänd";
  return share <= HOLES_GOOD ? "god" : share <= HOLES_OK ? "godtagbar" : "svag";
}

/** The quality of the scan behind a measurement, from its parameters (or provenance.parameters). */
export function scanQuality(params: Record<string, unknown> | null | undefined): ScanQuality {
  const p = params ?? {};
  const spacing = num(p.mesh_point_spacing_mm);
  const holes = num(p.hole_fraction);
  const noise = num(p.noise_mm);
  const ks = spacingClass(spacing);
  const kh = holesClass(holes);
  const parts: ScanQualityPart[] = [
    { key: "punktavstånd", value: spacing, klass: ks,
      text: spacing === null ? "punktavståndet är inte känt"
        : `punktavstånd ${dec(spacing, 2)} mm (god högst ${dec(SPACING_GOOD_MM, 1)}, godtagbar högst ${dec(SPACING_OK_MM, 1)} mm)` },
    { key: "hål", value: holes, klass: kh,
      text: holes === null ? "andelen hål är inte uppmätt (äldre analys)"
        : `hål ${dec(100 * holes, 1)} % av stenytan (god högst ${HOLES_GOOD * 100} %, godtagbar högst ${HOLES_OK * 100} %)` },
    { key: "brus", value: noise, klass: null,
      text: noise === null ? "ytans brus är inte känt"
        : `ytans brus ${dec(noise, 2)} mm (betygsätts inte: det speglar mest stenens egen ojämnhet; spårtröskeln blir 3 × bruset)` },
  ];
  const known = [ks, kh].filter(k => k !== "okänd");
  const klass: ScanClass = ks === "okänd" ? "okänd" : known.reduce((a, b) => (RANK[b] > RANK[a] ? b : a), "god" as ScanClass);
  const text = klass === "okänd"
    ? "Skanningens kvalitet kan inte bedömas: punktavståndet saknas."
    : `${SCAN_CLASS_LABEL[klass]}: den sämsta av delarna punktavstånd och hål`
      + (kh === "okänd" ? " (här bara punktavståndet, hålen är inte uppmätta)" : "") + ". "
      + parts.map(x => x.text).join("; ") + ".";
  return { klass, label: SCAN_CLASS_LABEL[klass], parts, text };
}

/** Tailwind classes for the class badge (no violet; rust is the app's accent). */
export const SCAN_CLASS_STYLE: Record<ScanClass, string> = {
  god: "bg-emerald-100 text-emerald-800",
  godtagbar: "bg-amber-100 text-amber-900",
  svag: "bg-orange-100 text-[#9a350b]",
  "okänd": "bg-slate-100 text-slate-500",
};
