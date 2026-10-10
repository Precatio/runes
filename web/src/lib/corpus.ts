// Shared research corpus of groove measurements (Firestore collection "corpus").
// Readable by all signed-in users; each entry can only be changed by its contributor, while
// other researchers may add a verification.
//
// Layout:
//   corpus/{id}                     main entry (metrics per slice, summary, metadata) – small
//   corpus/{id}/raw/{n}             raw cross-section profiles in chunks, for recomputation
//   corpus/{id}/runeforms/{cropId}  rune forms from the 2D analysis
import {
  arrayUnion, collection, doc, getDocs, orderBy, query, updateDoc, writeBatch,
} from "firebase/firestore";
import { auth, db as firestore } from "@/firebase/config";
import { API_URL } from "@/lib/api";
import { METRICS, type FeatureType, type Metric, type SliceMetrics, type Summary } from "@/lib/metrics";
import type { AnalysisProvenance, GrooveSummaryLite, PaleographicCrop } from "@/lib/db";

export const CORPUS_LICENSE = "CC-BY-4.0";
export const CURRENT_METHOD = "groove-5";

export interface ScanMetadata {
  device?: string;
  resolution_mm?: number;
  accuracy_mm?: number;
  date?: string;
  scanned_by?: string;
  url?: string;     // where the scan is published (DOI or link)
  license?: string; // licence of the scan itself
}

export interface StoneCondition {
  weathering?: "låg" | "medel" | "hög";
  lichen?: boolean;
  paint?: boolean; // modern repainting
  notes?: string;
}

export interface Verification {
  uid: string;
  name: string;
  institution?: string;
  date: string;
  comment?: string;
}

export interface CorpusEntry {
  id: string;
  signum: string;
  label: string;
  feature_type: FeatureType;
  contributorUid: string;
  contributorName: string;
  institution: string;
  license: typeof CORPUS_LICENSE;
  createdAt: string;
  method_version: string;
  means: Record<Metric, number>;
  summary: Record<Metric, Summary>;
  slices: SliceMetrics[];
  // Downsampled main profile, for overlay plots
  profile?: { x: number[]; z: number[] };
  provenance: AnalysisProvenance;
  scanner?: string;
  notes?: string;
  scan?: ScanMetadata;
  condition?: StoneCondition;
  raw_profile_chunks?: number;
  rune_forms?: number;
  rune_groups?: { tag: string; groove: GrooveSummaryLite }[];
  verifications?: Verification[];
  recomputedAt?: string;
}

export interface RuneForm {
  id: string;
  tag: string;
  featureVector: number[];
  featureVersion: string;
  formPng?: string;
  grooveSummary?: GrooveSummaryLite;
}

type RawProfile = { x: number[]; z: number[] } | null;

export interface RecomputeResult {
  method_version: string;
  slices: (Record<Metric, number> | null)[];
  failed: number;
  summary: Record<Metric, Summary> | null;
}

const COLLECTION = "corpus";
const CHUNK_CHARS = 700_000; // well below Firestore's 1 MB document limit

function downsample(xs: number[], zs: number[], max = 200) {
  if (xs.length <= max) return { x: xs, z: zs };
  const step = xs.length / max;
  const x: number[] = [];
  const z: number[] = [];
  for (let i = 0; i < max; i++) {
    const k = Math.floor(i * step);
    x.push(xs[k]);
    z.push(zs[k]);
  }
  return { x, z };
}

function chunkProfiles(profiles: RawProfile[]): RawProfile[][] {
  const chunks: RawProfile[][] = [];
  let current: RawProfile[] = [];
  let size = 0;
  for (const p of profiles) {
    const s = JSON.stringify(p).length;
    if (current.length && size + s > CHUNK_CHARS) {
      chunks.push(current);
      current = [];
      size = 0;
    }
    current.push(p);
    size += s;
  }
  if (current.length) chunks.push(current);
  return chunks;
}

const clean = <T,>(v: T): T => JSON.parse(JSON.stringify(v)); // Firestore rejects undefined

export type NewCorpusEntry = Omit<CorpusEntry, "id" | "contributorUid" | "createdAt" | "license" | "profile"
  | "raw_profile_chunks" | "rune_forms" | "verifications"> & { profile?: { x: number[]; z: number[] } | null };

export const corpus = {
  list: async (): Promise<CorpusEntry[]> => {
    if (!auth.currentUser) return [];
    const snap = await getDocs(query(collection(firestore, COLLECTION), orderBy("createdAt", "desc")));
    return snap.docs.map(d => d.data() as CorpusEntry);
  },

  add: async (
    entry: NewCorpusEntry,
    extras: { includeRaw: boolean; runeForms?: PaleographicCrop[] },
  ): Promise<CorpusEntry> => {
    const user = auth.currentUser;
    if (!user) throw new Error("Du måste vara inloggad för att bidra till korpusen.");
    for (const m of METRICS) {
      if (!Number.isFinite(entry.means[m])) throw new Error(`Mätvärdet ${m} saknas.`);
    }
    const id = `c_${crypto.randomUUID()}`;
    // Raw profiles go to a subcollection; the main document keeps the metrics only
    const rawProfiles: RawProfile[] = entry.slices.map(s => s.profile ?? null);
    const slices = entry.slices.map(s => {
      const { profile: _p, point: _pt, direction: _d, up: _u, ...rest } = s;
      void _p; void _pt; void _d; void _u;
      return rest as SliceMetrics;
    });
    const chunks = extras.includeRaw && rawProfiles.some(Boolean) ? chunkProfiles(rawProfiles) : [];
    const forms = (extras.runeForms ?? []).filter(c => c.featureVector && c.featureVersion);
    const groups = forms.filter(c => c.grooveSummary).map(c => ({ tag: c.tag, groove: c.grooveSummary! }));

    const full: CorpusEntry = {
      ...entry,
      slices,
      id,
      contributorUid: user.uid,
      createdAt: new Date().toISOString(),
      license: CORPUS_LICENSE,
      profile: entry.profile ? downsample(entry.profile.x, entry.profile.z) : undefined,
      raw_profile_chunks: chunks.length,
      rune_forms: forms.length,
      rune_groups: groups.length ? groups : undefined,
      verifications: [],
    };
    const batch = writeBatch(firestore);
    batch.set(doc(firestore, COLLECTION, id), clean(full));
    chunks.forEach((profiles, n) => batch.set(doc(firestore, COLLECTION, id, "raw", String(n)), clean({ index: n, profiles })));
    for (const f of forms) {
      const form: RuneForm = {
        id: f.id, tag: f.tag, featureVector: f.featureVector!, featureVersion: f.featureVersion!,
        formPng: f.formPng, grooveSummary: f.grooveSummary,
      };
      batch.set(doc(firestore, COLLECTION, id, "runeforms", f.id), clean(form));
    }
    await batch.commit();
    return full;
  },

  rawProfiles: async (entry: CorpusEntry): Promise<RawProfile[]> => {
    if (!entry.raw_profile_chunks) return [];
    const snap = await getDocs(collection(firestore, COLLECTION, entry.id, "raw"));
    return snap.docs
      .map(d => d.data() as { index: number; profiles: RawProfile[] })
      .sort((a, b) => a.index - b.index)
      .flatMap(d => d.profiles);
  },

  runeForms: async (entry: CorpusEntry): Promise<RuneForm[]> => {
    if (!entry.rune_forms) return [];
    const snap = await getDocs(collection(firestore, COLLECTION, entry.id, "runeforms"));
    return snap.docs.map(d => d.data() as RuneForm);
  },

  // Recompute the entry's slices from its raw profiles with the current measurement method
  recompute: async (entry: CorpusEntry): Promise<RecomputeResult> => {
    const profiles = await corpus.rawProfiles(entry);
    if (!profiles.length) throw new Error("Mätningen saknar råprofiler och kan inte räknas om.");
    const res = await fetch(`${API_URL}/api/stats/recompute`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ profiles: profiles.map(p => p ?? { x: [], z: [] }) }),
    });
    if (!res.ok) throw new Error((await res.json().catch(() => null))?.detail || "Omräkningen misslyckades.");
    return res.json();
  },

  // Owner: replace the stored metrics with recomputed ones (raw profiles stay unchanged)
  applyRecompute: async (entry: CorpusEntry, recomputed: RecomputeResult): Promise<void> => {
    if (!recomputed.summary) throw new Error("Inga snitt kunde räknas om.");
    const slices = entry.slices.map((s, i) => (recomputed.slices[i] ? { ...s, ...recomputed.slices[i]! } : s));
    const means = Object.fromEntries(METRICS.map(m => [m, recomputed.summary![m].mean])) as Record<Metric, number>;
    await updateDoc(doc(firestore, COLLECTION, entry.id), clean({
      slices, means, summary: recomputed.summary, method_version: recomputed.method_version,
      recomputedAt: new Date().toISOString(),
    }));
  },

  verify: async (entry: CorpusEntry, v: Omit<Verification, "uid" | "date">) => {
    const user = auth.currentUser;
    if (!user) throw new Error("Logga in för att verifiera.");
    if (user.uid === entry.contributorUid) throw new Error("Du kan inte verifiera din egen mätning.");
    const verification: Verification = { ...v, uid: user.uid, date: new Date().toISOString() };
    await updateDoc(doc(firestore, COLLECTION, entry.id), { verifications: arrayUnion(clean(verification)) });
    return verification;
  },

  remove: async (entry: CorpusEntry) => {
    const batch = writeBatch(firestore);
    for (const sub of ["raw", "runeforms"]) {
      const snap = await getDocs(collection(firestore, COLLECTION, entry.id, sub));
      snap.docs.forEach(d => batch.delete(d.ref));
    }
    batch.delete(doc(firestore, COLLECTION, entry.id));
    await batch.commit();
  },
};

// Simple quality indicators shown in the corpus
export function quality(e: CorpusEntry) {
  return {
    raw: (e.raw_profile_chunks ?? 0) > 0,
    scan: !!(e.scan?.device && (e.scan?.resolution_mm || e.scan?.accuracy_mm)),
    enoughSlices: e.slices.length >= 5,
    currentMethod: e.method_version === CURRENT_METHOD,
    verified: (e.verifications?.length ?? 0) > 0,
  };
}

export function corpusToRows(entries: CorpusEntry[]) {
  return entries.map(e => ({
    id: e.id,
    signum: e.signum,
    label: e.label,
    feature_type: e.feature_type,
    n_slices: e.slices.length,
    ...Object.fromEntries(METRICS.flatMap(m => [
      [`${m}_mean`, e.summary[m]?.mean],
      [`${m}_sd`, e.summary[m]?.sd],
    ])),
    method_version: e.method_version,
    mesh_sha256: e.provenance?.mesh?.sha256,
    scan_device: e.scan?.device,
    scan_resolution_mm: e.scan?.resolution_mm,
    scan_accuracy_mm: e.scan?.accuracy_mm,
    scan_url: e.scan?.url,
    weathering: e.condition?.weathering,
    lichen: e.condition?.lichen,
    repainted: e.condition?.paint,
    raw_profiles: (e.raw_profile_chunks ?? 0) > 0,
    verifications: e.verifications?.length ?? 0,
    contributor: e.contributorName,
    institution: e.institution,
    license: e.license,
    created: e.createdAt,
  }));
}

// Dataset package for archiving (e.g. a Zenodo deposit): metadata, licence, citation and all entries
export async function datasetPackage(entries: CorpusEntry[], includeRaw: boolean) {
  const resources = [];
  for (const e of entries) {
    resources.push({ ...e, raw_profiles: includeRaw ? await corpus.rawProfiles(e) : undefined });
  }
  return {
    name: "runforskning-matkorpus",
    title: "Vitki – mätkorpus för huggspår på runstenar",
    created: new Date().toISOString(),
    license: { name: CORPUS_LICENSE, path: "https://creativecommons.org/licenses/by/4.0/" },
    citation: "Bidragsgivarna enligt varje post; Vitki, https://github.com/Precatio/runes",
    method: "Se METHODS.md i programvarans repo; metodversion anges per post.",
    contributors: [...new Set(entries.map(e => `${e.contributorName}${e.institution ? `, ${e.institution}` : ""}`))],
    count: entries.length,
    entries: resources,
  };
}
