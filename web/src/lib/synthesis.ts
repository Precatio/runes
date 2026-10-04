// Types and request helper for the synthesis (POST /api/synthesis/analyze)
import { API_URL } from "@/lib/api";
import type { CorpusEntry } from "@/lib/corpus";
import type { GrooveAnalysisRecord, ProjectData } from "@/lib/db";
import { METRICS, type Metric, type Summary } from "@/lib/metrics";
import type { Geology, LanguageComparison } from "@/components/StoneContext";

export type LiteratureVerdict = "stämmer" | "stämmer delvis" | "nytt" | "motsäger" | "okänt" | "inget";

export interface Candidate {
  name: string;
  strength: "stark" | "måttlig" | "svag";
  score?: number;
  sources?: string[];
  first_in?: string[];
  evidence: { source: string; description: string; weight?: number }[];
  reasoning: string;
  literature?: { verdict: LiteratureVerdict; text: string };
  geography?: { in_area: boolean; nearest_km: number | null; provinces: Record<string, number>; plausible: boolean; text: string };
  styles?: { styles: Record<string, number>; span: [number, number] | null; fits: boolean | null; text: string };
  stone_tests?: { tests: { signum: string; n: number; p_value: number | null; compatible: boolean }[]; compatible: number; n: number; text: string };
  material?: { material: string; fits: boolean | null; text: string } | null;
  language?: (LanguageComparison & { fits: boolean | null }) | null;
  category?: { categories: string[]; fits: boolean | null; text: string } | null;
}

export interface OrthographyItem {
  carver: string; similarity: number; n_inscriptions: number; precision: number; in_area: boolean; reliability: number;
  significance?: { p_value: number; p_adjusted: number; n_null: number; own_percentile: number | null; n_carvers: number } | null;
}

export interface SynthesisResult {
  candidates: Candidate[];
  conflicts: string[];
  missing: string[];
  outcome?: { verdict: LiteratureVerdict; text: string; support?: string[] };
  analysis_used?: { id: string | null; feature_type: string; n: number; saved_at: string | null };
  geology_analysis: string;
  theory_analysis: string;
  dating_analysis: string;
  summary: string;
  sources: string[];
  ai_used: boolean;
  evidence?: {
    orthography?: { ranking: OrthographyItem[]; n_words: number; usable: boolean; source?: string;
      evaluation: { top1_accuracy: number; top3_accuracy: number; chance_top1: number; n_carvers: number; signed_top1: number | null } } | null;
    groove?: { ranking: { group: string; n: number; distance: number }[]; evaluation?: { top1_accuracy: number; chance_top1: number; n_stones: number; n_groups: number } | null;
      reference_size?: number; reliability?: number } | null;
    measurements_by_feature?: Record<string, { n: number; summary: Record<Metric, Summary> }> | null;
    style_check?: { ai_style: string; ai_confidence?: number; rundata_style: string | null; agrees: boolean; note: string };
    reading_check?: { char_agreement: number; word_agreement: number; coverage: number; summary: string };
    geology?: Omit<Geology, "signum" | "place"> | null;
    rundata?: { carver_raw: string; style: string | null; dating: string; material: string; place: string } | null;
  };
}

// Only the metrics travel to the server – raw profiles and positions are not needed here
const metricsOnly = (slices: GrooveAnalysisRecord["slices"]) =>
  slices.map(s => ({ ...Object.fromEntries(METRICS.map(m => [m, s[m]])), position_mm: s.position_mm }));

export async function runSynthesis(project: ProjectData, analysisId: string | null, geminiKey: string,
  corpusEntries: CorpusEntry[] | null): Promise<SynthesisResult> {
  const res = await fetch(`${API_URL}/api/synthesis/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Gemini-Api-Key": geminiKey },
    body: JSON.stringify({
      signum: project.metaText || "Okänt",
      stoneType: project.metaStone || "Okänd",
      weathering: project.metaWeathering || "Okänt",
      attributed_carver: project.attributedCarver || null,
      location: project.location || null,
      ornamentation: project.metaOrnamentation || null,
      period: project.metaPeriod || null,
      analyses: (project.grooveAnalyses ?? []).map(a => ({ id: a.id, feature_type: a.feature_type, savedAt: a.savedAt, slices: metricsOnly(a.slices) })),
      analysis_id: analysisId,
      // Fallback for projects saved before full analyses were kept
      slices: project.grooveAnalyses?.length ? [] : project.slices,
      corpus: (corpusEntries ?? []).map(e => ({ signum: e.signum, feature_type: e.feature_type, means: e.means, slices: metricsOnly(e.slices) })),
      corpus_note: corpusEntries === null ? "logga in för att jämföra med den delade mätkorpusen." : null,
      // The app's own reading (Språk & Fonetik) – used when Rundata has no usable text
      reading: project.linguisticResults?.transliteration ? {
        transliteration: project.linguisticResults.transliteration,
        normalization: project.linguisticResults.normalization,
      } : null,
      two_d: project.twoDResults ? {
        predicted_style: project.twoDResults.predicted_style,
        confidence: project.twoDResults.confidence,
        reasoning: project.twoDResults.reasoning,
      } : undefined,
    }),
  });
  if (!res.ok) throw new Error((await res.json().catch(() => null))?.detail || "Syntesen misslyckades.");
  return res.json();
}
