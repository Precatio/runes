// Shared research corpus of groove measurements (Firestore collection "corpus").
// Readable by all signed-in users; each entry can only be changed by its contributor.
import { collection, deleteDoc, doc, getDocs, orderBy, query, setDoc } from "firebase/firestore";
import { auth, db as firestore } from "@/firebase/config";
import { METRICS, type FeatureType, type Metric, type SliceMetrics, type Summary } from "@/lib/metrics";
import type { AnalysisProvenance } from "@/lib/db";

export const CORPUS_LICENSE = "CC-BY-4.0";

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
}

const COLLECTION = "corpus";

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

export const corpus = {
  list: async (): Promise<CorpusEntry[]> => {
    if (!auth.currentUser) return [];
    const snap = await getDocs(query(collection(firestore, COLLECTION), orderBy("createdAt", "desc")));
    return snap.docs.map(d => d.data() as CorpusEntry);
  },

  add: async (
    entry: Omit<CorpusEntry, "id" | "contributorUid" | "createdAt" | "license" | "profile"> & {
      profile?: { x: number[]; z: number[] } | null;
    },
  ): Promise<CorpusEntry> => {
    const user = auth.currentUser;
    if (!user) throw new Error("Du måste vara inloggad för att bidra till korpusen.");
    for (const m of METRICS) {
      if (!Number.isFinite(entry.means[m])) throw new Error(`Mätvärdet ${m} saknas.`);
    }
    const id = `c_${crypto.randomUUID()}`;
    const full: CorpusEntry = {
      ...entry,
      id,
      contributorUid: user.uid,
      createdAt: new Date().toISOString(),
      license: CORPUS_LICENSE,
      profile: entry.profile ? downsample(entry.profile.x, entry.profile.z) : undefined,
    };
    // Firestore rejects undefined values
    await setDoc(doc(firestore, COLLECTION, id), JSON.parse(JSON.stringify(full)));
    return full;
  },

  remove: async (id: string) => {
    await deleteDoc(doc(firestore, COLLECTION, id));
  },
};

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
    contributor: e.contributorName,
    institution: e.institution,
    license: e.license,
    created: e.createdAt,
  }));
}
