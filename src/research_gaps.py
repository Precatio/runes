"""Forskningsluckor: var saknas uppgifter i Rundata, och var kan nya mätningar göra skillnad?

Allt räknas fram ur Rundata och den ortografiska modellen. Observera att frånvaro av en uppgift i
Rundata inte betyder att forskning saknas: ristaruppgifterna för Mälardalen bygger främst på
Axelson (1993), som täcker Södermanland, Uppland, Västmanland och Gästrikland.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict

SWEDISH = {"U", "Sö", "Ög", "Vg", "Sm", "Öl", "G", "Vs", "Nä", "Gs", "Hs", "M", "Ån", "J", "D", "Bo", "Ds",
           "Vr", "Hr", "Lp", "SE"}
PROVINCE_NAMES = {
    "U": "Uppland", "Sö": "Södermanland", "Ög": "Östergötland", "Vg": "Västergötland", "Sm": "Småland",
    "Öl": "Öland", "G": "Gotland", "Vs": "Västmanland", "Nä": "Närke", "Gs": "Gästrikland",
    "Hs": "Hälsingland", "M": "Medelpad", "Ån": "Ångermanland", "J": "Jämtland", "D": "Dalarna",
    "Bo": "Bohuslän", "Ds": "Dalsland", "Vr": "Värmland", "Hr": "Härjedalen", "Lp": "Lappland", "SE": "Okänt landskap",
}
AXELSON_PROVINCES = {"Sö", "U", "Vs", "Gs"}
SOURCE_NOTE = (
    "Uppgifterna kommer ur Samnordisk runtextdatabas. Ristaruppgifterna för Södermanland, Uppland, "
    "Västmanland och Gästrikland bygger främst på Axelson (1993); i andra landskap kan attribueringar "
    "finnas i litteraturen utan att vara inlagda i Rundata."
)


def province(rec: dict) -> str:
    return rec["signum"].split(" ")[0]


def is_runestone(rec: dict) -> bool:
    return (rec["period"] == "V" and province(rec) in SWEDISH
            and "runsten" in (rec.get("object") or "").lower())


def certain_carvers(rec: dict) -> list[str]:
    return [c["name"] for c in rec["carvers"] if c["kind"] in ("S", "A") and not c["uncertain"]]


def has_carver(rec: dict) -> bool:
    return any(c["kind"] in ("S", "A") for c in rec["carvers"])


def has_style(rec: dict) -> bool:
    return bool(rec["style"]) and rec["style"] != "?" and not rec["style_uncertain"]


def is_dated_by_year(rec: dict) -> bool:
    return bool(re.search(r"\d{3,4}", rec.get("dating") or ""))


def uncertain_interpretation(rec: dict) -> bool:
    n = (rec.get("normalization") or "").strip()
    return not n or n.startswith("?") or "(?)" in n


def coverage(inscriptions: list[dict], measured: set[str]) -> dict:
    stones = [r for r in inscriptions if is_runestone(r)]
    rows = defaultdict(Counter)
    for r in stones:
        p = province(r)
        c = rows[p]
        c["total"] += 1
        c["carver"] += has_carver(r)
        c["style"] += has_style(r)
        c["dated"] += is_dated_by_year(r)
        c["uncertain_interpretation"] += uncertain_interpretation(r)
        c["lost"] += r["flags"]["lost"]
        c["measured"] += r["signum"] in measured
    per_province = sorted(
        ({"code": p, "name": PROVINCE_NAMES.get(p, p), "axelson": p in AXELSON_PROVINCES, **dict(c)}
         for p, c in rows.items()),
        key=lambda x: -x["total"],
    )
    totals = Counter()
    for row in per_province:
        for k, v in row.items():
            if isinstance(v, int) and not isinstance(v, bool):
                totals[k] += v
    return {"scope": "Svenska vikingatida runstenar", "totals": dict(totals), "per_province": per_province}


def carver_home(inscriptions: list[dict]) -> dict[str, Counter]:
    home: dict[str, Counter] = defaultdict(Counter)
    for r in inscriptions:
        for name in certain_carvers(r):
            home[name][province(r)] += 1
    return home


def orthographic_hypotheses(model, inscriptions: list[dict], min_similarity=0.6, min_margin=0.05,
                            min_words=8) -> dict:
    """Oattribuerade runstenar där ortografin pekar tydligt mot en ristare, och attribuerade stenar
    där ortografin pekar mot någon annan (kandidater för omprövning)."""
    home = carver_home(inscriptions)
    evaluation = model.evaluate()
    per_carver = evaluation.get("per_carver", {})
    new, reconsider = [], []
    for rec in model.records:
        if not is_runestone(rec) or rec["flags"]["lost"]:
            continue
        rk = model.rank_carvers(rec["signum"], 3)
        ranking = rk["ranking"]
        if len(ranking) < 2:
            continue
        top, second = ranking[0], ranking[1]
        margin = top["similarity"] - second["similarity"]
        p = province(rec)
        home_provinces = home.get(top["carver"], Counter())
        in_home = p in home_provinces
        item = {
            "signum": rec["signum"], "place": rec["place"], "province": p, "style": rec["style"],
            "carver": top["carver"], "similarity": round(top["similarity"], 3), "margin": round(margin, 3),
            "p_value": (top.get("significance") or {}).get("p_value"),
            "p_adjusted": (top.get("significance") or {}).get("p_adjusted"),
            "runner_up": second["carver"], "n_words": rk["n_words"], "in_carver_area": in_home,
            "carver_area": [k for k, _ in home_provinces.most_common(3)],
            # How often the model is right when it names this carver (cross-validated)
            "carver_precision": per_carver.get(top["carver"], {}).get("precision"),
            "short_text": rk["n_words"] < 12,
        }
        if rk["n_words"] < min_words:
            continue
        if not has_carver(rec):
            if top["similarity"] >= min_similarity and margin >= min_margin:
                new.append(item)
        else:
            attributed = [c["name"] for c in rec["carvers"] if c["kind"] == "A"]
            top3 = [r["carver"] for r in ranking]
            if attributed and not any(a in top3 for a in attributed) and margin >= min_margin \
                    and any(a in model_carvers(model) for a in attributed):
                reconsider.append({**item, "attributed_to": attributed})
    def strength(x):
        return (x["carver_precision"] or 0) * x["similarity"] * (1 if x["in_carver_area"] else 0.5)

    new.sort(key=lambda x: -strength(x))
    reconsider.sort(key=lambda x: -strength(x))
    return {"new": new, "reconsider": reconsider, "evaluation": evaluation}


def model_carvers(model) -> set[str]:
    if not hasattr(model, "_carver_set"):
        model._carver_set = set(model._labelled().values())
    return model._carver_set


def open_questions(inscriptions: list[dict], limit=200) -> dict:
    stones = [r for r in inscriptions if is_runestone(r) and not r["flags"]["lost"]]
    uninterpreted = sorted(
        (r for r in stones if uncertain_interpretation(r) and r["transliteration"]),
        key=lambda r: -len(r["transliteration"]),
    )
    uncertain_style = [r for r in stones if r["style"] and (r["style"] == "?" or r["style_uncertain"])]
    brief = lambda r: {"signum": r["signum"], "place": r["place"], "province": province(r), "style": r["style"],
                       "dating": r["dating"], "carvers": [c["name"] for c in r["carvers"] if c["kind"] in "SA"]}
    return {
        "uninterpreted": {"count": len(uninterpreted), "items": [brief(r) for r in uninterpreted[:limit]]},
        "uncertain_style": {"count": len(uncertain_style), "items": [brief(r) for r in uncertain_style[:limit]]},
    }


def measurement_priorities(inscriptions: list[dict], measured: set[str], min_inscriptions=5,
                           target=5) -> list[dict]:
    """Ristare med många inskrifter i Rundata men få uppmätta stenar: här gör nya mätningar mest nytta,
    eftersom attribueringen mot korpusen kräver flera uppmätta stenar per ristare."""
    by_carver: dict[str, list[dict]] = defaultdict(list)
    for r in inscriptions:
        if not is_runestone(r):
            continue
        cs = certain_carvers(r)
        if len(cs) == 1:
            by_carver[cs[0]].append(r)
    out = []
    for name, recs in by_carver.items():
        if len(recs) < min_inscriptions:
            continue
        done = [r["signum"] for r in recs if r["signum"] in measured]
        candidates = [r for r in recs if r["signum"] not in measured and not r["flags"]["lost"]]
        # Signed stones first: the attribution is most certain there
        candidates.sort(key=lambda r: (0 if any(c["kind"] == "S" for c in r["carvers"]) else 1, r["signum"]))
        out.append({
            "carver": name,
            "inscriptions": len(recs),
            "signed": sum(any(c["kind"] == "S" for c in r["carvers"]) for r in recs),
            "measured": len(done),
            "measured_signa": done,
            "missing_to_target": max(0, target - len(done)),
            "suggestions": [{"signum": r["signum"], "place": r["place"],
                             "signed": any(c["kind"] == "S" for c in r["carvers"]),
                             "has_coords": r["lat"] is not None} for r in candidates[:8]],
        })
    out.sort(key=lambda x: (x["measured"] >= 2, -x["inscriptions"]))
    return out
