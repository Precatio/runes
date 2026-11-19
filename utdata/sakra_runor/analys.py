"""Proven i den låsta planen analysplaner/2026-11-19-sakra-runor-skanningskvalitet.md (sha256 fb4a444a…) och
tilläggsplan 1 (analysplaner/2026-11-19-sakra-runor-tillagg-1-annan-kalla.md, sha256 e7dd8b3d…), ur mätningarna som
kor.py skrev i matningar/ (Kitzler Åhfeldt, Södermanland) och matningar_zedig/ (Zedig, Medelpad och Hälsingland).

Stenmåtten per mätning (V-vinkel, spårdjup, spårbredd):
  H, hela slingan: medelvärdet över alla godkända snitt.
  S, säkra runor: runor med minst 4 godkända snitt; de 15 med flest snitt (vid lika: ordningen längs slingan, som är
     runnumrets ordning i groove-7, src/staveless.group_runes); medelvärdet av runornas medianer; under 8 säkra runor
     inget S-mått.
R1 (och R1z för Zedig): ICC(2,1), absolut överensstämmelse mellan D0 och D1/D2/D3, för H och S; teststorheten är
medelvärdet av ICC(S) − ICC(H) över 3 mått × 3 försämringar; 95 %-intervall ur 2 000 omdragningar av stenar (för Zedig
sten för sten, signum). R2 (bara Kitzler Åhfeldt): avstånd mellan stenar med samma ristare minus olika ristare, bara
par på samma bergart, p ur 10 000 omblandningar av ristarna inom bergarten.
    .venv/bin/python utdata/sakra_runor/analys.py   → resultat.json, resultat.md"""
from __future__ import annotations

import glob
import hashlib
import itertools
import json
import os
import statistics
import sys
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)

PLAN = os.path.join(ROOT, "analysplaner", "2026-11-19-sakra-runor-skanningskvalitet.md")
SHA = hashlib.sha256(open(PLAN, "rb").read()).hexdigest()
assert SHA.startswith("fb4a444a"), SHA
SEED = int(SHA[:8], 16)
PLAN_Z = os.path.join(ROOT, "analysplaner", "2026-11-19-sakra-runor-tillagg-1-annan-kalla.md")
SHA_Z = hashlib.sha256(open(PLAN_Z, "rb").read()).hexdigest()
assert SHA_Z.startswith("e7dd8b3d"), SHA_Z
SEED_Z = int(SHA_Z[:8], 16)

METRICS = ("apex_vinkel_deg", "spårdjup_mm", "spårbredd_mm")
LABEL = {"apex_vinkel_deg": "V-vinkel (°)", "spårdjup_mm": "spårdjup (mm)", "spårbredd_mm": "spårbredd (mm)"}
VARIANTS = ("D0", "D1", "D2", "D3")
DEGRADED = ("D1", "D2", "D3")
MIN_SLICES, TOP_RUNES, MIN_RUNES = 4, 15, 8
BOOT, PERM = int(os.environ.get("BOOT", 2000)), int(os.environ.get("PERM", 10000))
REF = os.path.join(ROOT, "utdata", "Rak", "referenser_g7")
D0_TOL = {"apex_vinkel_deg": 0.5, "spårdjup_mm": 0.1, "spårbredd_mm": 0.1}


# ---- stone measures ---------------------------------------------------------------------------------------------
def safe_runes(slices: list[dict]) -> list[list[dict]]:
    """The safe runes: at least MIN_SLICES accepted cross-sections; the TOP_RUNES with the most, ties by the order
    along the band (rune number)."""
    by = defaultdict(list)
    for s in slices:
        if s.get("rune_id") is not None:
            by[int(s["rune_id"])].append(s)
    ok = [(rid, ss) for rid, ss in by.items() if len(ss) >= MIN_SLICES]
    ok.sort(key=lambda t: (-len(t[1]), t[0]))
    return [ss for _, ss in ok[:TOP_RUNES]], len(ok)


def measures(d: dict) -> dict:
    sl = d.get("slices") or []
    H = {m: float(np.mean([s[m] for s in sl])) for m in METRICS} if sl else None
    chosen, n_safe = safe_runes(sl)
    S = ({m: float(np.mean([np.median([s[m] for s in ss]) for ss in chosen])) for m in METRICS}
         if n_safe >= MIN_RUNES else None)
    icc = {m: ((d.get("rune_summary") or {}).get("metrics") or {}).get(m, {}).get("icc") for m in METRICS}
    return {"H": H, "S": S, "n_safe": n_safe, "n_slices": len(sl),
            "n_runes": (d.get("rune_summary") or {}).get("n_runes"), "rune_icc": icc,
            "bands": (d.get("bands") or {}).get("source")}


def load(folder: str, key: str) -> dict[str, dict]:
    """{unit: {variant: measures, 'signum': …}} for the units measured in all four variants."""
    out: dict[str, dict] = defaultdict(dict)
    for f in sorted(glob.glob(os.path.join(folder, "*_D?.json"))):
        d = json.load(open(f, encoding="utf-8"))
        unit = d.get(key) or d["signum"]
        out[unit][d["variant"]] = measures(d)
        out[unit]["signum"] = d["signum"]
        out[unit]["file"] = d["file"]
    return {u: v for u, v in out.items() if all(x in v for x in VARIANTS)}


# ---- R1 ---------------------------------------------------------------------------------------------------------
def icc21(a: np.ndarray, b: np.ndarray) -> float:
    """ICC(2,1), two-way random, absolute agreement, single measure (Shrout & Fleiss), for two ratings per unit."""
    x = np.c_[a, b]
    n, k = x.shape
    g = x.mean()
    ssr = k * ((x.mean(axis=1) - g) ** 2).sum()
    ssc = n * ((x.mean(axis=0) - g) ** 2).sum()
    sse = ((x - g) ** 2).sum() - ssr - ssc
    msr, msc, mse = ssr / (n - 1), ssc / (k - 1), sse / ((n - 1) * (k - 1))
    return float((msr - mse) / (msr + (k - 1) * mse + k * (msc - mse) / n))


def r1_table(data: dict, units: list[str]) -> dict:
    t = {}
    for m in METRICS:
        for D in DEGRADED:
            for X in ("H", "S"):
                a = np.array([data[u]["D0"][X][m] for u in units])
                b = np.array([data[u][D][X][m] for u in units])
                t[(m, D, X)] = icc21(a, b)
    return t


def r1_stat(t: dict) -> tuple[float, dict]:
    diffs = {(m, D): t[(m, D, "S")] - t[(m, D, "H")] for m in METRICS for D in DEGRADED}
    per_metric = {m: float(np.mean([diffs[(m, D)] for D in DEGRADED])) for m in METRICS}
    return float(np.mean(list(diffs.values()))), per_metric


def r1(data: dict, seed: int, cluster_key: str | None = None) -> dict:
    units = sorted(u for u in data if all(data[u][v]["H"] and data[u][v]["S"] for v in VARIANTS))
    t = r1_table(data, units)
    stat, per_metric = r1_stat(t)
    # resampling stones: for Zedig by signum (several files can belong to one stone), otherwise by unit
    groups = defaultdict(list)
    for u in units:
        groups[data[u]["signum"] if cluster_key else u].append(u)
    keys = sorted(groups)
    rng = np.random.default_rng(seed)
    boot = []
    for _ in range(BOOT):
        pick = [u for k in rng.choice(keys, len(keys), replace=True) for u in groups[k]]
        boot.append(r1_stat(r1_table(data, pick))[0])
    lo, hi = (float(v) for v in np.percentile(boot, [2.5, 97.5]))
    n_pos = sum(v > 0 for v in per_metric.values())
    n_neg = sum(v < 0 for v in per_metric.values())
    holds = lo > 0 and n_pos >= 2
    return {"units": units, "n_units": len(units), "n_stones": len(keys), "stat": stat, "ci95": [lo, hi],
            "per_metric": per_metric, "metrics_positive": n_pos, "metrics_negative": n_neg, "holds": holds,
            "icc": {f"{m}|{D}|{X}": v for (m, D, X), v in t.items()}, "boot": BOOT, "seed": seed}


# ---- R2 ---------------------------------------------------------------------------------------------------------
def r2(data: dict, seed: int) -> dict:
    from src import geology, rune_links
    from src.research_gaps import certain_carvers
    base = sorted(u for u in data if data[u]["D0"]["H"] and data[u]["D0"]["S"])
    info = {}
    for u in base:
        rec, _ = rune_links.rundata_record(data[u]["signum"])
        info[u] = {"carvers": set(certain_carvers(rec)) if rec else set(),
                   "rock": frozenset(geology.families((rec or {}).get("material") or "")),
                   "material": (rec or {}).get("material") or ""}
    count = defaultdict(int)
    for u in base:
        for c in info[u]["carvers"]:
            count[c] += 1
    stones = [u for u in base if any(count[c] >= 2 for c in info[u]["carvers"]) and info[u]["rock"]]
    dropped_no_rock = [u for u in base if any(count[c] >= 2 for c in info[u]["carvers"]) and not info[u]["rock"]]
    pairs = [(a, b) for a, b in itertools.combinations(stones, 2) if info[a]["rock"] == info[b]["rock"]]
    out = {"stones": stones, "carvers": {u: sorted(info[u]["carvers"]) for u in stones},
           "rock": {u: sorted(info[u]["rock"]) for u in stones}, "dropped_no_rock": dropped_no_rock,
           "n_pairs": len(pairs), "perm": PERM, "seed": seed}
    strata = defaultdict(list)
    for u in stones:
        strata[info[u]["rock"]].append(u)

    def delta(lab: dict, D: np.ndarray, index: dict) -> tuple[float, int, int]:
        same, diff = [], []
        for a, b in pairs:
            (same if lab[a] & lab[b] else diff).append(D[index[a], index[b]])
        if not same or not diff:
            return float("nan"), len(same), len(diff)
        return float(np.mean(same) - np.mean(diff)), len(same), len(diff)

    for X in ("S", "H"):
        # the three measures z-scaled over the stones in the original (all stones with both measures)
        Z = np.array([[data[u]["D0"][X][m] for m in METRICS] for u in base])
        Z = (Z - Z.mean(axis=0)) / Z.std(axis=0, ddof=1)
        index = {u: i for i, u in enumerate(base)}
        D = np.sqrt(((Z[:, None, :] - Z[None, :, :]) ** 2).sum(axis=2))
        lab = {u: info[u]["carvers"] for u in stones}
        obs, n_same, n_diff = delta(lab, D, index)
        rng = np.random.default_rng(seed)
        le = 0
        valid = 0
        vals = []
        for _ in range(PERM):
            perm = dict(lab)
            for us in strata.values():
                shuffled = rng.permutation(len(us))
                for u, j in zip(us, shuffled):
                    perm[u] = lab[us[j]]
            v = delta(perm, D, index)[0]
            if np.isfinite(v):
                valid += 1
                le += v <= obs
                vals.append(v)
        p = (1 + le) / (1 + valid) if np.isfinite(obs) else float("nan")
        # the smallest p the permutation can give: the share of assignments as extreme as the most extreme one
        vmin = min(vals) if vals else float("nan")
        smallest = (1 + sum(v <= vmin + 1e-12 for v in vals)) / (1 + valid) if vals else float("nan")
        out[X] = {"delta": obs, "n_same": n_same, "n_diff": n_diff, "p": p, "smallest_p": smallest,
                  "n_distinct": len({round(v, 9) for v in vals})}
    s, h = out["S"]["delta"], out["H"]["delta"]
    out["holds_for_S"] = bool(np.isfinite(s) and s < 0 and out["S"]["p"] < 0.05)
    out["holds_for_H"] = bool(np.isfinite(h) and h < 0 and out["H"]["p"] < 0.05)
    # H separates more than S (a larger gap between same and different carvers): S separates worse
    out["S_worse"] = bool(np.isfinite(s) and np.isfinite(h) and h < s)
    return out


# ---- descriptive ------------------------------------------------------------------------------------------------
def descriptive(data: dict) -> dict:
    units = sorted(data)
    n_safe = {u: data[u]["D0"]["n_safe"] for u in units}
    with_s = [u for u in units if data[u]["D0"]["S"]]
    sb = {}
    for m in METRICS:
        iccs = [data[u]["D0"]["rune_icc"][m] for u in units if data[u]["D0"]["rune_icc"][m] is not None]
        # a negative ICC (more spread within the runes than between them) counts as 0: no reliability to build on
        curve = [float(np.median([k * max(r, 0.0) / (1 + (k - 1) * max(r, 0.0)) for r in iccs])) for k in range(1, 31)]
        sb[m] = {"n_stones": len(iccs), "icc_median": float(np.median(iccs)) if iccs else None,
                 "icc_range": [float(min(iccs)), float(max(iccs))] if iccs else None, "curve_k1_30": curve}
    shift = {}
    for X in ("H", "S"):
        for D in DEGRADED:
            us = [u for u in units if data[u]["D0"][X] and data[u][D][X]]
            for m in METRICS:
                d = [data[u][D][X][m] - data[u]["D0"][X][m] for u in us]
                shift[f"{X}|{D}|{m}"] = {"n": len(us), "mean": float(np.mean(d)), "mean_abs": float(np.mean(np.abs(d)))}
    # the stone where H and S differ most: the sum over the three measures of |S − H| in units of H's spread
    both = [u for u in units if data[u]["D0"]["H"] and data[u]["D0"]["S"]]
    sd = {m: float(np.std([data[u]["D0"]["H"][m] for u in both], ddof=1)) for m in METRICS}
    score = {u: sum(abs(data[u]["D0"]["S"][m] - data[u]["D0"]["H"][m]) / sd[m] for m in METRICS) for u in both}
    top = max(score, key=score.get) if score else None
    return {"n_units": len(units), "n_safe": n_safe, "n_with_S": len(with_s), "without_S": sorted(set(units) - set(with_s)),
            "spearman_brown": sb, "shift": shift,
            "example": {"unit": top, "signum": data[top]["signum"], "score": score[top], "H": data[top]["D0"]["H"],
                        "S": data[top]["D0"]["S"], "n_safe": data[top]["D0"]["n_safe"],
                        "n_slices": data[top]["D0"]["n_slices"]} if top else None}


def d0_check(data: dict) -> dict:
    """D0 against the saved groove-7 measurement: within 0.5° and 0.1 mm. The saved measurements of 2026-11-03 used the
    band model for the files whose depth image lacked its origin (fixed 2026-11-08), so those are compared but marked."""
    rows = {}
    for u in sorted(data):
        ref = json.load(open(os.path.join(REF, u.replace(" ", "_") + ".json"), encoding="utf-8"))
        diff = {m: data[u]["D0"]["H"][m] - ref["summary"][m]["mean"] for m in METRICS}
        rows[u] = {"saved_bands": ref["parameters"].get("bands_source"), "bands": data[u]["D0"]["bands"],
                   "diff": diff, "within": all(abs(diff[m]) <= D0_TOL[m] for m in METRICS),
                   "n_saved": ref["counts"]["accepted"], "n_now": data[u]["D0"]["n_slices"]}
    same = [u for u, r in rows.items() if r["saved_bands"] == r["bands"]]
    return {"rows": rows, "same_bands": same, "same_bands_within": [u for u in same if rows[u]["within"]],
            "other_bands": [u for u in rows if u not in same]}


def drawn_carver_pairs(data: dict) -> dict:
    """Zedig: stones with a certain carver that has two or more stones in the material (described, not tested)."""
    from src import rune_links
    from src.research_gaps import certain_carvers
    by = defaultdict(set)
    for u in data:
        rec, _ = rune_links.rundata_record(data[u]["signum"])
        for c in (certain_carvers(rec) if rec else []):
            by[c].add(data[u]["signum"])
    return {c: sorted(s) for c, s in by.items() if len(s) >= 2}


# ---- report -----------------------------------------------------------------------------------------------------
def f(x, d=2):
    return "–" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x:.{d}f}".replace(".", ",")


def main():
    kz = load(os.path.join(HERE, "matningar"), "signum")
    zd = load(os.path.join(HERE, "matningar_zedig"), "stem")
    res = {"plan_sha256": SHA, "addendum_sha256": SHA_Z, "metrics": list(METRICS)}
    res["d0_check"] = d0_check(kz)
    res["R1"] = r1(kz, SEED)
    res["R2"] = r2(kz, SEED)
    res["descriptive"] = descriptive(kz)
    zres = {}
    if zd:
        zres["R1z"] = r1(zd, SEED_Z, cluster_key="signum")
        zres["descriptive"] = descriptive(zd)
        zres["carvers_with_several_stones"] = drawn_carver_pairs(zd)
        zres["units"] = {u: {"signum": zd[u]["signum"], "file": zd[u]["file"]} for u in sorted(zd)}
    res["zedig"] = zres
    r1h, r2s = res["R1"]["holds"], res["R2"]
    r1z = (zres.get("R1z") or {}).get("holds", False)
    res["decision"] = {
        "R1_holds": r1h, "R1z_holds": r1z, "R2_S_worse": r2s["S_worse"],
        "main_plan_rule": "S" if r1h and not r2s["S_worse"] else "H",
        "addendum_rule": "S" if r1h and r1z and not r2s["S_worse"] else "H"}
    json.dump(res, open(os.path.join(HERE, "resultat.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1,
              default=lambda o: sorted(o) if isinstance(o, (set, frozenset)) else str(o))
    open(os.path.join(HERE, "resultat.md"), "w", encoding="utf-8").write(report(res, kz, zd))
    print(json.dumps(res["decision"], ensure_ascii=False))


def report(res: dict, kz: dict, zd: dict) -> str:
    R1, R2, de, dc = res["R1"], res["R2"], res["descriptive"], res["d0_check"]
    L = ["# Säkra runor mot hela slingan, och hur måtten tål sämre skanningar – resultat", "",
         f"Låst plan: `analysplaner/2026-11-19-sakra-runor-skanningskvalitet.md` (sha256 `{SHA[:8]}…`). Tilläggsplan 1: "
         f"`analysplaner/2026-11-19-sakra-runor-tillagg-1-annan-kalla.md` (sha256 `{SHA_Z[:8]}…`). Räknat av "
         "`utdata/sakra_runor/analys.py` ur `matningar/` och `matningar_zedig/` (groove-7, `kor.py`).", "",
         "## Kontroll av kedjan (D0)", ""]
    same, ok = dc["same_bands"], dc["same_bands_within"]
    L.append(f"- Stenar där den sparade groove-7-mätningen använde samma slingor som i dag (ritade): {len(same)}; inom "
             f"0,5° och 0,1 mm: {len(ok)} av {len(same)}.")
    worst = max((abs(dc['rows'][u]['diff'][m]) for u in same for m in METRICS), default=float('nan'))
    L.append(f"- Största avvikelse bland dem: {f(worst, 4)} (grader eller mm).")
    L.append(f"- Stenar vars sparade mätning (2026-11-03) använde slingmodellen eftersom djupbildens origo saknades "
             f"(rättat 2026-11-08): {len(dc['other_bands'])}. De mäts nu med de ritade slingorna, som planen kräver, och "
             "jämförs därför inte med de sparade värdena; deras D0 är dagens mätning.")
    L += ["", "## R1 – tål S sämre skanningar bättre än H? (Kitzler Åhfeldt)", ""]
    L.append(f"- Stenar med H- och S-mått i alla fyra körningarna: {R1['n_units']}.")
    L.append(f"- Medelskillnad ICC(S) − ICC(H) över 3 mått × 3 försämringar: **{f(R1['stat'], 3)}**, 95 %-intervall "
             f"{f(R1['ci95'][0], 3)} till {f(R1['ci95'][1], 3)} ({BOOT} omdragningar av stenar).")
    L.append("- Per mått (medel över D1–D3): " + "; ".join(f"{LABEL[m]} {f(v, 3)}" for m, v in R1["per_metric"].items()) + ".")
    L.append(f"- **R1 {'håller' if R1['holds'] else 'håller inte'}** (villkor: intervallet över 0 och skillnaden positiv "
             f"för minst två av tre mått; positiv för {R1['metrics_positive']}).")
    L += ["", "ICC(2,1) mellan originalet och den försämrade skanningen:", ""]
    for m in METRICS:
        L.append(f"- {LABEL[m]}: " + "; ".join(f"{D} H {f(R1['icc'][f'{m}|{D}|H'], 3)}, S {f(R1['icc'][f'{m}|{D}|S'], 3)}"
                                               for D in DEGRADED))
    L += ["", "## R2 – skiljer S ristarna åt minst lika bra som H? (Kitzler Åhfeldt, originalet)", ""]
    L.append(f"- Stenar: {len(R2['stones'])} ({', '.join(R2['stones'])}); par på samma bergart: {R2['n_pairs']}"
             f" ({R2['S']['n_same']} med samma ristare, {R2['S']['n_diff']} med olika).")
    if R2["dropped_no_rock"]:
        L.append(f"- Utan bergart i Rundata och därför utanför: {', '.join(R2['dropped_no_rock'])}.")
    for X in ("S", "H"):
        L.append(f"- {X}: avstånd samma ristare minus olika ristare {f(R2[X]['delta'], 3)} (z-enheter), p = {f(R2[X]['p'], 4)} "
                 f"({PERM} omblandningar inom bergarten).")
    if not (np.isfinite(R2["S"]["delta"]) and np.isfinite(R2["H"]["delta"])):
        L.append("- **R2 kan inte räknas:** det finns inga par med både samma och olika ristare på samma bergart.")
    else:
        L.append(f"- **R2 {'håller' if R2['holds_for_S'] else 'håller inte'} för S.** "
                 + ("H skiljer ristarna mer än S, alltså skiljer S sämre." if R2["S_worse"] else "H skiljer inte ristarna mer än S."))
    L.append("- R2 är litet: få ristare har två eller fler stenar i materialet, och bara par på samma bergart räknas. "
             f"Omblandningen inom bergarten ger bara {R2['S']['n_distinct']} olika värden av teststorheten, så p kan inte "
             f"bli lägre än omkring {f(R2['S']['smallest_p'], 2)}"
             + (": provet kunde inte hålla med det här materialet." if R2['S']['smallest_p'] >= 0.05 else "."))
    if res["zedig"]:
        z = res["zedig"]["R1z"]
        L += ["", "## R1z – samma prov på Zedigs skanningar (tilläggsplan 1)", ""]
        L.append(f"- Filer med H- och S-mått i alla fyra körningarna: {z['n_units']}, från {z['n_stones']} stenar.")
        L.append(f"- Medelskillnad ICC(S) − ICC(H): **{f(z['stat'], 3)}**, 95 %-intervall {f(z['ci95'][0], 3)} till "
                 f"{f(z['ci95'][1], 3)} ({BOOT} omdragningar sten för sten).")
        L.append("- Per mått: " + "; ".join(f"{LABEL[m]} {f(v, 3)}" for m, v in z["per_metric"].items()) + ".")
        L.append(f"- **R1z {'håller' if z['holds'] else 'håller inte'}** (positiv för {z['metrics_positive']} av 3 mått).")
        for m in METRICS:
            L.append(f"- ICC {LABEL[m]}: " + "; ".join(f"{D} H {f(z['icc'][f'{m}|{D}|H'], 3)}, S {f(z['icc'][f'{m}|{D}|S'], 3)}"
                                                       for D in DEGRADED))
        cw = res["zedig"]["carvers_with_several_stones"]
        L.append("- R2 görs inte i tillägget. Ristare med flera stenar i Zedigs material: "
                 + ("; ".join(f"{c}: {', '.join(s)}" for c, s in cw.items()) if cw else "inga") + ".")
    dec = res["decision"]
    L += ["", "## Beslut", ""]
    L.append(f"- Huvudplanens regel: **{dec['main_plan_rule']}** (R1 {'håller' if dec['R1_holds'] else 'håller inte'}; "
             f"R2 {'visar' if dec['R2_S_worse'] else 'visar inte'} att S skiljer ristarna sämre).")
    L.append(f"- Tilläggets ändrade regel (R1 och R1z måste hålla): **{dec['addendum_rule']}**"
             + ("." if dec["addendum_rule"] == "S" else ". H behålls som appens förvalda stenmått, och S redovisas som ett alternativ med båda resultaten."))
    for name, dd in (("Kitzler Åhfeldt", de), ("Zedig", (res["zedig"] or {}).get("descriptive"))):
        if not dd:
            continue
        L += ["", f"## Beskrivande – {name}", ""]
        ns = list(dd["n_safe"].values())
        L.append(f"- Säkra runor per {'skanning' if name == 'Zedig' else 'sten'} (D0): median {f(float(statistics.median(ns)), 1)}, från {min(ns)} till {max(ns)}; S-mått för "
                 f"{dd['n_with_S']} av {dd['n_units']}" + (f" (utan: {', '.join(dd['without_S'])})" if dd["without_S"] else "") + ".")
        for m in METRICS:
            sb = dd["spearman_brown"][m]
            c = sb["curve_k1_30"]
            L.append(f"- Runornas ICC för {LABEL[m]}: median {f(sb['icc_median'])} ({sb['n_stones']} stenar, "
                     f"{f(sb['icc_range'][0])}–{f(sb['icc_range'][1])}); Spearman–Brown, median över stenarna: "
                     f"1 runa {f(c[0])}, 4 {f(c[3])}, 8 {f(c[7])}, 15 {f(c[14])}, 30 {f(c[29])}.")
        for X in ("H", "S"):
            L.append(f"- Förflyttning {X} (medel D − D0, inom parentes medel av beloppet): " + "; ".join(
                f"{D}: " + ", ".join(f"{LABEL[m].split(' (')[0]} {f(dd['shift'][f'{X}|{D}|{m}']['mean'])} "
                                     f"({f(dd['shift'][f'{X}|{D}|{m}']['mean_abs'])})" for m in METRICS) for D in DEGRADED) + ".")
        ex = dd["example"]
        if ex:
            L.append(f"- Störst skillnad mellan H och S: {ex['signum']} ({ex['n_slices']} snitt, {ex['n_safe']} säkra runor): "
                     + ", ".join(f"{LABEL[m]} H {f(ex['H'][m])} mot S {f(ex['S'][m])}" for m in METRICS) + ".")
    L += ["", "## Vad som inte sägs", "",
          "- Försämringarna efterliknar sämre skanningar men är inte riktiga skanningar med en annan skanner.",
          "- Ett S som tål försämringen bättre betyder inte att det mäter ristarens hand.",
          "- Två källor med olika stenar ger inget prov av samma sten i två skannrar; det kräver att någon sten skannas om.",
          "", "## Avvikelser", ""]
    L += [f"- {a}" for a in DEVIATIONS] if DEVIATIONS else ["- Inga."]
    return "\n".join(L) + "\n"


DEVIATIONS = [
    "Kontrollen av kedjan (D0): planen jämför med de sparade groove-7-värdena. För de stenar vars sparade mätning "
    "(2026-11-03) använde slingmodellen, eftersom djupbildens origo saknades (felet rättades 2026-11-08), mäts D0 nu med "
    "de ritade slingorna, som planen kräver (\"samma ritade slingor\"). De kan inte jämföras med de sparade värdena, så "
    "kontrollen gjordes på stenarna vars sparade mätning använde de ritade slingorna. Kedjan ändrades inte.",
    "Sö 371 ingår inte: slingorna är märkta \"överhoppad\", inte granskade, och planen tar med stenar med ritade slingor. "
    "Materialet blir 36 skanningar i stället för 37.",
    "R2: \"samma bergart\" tolkas som samma uppsättning bergartsfamiljer ur Rundatas material (src/geology.families; "
    "gråsten ger gnejs och granit), och omblandningen görs inom den. \"Samma ristare\" betyder att stenarna delar minst "
    "en säker ristare (signerad eller attribuerad, inte osäker). Stenarna i R2 och z-skalningen är de med både H- och "
    "S-mått i originalet, så att S och H prövas på samma stenar. p är ensidigt (mindre avstånd vid samma ristare).",
    "Beskrivande, Spearman–Brown: en sten med negativ ICC för runorna räknas med ICC 0 (formeln är inte definierad för "
    "alla k när ICC är negativ). Det gäller bara den beskrivande kurvan, inget prov.",
    "Tilläggsplan 1: bruset i D1 och D3 har fröet ur tilläggets kontrollsumma (planen nämner tilläggets frö för "
    "omdragningen). D0 mäts med vyn som appen väljer för de öppna skanningarna (djupbildens normal och upp-riktning, "
    "rakt mot den ristade sidan, den vy slingorna är ritade i) och appens förval i övrigt (Vitki-protokollet; stavlöst "
    "läge på när Rundata bara anger stavlösa runor, vilket inte ändrar något när slingor finns).",
]

if __name__ == "__main__":
    main()
