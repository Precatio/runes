// Input for the stone report (POST /api/reports/stone): one stone, its groove analyses with raw profiles
// and slice positions, and – if the model is still in the analysis engine's memory – its mesh id, so that
// the report can include surface figures computed from the scan.
import type { AnalysisProvenance, PaleographicCrop, ProjectData, ThreeDAnalysisResult, TwoDResultData } from "@/lib/db";
import type { AutoAnalysisResult, AutoLabel } from "@/lib/mesh";
import { METRICS, type FeatureType, type Metric, type SliceMetrics } from "@/lib/metrics";
import type { SynthesisResult } from "@/lib/synthesis";

export interface StoneReportAnalysis {
  feature_type: FeatureType;
  slices: SliceMetrics[];
  provenance?: AnalysisProvenance;
}

export interface StoneReportInput {
  source: string; // shown to the user: where the data comes from
  signum: string;
  meta: Record<string, string>;
  meshId?: string;
  view?: { normal: number[]; up?: number[] };
  analyses: StoneReportAnalysis[];
  counts?: AutoAnalysisResult["counts"];
  twoD?: { image?: string; result?: TwoDResultData | null; crops?: { tag: string; formPng?: string }[]; caption?: string };
  synthesis?: SynthesisResult; // attribution section of the report
}

type Meta = { stone: string; weathering: string; text: string; ornamentation: string; period: string; carver: string; location: string };

const metaRecord = (m: Meta): Record<string, string> => ({
  stone: m.stone, weathering: m.weathering, text: m.text, ornamentation: m.ornamentation,
  period: m.period, carver: m.carver, location: m.location,
});

const cropsOf = (crops?: PaleographicCrop[]) =>
  (crops ?? []).map(c => ({ tag: c.tag, formPng: c.formPng ?? c.imageBase64 }));

// From the current 3D session: the reviewed automatic analysis (runes and ornament separately), or else the
// latest manual analysis
export function fromSession(args: {
  meta: Meta;
  meshId?: string;
  autoResult: AutoAnalysisResult | null;
  autoLabels: AutoLabel[];
  results: ThreeDAnalysisResult | null;
  featureType: FeatureType;
  project?: ProjectData | null;
}): StoneReportInput | null {
  const { meta, meshId, autoResult, autoLabels, results, featureType, project } = args;
  let analyses: StoneReportAnalysis[] = [];
  let view: StoneReportInput["view"];
  if (autoResult && autoResult.counts.accepted > 0) {
    const groups: Partial<Record<FeatureType, SliceMetrics[]>> = {};
    autoResult.slices.forEach((s, i) => {
      const label = autoLabels[i] ?? "unknown";
      if (!s.accepted || label === "excluded") return;
      (groups[label] ??= []).push({
        ...(Object.fromEntries(METRICS.map(m => [m, s[m] as number])) as Record<Metric, number>),
        position_mm: s.position_mm, fit_r2: s.fit_r2, profile: s.profile, point: s.point, direction: s.direction, up: s.up,
      });
    });
    analyses = (Object.entries(groups) as [FeatureType, SliceMetrics[]][])
      .map(([feature_type, slices]) => ({ feature_type, slices, provenance: { ...autoResult.provenance, feature_type } }));
    const p = autoResult.parameters as Record<string, number[]>;
    if (Array.isArray(p.normal)) view = { normal: p.normal, up: Array.isArray(p.up) ? p.up : undefined };
  } else if (results?.slices?.length) {
    analyses = [{ feature_type: featureType, slices: results.slices, provenance: results.provenance }];
  }
  if (!analyses.length) return null;
  return {
    source: autoResult ? "Aktuell automatisk 3D-analys" : "Aktuell 3D-analys",
    signum: meta.text,
    meta: metaRecord(meta),
    meshId,
    view,
    analyses,
    counts: autoResult?.counts,
    twoD: project ? { image: project.twoDImage, result: project.twoDResults, crops: cropsOf(project.paleographicCrops) } : undefined,
    synthesis: project?.synthesis?.result,
  };
}

// From a saved project: all saved groove analyses. The surface figures need the scan in the engine's
// memory; the mesh is found by its checksum.
export function fromProject(project: ProjectData): StoneReportInput | null {
  const analyses = (project.grooveAnalyses ?? []).map(a => ({
    feature_type: a.feature_type, slices: a.slices, provenance: a.provenance,
  }));
  if (!analyses.length) return null;
  const latest = project.grooveAnalyses!.at(-1)!;
  const p = latest.provenance?.parameters as Record<string, unknown> | undefined;
  return {
    source: `Sparat projekt: ${project.name}`,
    signum: project.metaText,
    meta: {
      stone: project.metaStone, weathering: project.metaWeathering, text: project.metaText,
      ornamentation: project.metaOrnamentation ?? "", period: project.metaPeriod ?? "",
      carver: project.attributedCarver ?? "", location: project.location ?? "",
    },
    meshId: latest.provenance?.mesh?.sha256,
    view: Array.isArray(p?.normal) ? { normal: p!.normal as number[], up: Array.isArray(p?.up) ? p!.up as number[] : undefined } : undefined,
    analyses,
    twoD: { image: project.twoDImage, result: project.twoDResults, crops: cropsOf(project.paleographicCrops) },
    synthesis: project.synthesis?.result,
  };
}

export const hasProfiles = (input: StoneReportInput) => input.analyses.some(a => a.slices.some(s => s.profile));
export const hasPositions = (input: StoneReportInput) => input.analyses.some(a => a.slices.some(s => s.point));
