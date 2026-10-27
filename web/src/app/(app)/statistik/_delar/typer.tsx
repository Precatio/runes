import { type Level } from "@/components/Explain";
import { type Pattern } from "@/components/PatternCard";

export interface Status {
  r: { available: boolean; version: string | null; missing: string[]; note: string | null };
  corpus?: {
    fingerprint: string; n_stones: number; ready: boolean; computed_at: string | null; running: boolean;
    module: string | null; done_modules: string[]; error: string | null; errors: Record<string, string> | null;
    modules: { key: string; label: string }[];
  };
}

type Dict = Record<string, unknown>;
interface ChangeFeature {
  key: string; label: string; group: string; n: number; share: number;
  time: {
    tested: boolean; n: number; n_yes: number; p?: number; q?: number | null; shape?: string; peak_year?: number | null;
    year_first?: number; year_last?: number; first?: number; last?: number; change_lo?: number; change_hi?: number;
    draws?: { n: number; share_sig: number | null; share_same_shape: number | null };
    curve?: { year: number; share: number }[];
  };
  provinces: { p_differ: number; q_differ?: number; p_differ_nocarver?: number; rows: { province: string; n: number; share1050: number; lo1050: number; hi1050: number; cross_year: number | null; cross_lo: number | null; cross_hi: number | null }[] } | null;
  space: { n: number; p: number; high: string[] | string; low: string[] | string } | null;
}
interface AnonGroup {
  id: number; name?: string | null; status: "candidate" | "known"; type_stone: string; n: number; spread_km: number;
  stones: string[]; parishes: string[] | string; styles: { style: string; n: number }[] | null; stability: number;
  robust_no_time?: number; robust?: boolean; known_carvers_near?: number; attributed_share_area?: number;
  marks: { feature: string; share_group: number; share_area: number }[] | null;
  nearest_carver: { carver: string; n: number; dist: number; km: number; as_close_as_same_carver: boolean } | null;
  model: { n: number; carver: string; share: number; mean_p: number } | null;
}
interface ChangeAssoc {
  key: string; label: string; n: number; n_x: number; share_x: number; share_other: number;
  all: { or: number; lo: number; hi: number; p: number; q: number | null } | null;
  dated: { n: number; or?: number; lo?: number; hi?: number; p?: number } | null;
}

interface RemainsTest {
  label: string; n: number; or: number; lo: number; hi: number; p: number; q_bh: number;
  halves?: { replicated: boolean }; periods?: { early: number; late: number; n_early: number; n_late: number };
}
interface CultTest extends RemainsTest { share_near: number; share_far: number; n_near: number; n_places?: number; loo?: { min_or: number; max_or: number } }
export interface CultResult {
  available: boolean; near_km: number; n_a: number; n_b: number; n_c?: number; stones_near_a: number; stones_near_b: number;
  near_a_stones: number; near_a_random: number; tests?: Record<string, CultTest>;
  radius?: { km: number; n_near: number; or: number; p: number }[];
  pagan?: { signum: string; km_a: number; km_b: number }[];
  churches?: { n_churches: number; n_other: number; near_church_other: number; near_km: number;
    rows: { tier: string; n: number; near_church: number; or: number; p: number }[]; age?: ChurchAge } | null;
}
export type AgeTerm = { or: number; lo: number; hi: number; p: number; halves?: { replicated: boolean } } | null;
export interface ChurchAge {
  early_year: number; n_early: number; n_late: number; near_km: number;
  tests: { feature: string; label: string; n: number; early: AgeTerm; late: AgeTerm; early_time: AgeTerm; late_time: AgeTerm;
    ratio: number; p_diff: number; share_early: number; n_early: number; share_late: number; n_late: number; share_none: number; n_none: number }[];
}
export interface VikingShore {
  n_stones: number; median_stones_km: number; median_random_km: number; p: number; error?: string;
  provinces?: { province: string; uplift_m: number; n: number; median_stones_km: number; median_random_km: number; p: number }[];
}

interface Finding {
  signum: string; place: string; method: string; verdict: string; ours: string; existing: string; score: number;
  assessment: string; suggested?: string; crosscheck?: { status: string; runor?: { text: string; url?: string | null } };
}
export interface Corpus {
  computed_at: string; r_version: string; errors: Record<string, string>;
  figure_urls: Record<string, Record<string, string>>;
  patterns: Pattern[]; findings: Finding[];
  findings_summary: { n: number; new: number; contradicts: number; crosschecked: number; already_known: number; still_new: number };
  html_map_url: string | null;
  geography: Dict & { carvers: { carver: string; n: number; median_km: number; random_median_km: number; compact_ratio: number; compact_q: number; provinces: string; hull_area_km2: number }[]; method: string;
    water: Dict & { note?: string; viking_shore?: VikingShore; provinces?: { province: string; median_stones_km: number; median_random_km: number }[] } };
  clusters: Dict & { k: number; best_silhouette: number; structure: string; n_stones: number; method: string; carvers: { ari: number };
    clusters: { cluster: number; n: number; stability: number; silhouette: number; features: { level: string; share_in_cluster: number; share_overall: number }[]; styles: { style: string; n: number }[]; provinces: { province: string; n: number }[] }[] };
  text: Dict & { method: string; lemmas: { lemma: string; n: number; cramers_v: number; q: number }[];
    formulas: { tests: { label: string; cramers_v: number; q: number }[] } };
  attribution: Dict & { method: string; caveat: string; n_train: number; carvers: string[]; majority_baseline: number; min_inscriptions?: number;
    ablation: { features: string; accuracy: number; top3: number; log_loss: number }[];
    grouped_cv?: Record<string, { level: string; n_groups: number; ablation: { features: string; accuracy: number | null; top3: number | null }[] }>;
    material?: { per_family: { family: string; n: number; accuracy: number; carvers: number }[]; n_without_family: number };
    calibration: { ece: number; reliability: { threshold: number; n: number; accuracy: number }[] };
    per_carver: { carver: string; n: number; recall: number; precision: number | null }[];
    n_predictions?: number; n_someone_else?: number;
    open_set?: { threshold: number; method: string;
      known: { n: number; flagged: number; accuracy_kept: number; accuracy_all: number };
      left_out: { n: number; flagged: number; per_carver: { carver: string; n: number; flagged: number }[] };
      small_carvers: { n: number; carvers: number; flagged: number; median_p: number; median_p_known: number;
        stones: { signum: string; carver: string; top: string; p: number; someone_else: boolean }[] } } };
  chronology: Dict & { method: string; region: string; validation: { rho: number; partial_rho: number; usable: boolean; mae_loo_years: number; mae_naive_years: number };
    corpus_dimensions: { dim: number; inertia_pct: number; rho_time: number; rho_lat: number; eta2_province: number; eta2_carver: number; positive: string[] | string; negative: string[] | string; unexplained: boolean; explained_by: string[] | string }[] };
  dialect: Dict & { method: string; caveat: string; mantel: { r: number; p: number }; n_districts: number;
    groups: { group: number; n: number; provinces: string }[]; group_forms: { group: number; forms: { lemma: string; form: string; share_in_group: number; share_all: number }[] }[] };
  network: Dict & { method: string; modularity: number; communities: { community: number; size: number; words: { word: string }[] }[];
    kinship: { relation: string; n: number; early: number; late: number; q_period: number; share_christian: number; share_other: number; q_christian: number }[] };
  change?: Dict & { method: string; n_dated: number; draws: number; features: ChangeFeature[]; assoc: ChangeAssoc[] };
  remains?: Dict & { available: boolean; note?: string; method?: string; near_km?: number; n_stones?: number;
    distances?: { key: string; label: string; n_remains: number; median_stones_km: number; median_random_km: number; near_stones: number; near_random: number; q_bh: number }[];
    tests?: Record<string, RemainsTest>;
    gravfalt_provinces?: { province: string; n: number; near_stones: number; near_random: number; p: number }[];
    cult?: CultResult };
  anonymous?: Dict & { method: string; n_unattributed: number; n_candidates: number;
    calibration: { link_km: number; lr_min: number; tpr: number; fpr: number; precision: number; max_spread_km: number };
    validation: { n_groups: number; n_stones: number; purity: number; purity_geography: number; share_pure: number;
      heldout?: { purity: number; purity_geography: number; difference: number; difference_ci: number[] | number; runs_above: number; runs: number; folds: number } | null };
    coverage?: { carvers_by_province: Record<string, number>; n_carvers: number; share_attributed: Record<string, number>;
      n_stones_province: Record<string, number>; candidate_provinces: string[] | string; carvers_in_candidate_provinces: number };
    n_robust?: number; robust_min?: number;
    groups: AnonGroup[] };
  words?: Dict & { method: string; n_stones: number; n_dated: number; n_words_tested: number;
    provinces_tested: string[] | string; n_region_tests: number; n_time_tests: number;
    region: { word: string; province: string; logodds: number; q: number; k_in: number; n_in: number;
      k_out: number; n_out: number; rate_in: number; rate_out: number; holds: boolean }[];
    time: { word: string; slope: number; q: number; shares: { epoch: string; k: number; n: number }[] }[];
    ca: { inertia: number[]; provinces: { code: string; x: number; y: number; n: number }[];
      words: { w: string; x: number; y: number; n: number }[] };
    neighbors: { a: string; b: string; dist: number }[] };
  messages?: Dict & { method: string; n_stones: number; n_legible: number; elements: MessageElement[];
    travel: { n: number; cells: { region: string; direction: string; n: number; k: number }[]; common: OddsRow | null;
      common_glm: OddsRow | null; mh: OddsRow; p_interaction: number | null;
      by_direction: (OddsRow & { direction: string; fisher_p: number })[] };
    home: { n: number; cells: { region: string; n: number; k: number }[]; model: OddsRow | null } };
  sections?: Section[];
  overview?: { paragraphs: string[]; next_steps: string[] };
}

export type Tab = "overview" | "question" | "geography" | "clusters" | "text" | "attribution" | "anonymous" | "chronology" | "change" | "network" | "words" | "messages";

export interface OddsRow { or: number; lo: number; hi: number | null; p: number }
export interface MessageElement {
  key: string; label: string; n: number; k: number; separation: boolean; n_dated?: number;
  by_region: { region: string; n: number; k: number; share: number | null }[];
  adjusted?: { region: string; share: number }[]; model?: OddsRow | null; model_dated?: OddsRow | null; fisher: OddsRow;
}

export interface Section {
  key: Tab; question: string; why: string; headline: { value: string; label: string }; answer: string; short: string;
  confidence: Level; confidence_text: string; interpretation: string[]; not_saying: string[];
}
