"""Jämförelse av två stenar (se METHODS.md, 4).

Huggspåren jämförs med runan som enhet när snitten bär runnummer (automatisk analys): snitt i samma runa delar
slag, verktyg och vittring och är inte oberoende, så permutationstestet flyttar hela runor mellan stenarna. Utan
runnummer jämförs snitten, med en varning om att p-värdena då blir för små. Det samlade testet använder de stabila
måtten (V-vinkel, djup, bredd, djup/bredd); asymmetri och bottenradie redovisas men flaggas (METHODS.md 2e, 18).

Avståndet mellan stenarna ställs dessutom mot en referensskala: avstånden mellan stenpar i mätkorpusen, för par
med samma ristare och par med olika ristare i Rundata. Jämförbarheten kontrolleras (spårtyp, metodversion,
Vitki-protokollet, antal runor, punkttäthet, bergart), och har båda stenarna signum jämförs också ristare,
stilgrupp, datering, avstånd, bergart, storlek, stavning och språkdrag.
"""
from __future__ import annotations

import math

import numpy as np

from src.stats import METRIC_LABELS, METRICS, summarize

STABLE = ["apex_vinkel_deg", "spårdjup_mm", "spårbredd_mm", "djup_bredd_kvot"]
UNRELIABLE = {"asymmetri_deg", "bottenradie_mm"}
N_PERM = 5000


def units(slices: list[dict]) -> tuple[list[dict], str]:
    """Jämförelseenheterna: runornas medelvärden om minst 80 % av snitten har runnummer, annars snitten."""
    with_rune = [s for s in slices if s.get("rune_id") is not None]
    if slices and len(with_rune) >= 0.8 * len(slices):
        by: dict = {}
        for s in with_rune:
            by.setdefault(s["rune_id"], []).append(s)
        out = []
        for ss in by.values():
            row = {}
            for m in METRICS:
                v = [x[m] for x in ss if isinstance(x.get(m), (int, float)) and math.isfinite(x[m])]
                row[m] = float(np.mean(v)) if v else None
            out.append(row)
        return out, "runa"
    return [{m: s.get(m) for m in METRICS} for s in slices], "snitt"


def _vals(us: list[dict], m: str) -> np.ndarray:
    return np.array([u[m] for u in us if u.get(m) is not None and math.isfinite(u[m])], float)


def _perm(a: np.ndarray, b: np.ndarray, n_perm: int, seed: int = 0) -> float | None:
    if a.size < 2 or b.size < 2:
        return None
    rng = np.random.default_rng(seed)
    obs = abs(a.mean() - b.mean())
    pooled = np.concatenate([a, b])
    hits = 0
    for _ in range(n_perm):
        rng.shuffle(pooled)
        if abs(pooled[:a.size].mean() - pooled[a.size:].mean()) >= obs - 1e-12:
            hits += 1
    return (hits + 1) / (n_perm + 1)


def groove_comparison(slices_a: list[dict], slices_b: list[dict], n_perm: int = N_PERM) -> dict:
    ua, kind_a = units(slices_a)
    ub, kind_b = units(slices_b)
    kind = "runa" if kind_a == kind_b == "runa" else "snitt"
    if kind == "snitt" and "runa" in (kind_a, kind_b):  # mixed: compare slices for both
        ua, ub = [{m: s.get(m) for m in METRICS} for s in slices_a], [{m: s.get(m) for m in METRICS} for s in slices_b]
    per = []
    for m in METRICS:
        a, b = _vals(ua, m), _vals(ub, m)
        sd = math.sqrt(((a.size - 1) * a.var(ddof=1) + (b.size - 1) * b.var(ddof=1)) / (a.size + b.size - 2)) if a.size > 1 and b.size > 1 else 0
        per.append({"metric": m, "label": METRIC_LABELS.get(m, m), "stable": m not in UNRELIABLE,
                    "a": summarize(a), "b": summarize(b), "p_value": _perm(a, b, n_perm),
                    "diff": float(a.mean() - b.mean()) if a.size and b.size else None,
                    "effect_size_d": float((a.mean() - b.mean()) / sd) if sd > 0 else None})
    k = sum(1 for r in per if r["p_value"] is not None)
    for r in per:
        r["p_adjusted"] = min(1.0, r["p_value"] * k) if r["p_value"] is not None else None
    # Overall: stable measures, standardised, permuting whole units
    A = np.array([[u[m] for m in STABLE] for u in ua if all(u.get(m) is not None for m in STABLE)], float)
    B = np.array([[u[m] for m in STABLE] for u in ub if all(u.get(m) is not None for m in STABLE)], float)
    overall = {"p_value": None, "distance": None, "metrics_used": STABLE}
    if len(A) >= 2 and len(B) >= 2:
        X = np.vstack([A, B])
        sd = X.std(axis=0, ddof=1)
        sd[sd == 0] = 1
        Z = (X - X.mean(axis=0)) / sd
        na = len(A)
        stat = lambda z: float(np.linalg.norm(z[:na].mean(axis=0) - z[na:].mean(axis=0)))  # noqa: E731
        obs = stat(Z)
        rng = np.random.default_rng(0)
        hits = sum(stat(Z[rng.permutation(len(Z))]) >= obs - 1e-12 for _ in range(n_perm))
        overall = {"p_value": (hits + 1) / (n_perm + 1), "distance": obs, "metrics_used": STABLE}
    means_a = {m: (float(_vals(ua, m).mean()) if _vals(ua, m).size else None) for m in METRICS}
    means_b = {m: (float(_vals(ub, m).mean()) if _vals(ub, m).size else None) for m in METRICS}
    return {"unit": kind, "n_units": [len(ua), len(ub)], "per_metric": per, "overall": overall,
            "means": [means_a, means_b],
            "unit_values": [{m: _vals(ua, m).round(3).tolist() for m in STABLE}, {m: _vals(ub, m).round(3).tolist() for m in STABLE}]}


def reference_scale(means_a: dict, means_b: dict, corpus: list[dict], carver_of, feature_type: str | None,
                    method_version: str | None, material_of=None, pair_families: set | None = None) -> dict | None:
    """Var parets avstånd hamnar bland avstånden mellan stenpar i mätkorpusen (stabila mått, standardiserade med
    spridningen mellan korpusens stenar), för alla par, par med samma ristare och par med olika ristare. Delar
    paret en bergartsfamilj (src/geology.FAMILIES) jämförs det också mot korpusens par av samma familj – Rak-
    replikationen visade att bergarten påverkar måtten mer än handen, så den skalan är den ärligaste."""
    rows = []
    for e in corpus:
        mv = e.get("means") or {}
        if feature_type and (e.get("feature_type") or "unknown") != feature_type:
            continue
        if method_version and e.get("method_version") and e["method_version"] != method_version:
            continue
        if all(isinstance(mv.get(m), (int, float)) for m in STABLE):
            rows.append((e.get("signum"), [float(mv[m]) for m in STABLE]))
    if len(rows) < 5 or not all(means_a.get(m) is not None and means_b.get(m) is not None for m in STABLE):
        return None
    X = np.array([r[1] for r in rows])
    sd = X.std(axis=0, ddof=1)
    sd[sd == 0] = 1
    d_ab = float(np.linalg.norm((np.array([means_a[m] for m in STABLE]) - np.array([means_b[m] for m in STABLE])) / sd))
    fams = [material_of(r[0]) if material_of else set() for r in rows]
    same, diff, all_, mat = [], [], [], []
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            d = float(np.linalg.norm((X[i] - X[j]) / sd))
            all_.append(d)
            ci, cj = carver_of(rows[i][0]), carver_of(rows[j][0])
            if ci and cj:
                (same if ci == cj else diff).append(d)
            if pair_families and fams[i] & fams[j] & pair_families:
                mat.append(d)
    pct = lambda v: round(100 * sum(1 for x in v if x < d_ab) / len(v)) if v else None  # noqa: E731
    return {"distance": round(d_ab, 3), "n_stones": len(rows), "n_pairs": len(all_),
            "percentile_all": pct(all_), "percentile_same": pct(same), "percentile_different": pct(diff),
            "n_same": len(same), "n_different": len(diff),
            "percentile_material": pct(mat) if len(mat) >= 10 else None, "n_material": len(mat),
            "material_family": sorted(pair_families)[0] if pair_families else None,
            "median_same": round(float(np.median(same)), 3) if same else None,
            "median_different": round(float(np.median(diff)), 3) if diff else None}


def comparability(a: dict, b: dict, ga: dict, rec_a: dict | None, rec_b: dict | None) -> list[dict]:
    """Kontroller av om de två mätningarna går att jämföra. a, b: stenarna (feature_type, provenance)."""
    from src import geology, protocol
    from src.limitations import MIN_RUNES_COMPARE, MIN_RUNES_DESCRIBE
    out = []
    fa, fb = a.get("feature_type") or "unknown", b.get("feature_type") or "unknown"
    out.append({"key": "spårtyp", "ok": fa == fb, "text": "Samma spårtyp." if fa == fb
                else "Olika spårtyper (runor och ornamentik huggs ofta olika)."})
    pa, pb = a.get("provenance") or {}, b.get("provenance") or {}
    ma, mb = pa.get("method_version"), pb.get("method_version")
    if ma or mb:
        same = ma == mb
        out.append({"key": "metodversion", "ok": same, "text": f"Samma mätmetod ({ma})." if same
                    else f"Olika mätmetoder ({ma or 'okänd'} och {mb or 'okänd'}); räkna om med råprofilerna."})
    pra, prb = pa.get("protocol"), pb.get("protocol")
    if pra or prb:
        ok = bool(pra and prb and pra.get("compliant") and prb.get("compliant"))
        out.append({"key": "protokoll", "ok": ok, "text": "Båda följer Vitki-protokollet." if ok
                    else "Minst en mätning följer inte Vitki-protokollet (eller saknar uppgiften); jämför med försiktighet."})
    na, nb = ga["n_units"]
    if ga["unit"] == "runa":
        lo = min(na, nb)
        out.append({"key": "runor", "ok": lo >= MIN_RUNES_COMPARE if lo >= MIN_RUNES_DESCRIBE else False,
                    "text": f"{na} och {nb} runor" + (" – över riktvärdet för jämförelser." if lo >= MIN_RUNES_COMPARE else
                    f" – under riktvärdet {MIN_RUNES_COMPARE} för jämförelser; resultatet är osäkert.")})
    else:
        out.append({"key": "enhet", "ok": False,
                    "text": f"Snitten saknar runnummer ({na} och {nb} snitt), så snitten jämförs som om de vore oberoende – "
                            "p-värdena blir för små. Analysera stenarna automatiskt för att jämföra runa mot runa."})
    sa = ((pa.get("parameters") or {}).get("mesh_point_spacing_mm"))
    sb = ((pb.get("parameters") or {}).get("mesh_point_spacing_mm"))
    if sa and sb and sa == sa and sb == sb:
        ratio = max(sa, sb) / min(sa, sb)
        out.append({"key": "punkttäthet", "ok": ratio <= 1.5,
                    "text": f"Skanningarnas punktavstånd {sa:.2f} och {sb:.2f} mm".replace(".", ",") + ("." if ratio <= 1.5 else
                    " – mycket olika täthet påverkar måtten (METHODS.md 2e).")})
    if rec_a and rec_b:
        fam_a = geology.families(rec_a.get("material") or "")
        fam_b = geology.families(rec_b.get("material") or "")
        if fam_a and fam_b:
            ok = bool(fam_a & fam_b)
            out.append({"key": "bergart", "ok": ok, "text": f"Bergart: {rec_a.get('material')} och {rec_b.get('material')}"
                        + ("." if ok else " – olika bergarter kan ensamma ge skillnader i huggspåren.")})
    return out


def context(rec_a: dict, rec_b: dict, model, names, dims_lookup) -> dict:
    """Det som inte är huggspår: ristare, stil, datering, avstånd, bergart, storlek, stavning och språkdrag."""
    from src.language_profile import traits
    from src.synthesis import _km

    def carvers(r):
        return ", ".join(f"{c['name']} ({c['kind']}{'?' if c['uncertain'] else ''})" for c in r["carvers"] if c["kind"] in ("S", "A")) or "–"
    rows = [{"label": "Ristare i Rundata", "a": carvers(rec_a), "b": carvers(rec_b)},
            {"label": "Stilgrupp", "a": rec_a.get("style") or "–", "b": rec_b.get("style") or "–"},
            {"label": "Datering", "a": rec_a.get("dating") or "–", "b": rec_b.get("dating") or "–"},
            {"label": "Bergart", "a": rec_a.get("material") or "–", "b": rec_b.get("material") or "–"}]
    da, db = dims_lookup(rec_a["signum"]) or {}, dims_lookup(rec_b["signum"]) or {}
    if da.get("height_m") or db.get("height_m"):
        f = lambda d: f"{d['height_m']:.2f} m".replace(".", ",") if d.get("height_m") else "–"  # noqa: E731
        rows.append({"label": "Höjd (Kulturmiljöregistret)", "a": f(da), "b": f(db)})
    out = {"rows": rows}
    if rec_a.get("lat") is not None and rec_b.get("lat") is not None:
        out["distance_km"] = round(_km((rec_a["lat"], rec_a["lon"]), (rec_b["lat"], rec_b["lon"])), 1)
    i, j = model.index.get(rec_a["signum"]), model.index.get(rec_b["signum"])
    if i is not None and j is not None:
        sims = (model.X @ model.X[i].T).toarray().ravel()
        sims[i] = np.nan
        s = float(sims[j])
        others = sims[~np.isnan(sims)]
        out["orthography"] = {"similarity": round(s, 3), "percentile": round(100 * float(np.mean(others < s))),
                              "n": int(others.size)}
    ta, tb = traits(rec_a, names) or {}, traits(rec_b, names) or {}
    both = [k for k in ta if k in tb and ta[k] is not None and tb[k] is not None]
    if both:
        agree = [k for k in both if ta[k] == tb[k]]
        out["language"] = {"agree": len(agree), "comparable": len(both),
                           "differ": [f"{k}: {ta[k]} / {tb[k]}" for k in both if ta[k] != tb[k]]}
    return out


def conclusion(ga: dict, ref: dict | None, checks: list[dict], ctx: dict | None) -> list[str]:
    """Ett resonemang i några meningar, från huggspåren till de övriga beläggen."""
    out = []
    p = ga["overall"]["p_value"]
    unit = "runorna" if ga["unit"] == "runa" else "snitten"
    ptxt = "–" if p is None else ("< 0,001" if p < 0.001 else f"{p:.3f}".replace(".", ","))
    if p is None:
        out.append("För få mätningar för ett samlat test.")
    elif p < 0.01:
        out.append(f"Huggspåren skiljer sig tydligt (samlat test på {unit}, p {ptxt}).")
    elif p < 0.05:
        out.append(f"Huggspåren skiljer sig (samlat test på {unit}, p {ptxt}), men inte starkt.")
    else:
        out.append(f"Huggspåren skiljer sig inte påvisbart (samlat test på {unit}, p {ptxt}); det är förenligt med samma "
                   "hand men bevisar den inte.")
    if ref:
        out.append(f"Avståndet är större än {ref['percentile_all']} % av avstånden mellan stenpar i mätkorpusen"
                   + (f"; bland par med samma ristare är det större än {ref['percentile_same']} %" if ref.get("percentile_same") is not None else "")
                   + (f" och bland par med olika ristare större än {ref['percentile_different']} %" if ref.get("percentile_different") is not None else "")
                   + ".")
        if ref.get("percentile_material") is not None:
            out.append(f"Bland korpusens par av samma bergartsfamilj som stenarna ({ref['material_family']}, "
                       f"{ref['n_material']} par) är avståndet större än {ref['percentile_material']} %. Den skalan "
                       "väger tyngst: vår replikationsstudie visade att bergarten påverkar måtten mer än handen.")
    bad = [c for c in checks if c["ok"] is False]
    if bad:
        out.append("Jämförbarheten är begränsad: " + "; ".join(c["text"].rstrip(".") for c in bad) + ".")
    if ctx:
        o = ctx.get("orthography")
        if o:
            out.append(f"Stavningen liknar varandra mer än {o['percentile']} % av sten A:s jämförelser med andra inskrifter.")
        lang = ctx.get("language")
        if lang:
            out.append(f"{lang['agree']} av {lang['comparable']} jämförbara språkdrag stämmer överens.")
        if ctx.get("distance_km") is not None:
            out.append(f"Stenarna står {ctx['distance_km']:.0f} km från varandra." if ctx["distance_km"] >= 1
                       else "Stenarna står på samma plats.")
    return out
