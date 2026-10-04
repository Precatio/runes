import { db as firestore, auth } from "@/firebase/config";
import { collection, doc, getDocs, getDoc, setDoc, deleteDoc } from "firebase/firestore";
import type { FeatureType, Metric, SliceMetrics, Summary } from "@/lib/metrics";

export interface SliceData {
  p1: [number, number, number];
  p2: [number, number, number];
  angle?: number;
  asymmetry?: number;
  depth?: number;
  width?: number;
  djup_bredd_kvot?: number;
  bottenradie?: number;
  ytrahet?: number;
  tool?: string;
}

export interface GrooveMetrics {
  apex_vinkel_deg: number;
  asymmetri_deg: number;
  spårdjup_mm: number;
  spårbredd_mm: number;
  djup_bredd_kvot: number;
  bottenradie_mm: number;
  ytråhet_mm: number;
  troligt_verktyg: string;
  apex_idx?: number;
  left_shoulder?: number;
  right_shoulder?: number;
}

export interface AnalysisProvenance {
  software: string;
  version: string;
  method_version: string;
  timestamp: string;
  feature_type: string;
  mesh: {
    mock: boolean;
    filename?: string;
    sha256?: string;
    vertices?: number;
    faces?: number;
    extent_mm?: number[];
    centered_by?: number[];
  };
  parameters: Record<string, unknown>;
}

export interface ToolHeuristic {
  label: string;
  threshold_deg: number;
  adjustments: string[];
  note: string;
}

export interface ThreeDAnalysisResult {
  results: GrooveMetrics;
  summary?: Record<Metric, Summary>;
  slices?: SliceMetrics[];
  provenance?: AnalysisProvenance;
  tool_heuristic?: ToolHeuristic;
  plot_data?: {
    x: number[];
    z: number[];
    fit_left?: { k: number; m: number };
    fit_right?: { k: number; m: number };
  } | null;
  depth_profile?: { distances: number[]; depths: number[] };
}

export interface GrooveSummaryLite {
  n: number;
  angle_mean: number;
  angle_sd: number;
  depth_mean: number;
  width_mean: number;
}

export interface PaleographicCrop {
  id: string;
  tag: string;
  imageBase64: string; // small thumbnail (≤ 256 px) – the project document has a 1 MB limit
  coordinates: number[]; // [xmin, ymin, xmax, ymax] as fractions of the image
  featureVector?: number[];
  featureVersion?: string; // vectors are only compared within the same version
  formPng?: string; // normalised black-and-white rune form used for the comparison
  sourceKind?: TwoDSourceKind;
  grooveSummary?: GrooveSummaryLite; // groove measurements inside the crop (groove map only)
  createdAt: string;
}

export type TwoDSourceKind = "upload" | "ksamsok" | "3d-snapshot" | "groove-map" | "rti";

export interface TwoDSource {
  kind: TwoDSourceKind;
  description?: string;
  url?: string;
  // Groove map only: accepted automatic slices with positions as fractions of the image
  autoSlices?: { x: number; y: number; metrics: Record<string, number> }[];
  methodVersion?: string;
}

export interface MarkerData {
  label: string;
  description: string;
  box_2d?: number[];
  polygon?: number[][];
}

export interface TwoDResultData {
  predicted_style: string;
  confidence: number;
  reasoning: string;
  rune_types: string;
  markers?: MarkerData[];
  model?: string;
  source?: TwoDSourceKind;
}

export interface LinguisticResultData {
  transliteration: string;
  normalization: string;
  phonetic_ipa: string;
  translation: string;
  linguistic_analysis: string;
  academic_reading?: string;
  comparison?: string;
  sound_laws_applied?: string[];
  markers?: MarkerData[];
}

// One saved groove analysis (all slices + provenance), kept per project for reproducibility
export interface GrooveAnalysisRecord {
  id: string;
  feature_type: FeatureType;
  summary: Record<Metric, Summary>;
  slices: SliceMetrics[];
  provenance: AnalysisProvenance;
  savedAt: string;
}

// A synthesis run, saved with the project so that it can be reopened and used in the stone report
export interface SavedSynthesis {
  result: import("@/lib/synthesis").SynthesisResult;
  analysisId: string | null;
  featureType: string;
  savedAt: string;
}

export interface ProjectData {
  id: string;
  name: string;
  fileName: string; // Original filename, to ask the user to load it again
  metaStone: string;
  metaWeathering: string;
  metaText: string;
  metaOrnamentation?: string;
  metaPeriod?: string;
  attributedCarver?: string;
  location?: string;
  plotImage?: string;
  threeImage?: string;
  slices: SliceData[];
  twoDResults?: TwoDResultData;
  twoDImage?: string;
  linguisticResults?: LinguisticResultData;
  paleographicCrops?: PaleographicCrop[];
  grooveAnalyses?: GrooveAnalysisRecord[];
  synthesis?: SavedSynthesis;
  createdAt: string;
  updatedAt: string;
}

export interface ReportData {
  id: string;
  title: string;
  htmlContent: string;
  createdAt: string;
  updatedAt: string;
}

const STORAGE_KEY = "vitki_projects";
const FIRESTORE_DOC_LIMIT = 900_000; // characters; Firestore's hard limit is 1 MB per document

// Raw slice profiles and positions are the heavy part of a project; drop them when a copy must be small
function withoutSliceDetail(project: ProjectData): ProjectData {
  return {
    ...project,
    grooveAnalyses: project.grooveAnalyses?.map(a => ({
      ...a,
      slices: a.slices.map(sl => {
        const { profile: _p, point: _pt, direction: _d, up: _u, ...rest } = sl;
        void _p; void _pt; void _d; void _u;
        return rest;
      }),
    })),
  };
}

// The local copy keeps images and raw profiles that Firestore cannot hold. Use it when it is the same
// version as the one in Firestore; a newer Firestore version (edited elsewhere) wins.
function preferRicher(remote: ProjectData, local?: ProjectData): ProjectData {
  if (local && local.updatedAt === remote.updatedAt) return { ...remote, ...local };
  return remote;
}
const REPORT_STORAGE_KEY = "vitki_reports";

// Dual-layer Database (Firestore + LocalStorage fallback)
export const db = {
  getProjects: async (): Promise<ProjectData[]> => {
    if (typeof window === "undefined") return [];
    const user = auth.currentUser;
    
    let firestoreProjects: ProjectData[] = [];
    if (user) {
      try {
        const querySnapshot = await getDocs(collection(firestore, `users/${user.uid}/projects`));
        firestoreProjects = querySnapshot.docs.map(doc => doc.data() as ProjectData);
      } catch (error) {
        console.error("Failed to fetch from Firestore:", error);
      }
    }
    
    const data = localStorage.getItem(STORAGE_KEY);
    const localProjects: ProjectData[] = data ? JSON.parse(data) : [];
    
    // Merge, preferring Firestore versions if IDs overlap (with the richer local copy of the same version)
    const merged = firestoreProjects.map(fp => preferRicher(fp, localProjects.find(lp => lp.id === fp.id)));
    for (const lp of localProjects) {
      if (!merged.find(p => p.id === lp.id)) {
        merged.push(lp);
      }
    }
    
    // Sort by updatedAt descending
    return merged.sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime());
  },
  
  getProject: async (id: string): Promise<ProjectData | null> => {
    const user = auth.currentUser;
    if (user) {
      try {
        const docRef = doc(firestore, `users/${user.uid}/projects`, id);
        const docSnap = await getDoc(docRef);
        if (docSnap.exists()) {
          const local: ProjectData[] = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
          return preferRicher(docSnap.data() as ProjectData, local.find(p => p.id === id));
        }
      } catch (error) {
        console.error("Failed to fetch project from Firestore:", error);
      }
    }
    
    // Fallback
    const data = localStorage.getItem(STORAGE_KEY);
    const projects: ProjectData[] = data ? JSON.parse(data) : [];
    return projects.find((p) => p.id === id) || null;
  },

  getProjectBySignum: async (signum: string): Promise<ProjectData | null> => {
    if (!signum || signum.trim() === "" || signum.toLowerCase() === "okänd") return null;
    const projects = await db.getProjects();
    return projects.find((p) => p.metaText && p.metaText.toLowerCase() === signum.toLowerCase()) || null;
  },
  
  // Accepts a partial update: an existing project (by id) is merged with the given fields.
  saveProject: async (project: Partial<ProjectData>): Promise<ProjectData> => {
    const now = new Date().toISOString();
    const isNew = !project.id;
    const projectId = project.id || "proj_" + Math.random().toString(36).substring(2, 9);
    
    const user = auth.currentUser;
    
    // Retrieve existing to merge if it exists
    let existingProject: ProjectData | null = null;
    if (!isNew) {
      existingProject = await db.getProject(projectId);
    }
    
    const savedProject: ProjectData = {
      ...(existingProject || {}),
      ...project,
      id: projectId,
      createdAt: existingProject?.createdAt || now,
      updatedAt: now,
    } as ProjectData;

    // Save to Firestore if logged in
    if (user) {
      try {
        const docRef = doc(firestore, `users/${user.uid}/projects`, projectId);
        // Strip heavy base64 images before saving to Firestore to avoid 1MB document limit
        let firestoreProject = { ...savedProject };
        delete firestoreProject.plotImage;
        delete firestoreProject.threeImage;
        delete firestoreProject.twoDImage;
        if (JSON.stringify(firestoreProject).length > FIRESTORE_DOC_LIMIT) {
          firestoreProject = withoutSliceDetail(firestoreProject);
        }
        
        await setDoc(docRef, firestoreProject);
      } catch (error) {
        console.error("Failed to save project to Firestore:", error);
      }
    }

    // Always keep a local copy as backup/cache
    const data = localStorage.getItem(STORAGE_KEY);
    const projects: ProjectData[] = data ? JSON.parse(data) : [];
    const index = projects.findIndex(p => p.id === projectId);
    
    if (index !== -1) {
      projects[index] = savedProject;
    } else {
      projects.push(savedProject);
    }
    
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(projects));
    } catch {
      // Browser storage full: keep the project, without raw profiles
      console.warn("Lokal lagring full – tvärsnittsprofilerna sparas inte lokalt för detta projekt.");
      projects[index !== -1 ? index : projects.length - 1] = withoutSliceDetail(savedProject);
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(projects));
      } catch (e) {
        console.error("Kunde inte spara projektet lokalt:", e);
      }
    }
    
    return savedProject;
  },
  
  deleteProject: async (id: string): Promise<void> => {
    const user = auth.currentUser;
    if (user) {
      try {
        const docRef = doc(firestore, `users/${user.uid}/projects`, id);
        await deleteDoc(docRef);
      } catch (error) {
        console.error("Failed to delete project from Firestore:", error);
      }
    }
    
    const data = localStorage.getItem(STORAGE_KEY);
    if (data) {
      const projects: ProjectData[] = JSON.parse(data);
      const filtered = projects.filter((p) => p.id !== id);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered));
    }
  },
  
  // Method to manually migrate local projects to cloud
  migrateLocalToCloud: async (): Promise<void> => {
    const user = auth.currentUser;
    if (!user) return;
    
    const data = localStorage.getItem(STORAGE_KEY);
    if (!data) return;
    
    const projects: ProjectData[] = JSON.parse(data);
    for (const project of projects) {
      try {
        const docRef = doc(firestore, `users/${user.uid}/projects`, project.id);
        await setDoc(docRef, project, { merge: true });
      } catch (error) {
        console.error("Migration error for project", project.id, error);
      }
    }
  },

  // --- REPORTS API ---

  getReports: async (): Promise<ReportData[]> => {
    if (typeof window === "undefined") return [];
    const user = auth.currentUser;
    
    let firestoreReports: ReportData[] = [];
    if (user) {
      try {
        const querySnapshot = await getDocs(collection(firestore, `users/${user.uid}/reports`));
        firestoreReports = querySnapshot.docs.map(doc => doc.data() as ReportData);
      } catch (error) {
        console.error("Failed to fetch reports from Firestore:", error);
      }
    }
    
    const data = localStorage.getItem(REPORT_STORAGE_KEY);
    const localReports: ReportData[] = data ? JSON.parse(data) : [];
    
    const merged = [...firestoreReports];
    for (const lr of localReports) {
      if (!merged.find(r => r.id === lr.id)) {
        merged.push(lr);
      }
    }
    
    return merged.sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime());
  },
  
  saveReport: async (report: Omit<ReportData, "id" | "createdAt" | "updatedAt"> & { id?: string; createdAt?: string }): Promise<ReportData> => {
    const now = new Date().toISOString();
    const isNew = !report.id;
    const reportId = report.id || "rep_" + Math.random().toString(36).substring(2, 9);
    
    const user = auth.currentUser;
    
    const savedReport: ReportData = {
      ...report,
      id: reportId,
      createdAt: isNew ? now : report.createdAt || now,
      updatedAt: now,
    };

    if (user) {
      try {
        const docRef = doc(firestore, `users/${user.uid}/reports`, reportId);
        await setDoc(docRef, savedReport);
      } catch (error) {
        console.error("Failed to save report to Firestore:", error);
      }
    }

    const data = localStorage.getItem(REPORT_STORAGE_KEY);
    const reports: ReportData[] = data ? JSON.parse(data) : [];
    const index = reports.findIndex(r => r.id === reportId);
    
    if (index !== -1) {
      reports[index] = savedReport;
    } else {
      reports.push(savedReport);
    }
    
    localStorage.setItem(REPORT_STORAGE_KEY, JSON.stringify(reports));
    
    return savedReport;
  },

  deleteReport: async (id: string): Promise<void> => {
    const user = auth.currentUser;
    if (user) {
      try {
        const docRef = doc(firestore, `users/${user.uid}/reports`, id);
        await deleteDoc(docRef);
      } catch (error) {
        console.error("Failed to delete report from Firestore:", error);
      }
    }
    
    const data = localStorage.getItem(REPORT_STORAGE_KEY);
    if (data) {
      const reports: ReportData[] = JSON.parse(data);
      const filtered = reports.filter((r) => r.id !== id);
      localStorage.setItem(REPORT_STORAGE_KEY, JSON.stringify(filtered));
    }
  }
};
