"""Översikt per sten: alla oberoende belägg samlade mot Rundatas ristare (se METHODS.md, 13c).

För varje svensk vikingatida runsten samlas vad sex metoder säger om vem som ristade den:

  modell      R-modellens sannolikhet (avsnitt 17): korsvaliderad för stenar med säker ristare, förslag för
              stenar utan ristare inom 25 km från en träningssten
  ortografi   stavningens likhet med ristarnas profiler (avsnitt 6; stenen själv utelämnad)
  område      om stenen ligger i ristarens kända landskap och högst 60 km från en säker sten av ristaren
  stil        om stenens stilgrupp finns bland ristarens säkra stenar
  språkdrag   om minst hälften av de jämförbara språkdragen stämmer (avsnitt 8)
  bergart     om bergarten förekommer på ristarens stenar (avsnitt 10)

Två mått räknas fram, båda mellan 0 och 1:

  stöd         hur väl beläggen stämmer med Rundatas ristare: ett viktat medelvärde av metoderna som kan
               uttala sig (modell: sannolikheten för ristaren, vikt 2; ortografi: 1 om ristaren kommer först,
               0,6 bland de tre första, annars 0, vikt 1,5; område, stil och språkdrag 1 eller 0, vikt 1;
               bergart 1 eller 0, vikt 0,5)
  alternativ   styrkan för den bästa andra ristaren: 1 − (1 − modellens sannolikhet)(1 − ortografins
               tillförlitlighet om ristaren kommer först), nedräknat med andelen kontroller (område, stil,
               språkdrag, bergart) som inte klaras

Status för stenar med ristare i Rundata: *kan vara felbedömd* (alternativ ≥ 0,4 och stöd < 0,4), *omstridd*
(alternativ ≥ 0,4), *stöds* (stöd ≥ 0,6), annars *svagt underlag* – liksom när färre än två metoder kan uttala
sig. För stenar utan ristare: *nytt förslag* (≥ 0,5), *möjligt förslag* (≥ 0,3), annars *inget förslag*.

Måtten är index för att sortera och prioritera, inte sannolikheter: bara modellens sannolikhet är kalibrerad.
Signerade stenar används som kontroll – hur ofta de hamnar som "kan vara felbedömd" visar hur ofta indexet
larmar i onödan.
"""
from __future__ import annotations

import csv
import os

from src.research_gaps import carver_home, is_runestone, model_carvers, province
from src.synthesis import carver_styles, geography, language_check, material_check, smoothed_precision

WEIGHTS = {"modell": 2.0, "ortografi": 1.5, "område": 1.0, "stil": 1.0, "språkdrag": 1.0, "bergart": 0.5}
CHECKS = ("område", "stil", "språkdrag", "bergart")
MIN_WORDS = 8
STATUS_ORDER = ("kan vara felbedömd", "omstridd", "stöds", "svagt underlag", "signerad",
                "nytt förslag", "möjligt förslag", "inget förslag")


def r_probabilities(directory: str | None) -> tuple[dict, dict]:
    """(korsvaliderade sannolikheter per sten, förslag för stenar utan ristare) ur R-korpusens resultat."""
    oof, pred = {}, {}
    if not directory:
        return oof, pred
    p = os.path.join(directory, "attribution_oof.csv")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                oof[row["signum"]] = {k[len(".pred_"):]: float(v) for k, v in row.items() if k.startswith(".pred_")}
    j = os.path.join(directory, "attribution.json")
    if os.path.exists(j):
        import json
        for x in json.load(open(j, encoding="utf-8")).get("predictions") or []:
            pred[x["signum"]] = {c: x[k] for c, k in ((x.get("top"), "p"), (x.get("second"), "p2"), (x.get("third"), "p3"))
                                 if c and x.get(k) is not None}
    return oof, pred


def _checks(rec, carver, inscriptions, names, home) -> dict:
    """Område, stil, språkdrag och bergart för en ristare: True/False/None och en förklaring."""
    out = {}
    g = geography(rec, carver, inscriptions, home)
    out["område"] = (None if g["nearest_km"] is None and not g["in_area"] else bool(g["plausible"]), g["text"])
    st = carver_styles(rec, carver, inscriptions)
    out["stil"] = (st["fits"], st["text"])
    lang = language_check(rec, carver, inscriptions, names)
    out["språkdrag"] = ((lang or {}).get("fits"), (lang or {}).get("text") or "För få jämförbara språkdrag.")
    mat = material_check(rec, carver, inscriptions)
    out["bergart"] = ((mat or {}).get("fits"), (mat or {}).get("text") or "Bergarten kan inte jämföras.")
    return out


def _plausibility(checks: dict) -> float:
    known = [v for v, _ in checks.values() if v is not None]
    return sum(known) / len(known) if known else 1.0


def stone(rec, ctx: dict, detail: bool = False) -> dict:
    """Beläggen för en sten. ctx: inscriptions, model (ortografi), names, home, evaluation, oof, pred, known."""
    signum = rec["signum"]
    certain = [c for c in rec["carvers"] if c["kind"] in ("S", "A") and not c["uncertain"]]
    uncertain = [c for c in rec["carvers"] if c["kind"] in ("S", "A") and c["uncertain"]]
    # Rundata's carvers: the certain ones, or the uncertain ones if there is no certain carver (several are common:
    # two who signed together, or a signature and an attribution)
    listed = list(dict.fromkeys(c["name"] for c in (certain or uncertain)))
    signed = any(c["kind"] == "S" and not c["uncertain"] for c in rec["carvers"])
    inscriptions, names, home = ctx["inscriptions"], ctx["names"], ctx["home"]

    # The two methods that can point to a carver
    probs = ctx["oof"].get(signum) or ctx["pred"].get(signum) or {}
    model_kind = "korsvaliderad" if signum in ctx["oof"] else ("förslag" if probs else None)
    ortho = None
    m = ctx["model"]
    if signum in m.index:
        rk = m.rank_carvers(signum, 5)
        if rk and rk["n_words"] >= MIN_WORDS and rk["ranking"]:
            per = ctx["evaluation"].get("per_carver", {})
            length = 1.0 if rk["n_words"] >= 12 else 0.7
            ranking = []
            for r in rk["ranking"]:
                in_area = province(rec) in home.get(r["carver"], {})
                ranking.append({"carver": r["carver"], "similarity": round(r["similarity"], 3),
                                "reliability": round(smoothed_precision(per.get(r["carver"])) * (1.0 if in_area else 0.5) * length, 3)})
            ortho = {"ranking": ranking, "n_words": rk["n_words"]}

    def sources_for(carver: str) -> tuple[dict, float | None]:
        src: dict[str, dict] = {}
        if probs and carver in probs:
            src["modell"] = {"value": probs[carver], "points_to": max(probs, key=probs.get),
                             "text": f"Sannolikhet {probs[carver]:.2f} för {carver} ({model_kind})."}
        if ortho and carver in ctx["known"]:
            order = [r["carver"] for r in ortho["ranking"]]
            v = 1.0 if order[0] == carver else (0.6 if carver in order[:3] else 0.0)
            src["ortografi"] = {"value": v, "points_to": order[0],
                                "text": (f"{carver} kommer {'först' if v == 1 else ('bland de tre första' if v else 'inte bland de tre första')}"
                                         f" ({ortho['n_words']} ord; först: {order[0]}).")}
        for key, (fits, text) in _checks(rec, carver, inscriptions, names, home).items():
            if fits is not None:
                src[key] = {"value": 1.0 if fits else 0.0, "points_to": None, "text": text}
        sup = sum(WEIGHTS[k] * x["value"] for k, x in src.items()) / sum(WEIGHTS[k] for k in src) if src else None
        return src, sup

    # With several carvers in Rundata, the best supported one is shown (the others are named, not alternatives)
    current, sources, support = None, {}, None
    for name in listed:
        src, sup = sources_for(name)
        if current is None or (sup or -1) > (support or -1):
            current, sources, support = name, src, sup
    n_sources = len(sources)

    # Candidates other than Rundata's carvers: from the model and the orthography
    candidates = set(probs) | ({ortho["ranking"][0]["carver"]} if ortho else set())
    candidates -= set(listed)
    alts = []
    for c in candidates:
        mp = probs.get(c, 0.0)
        op = ortho["ranking"][0]["reliability"] if ortho and ortho["ranking"][0]["carver"] == c else 0.0
        raw = 1 - (1 - mp) * (1 - op)
        if raw < 0.15:
            continue
        chk = _checks(rec, c, inscriptions, names, home)
        alts.append({"carver": c, "strength": round(raw * (0.5 + 0.5 * _plausibility(chk)), 3), "model": round(mp, 3),
                     "orthography": round(op, 3), "checks": {k: v for k, (v, _) in chk.items()},
                     **({"check_texts": {k: t for k, (_, t) in chk.items()}} if detail else {})})
    alts.sort(key=lambda a: -a["strength"])
    best = alts[0] if alts else None
    strength = best["strength"] if best else 0.0

    if current:
        if signed:
            status = "signerad"
        elif n_sources < 2 or support is None:
            status = "svagt underlag"
        elif strength >= 0.4 and support < 0.4:
            status = "kan vara felbedömd"
        elif strength >= 0.4:
            status = "omstridd"
        elif support >= 0.6:
            status = "stöds"
        else:
            status = "svagt underlag"
    else:
        status = "nytt förslag" if strength >= 0.5 else ("möjligt förslag" if strength >= 0.3 else "inget förslag")

    out = {"signum": signum, "province": province(rec), "place": rec.get("place") or "", "carver": current,
           "carvers": listed,
           "carver_kind": ("S" if signed else ("A" if certain else ("?" if uncertain else None))),
           "status": status, "support": round(support, 3) if support is not None else None,
           "alternative": {"carver": best["carver"], "strength": best["strength"]} if best else None,
           "n_sources": n_sources, "lat": rec.get("lat"), "lon": rec.get("lon")}
    if detail:
        out["sources"] = sources
        out["alternatives"] = alts[:3]
        out["model"] = {"kind": model_kind, "probabilities": dict(sorted(probs.items(), key=lambda kv: -kv[1])[:5])} if probs else None
        out["orthography"] = ortho
    return out


def context(inscriptions, model, r_directory: str | None) -> dict:
    oof, pred = r_probabilities(r_directory)
    return {"inscriptions": inscriptions, "model": model, "names": model.names, "home": carver_home(inscriptions),
            "evaluation": model.evaluate() or {}, "oof": oof, "pred": pred, "known": model_carvers(model)}


def overview(inscriptions, model, r_directory: str | None) -> dict:
    ctx = context(inscriptions, model, r_directory)
    stones = [stone(r, ctx) for r in inscriptions if is_runestone(r)]
    counts = {s: sum(1 for x in stones if x["status"] == s) for s in STATUS_ORDER}
    # Control: signed stones are the closest thing to ground truth; how often would the index have flagged them?
    signed = [x for x in stones if x["status"] == "signerad"]
    flagged = [x for x in signed if (x["alternative"] or {}).get("strength", 0) >= 0.4]
    wrong = [x for x in flagged if (x["support"] or 0) < 0.4]
    return {"stones": stones, "counts": counts,
            "control": {"n_signed": len(signed), "flagged": len(flagged), "would_be_misjudged": len(wrong)},
            "r_available": bool(ctx["oof"] or ctx["pred"])}


def _percentile(value, values) -> int | None:
    if value is None or len(values) < 10:
        return None
    below = sum(1 for v in values if v < value) + 0.5 * sum(1 for v in values if v == value)
    return round(100 * below / len(values))


def variables(rec, inscriptions, r_rows: dict | None = None) -> dict:
    """Stenens övriga variabler, med percentil inom landskapet där det går (storlek, text, syfte, stil, tid)."""
    from src import stone_dimensions
    from src.inscription_types import CATEGORIES, categories
    from src.stone_size import n_names, n_words, status_words

    prov = province(rec)
    same = [r for r in inscriptions if is_runestone(r) and province(r) == prov]
    dims = stone_dimensions.lookup(rec["signum"]) or {}
    all_dims = stone_dimensions.load().get("stones") or {}
    heights = [d["height_m"] for s, d in all_dims.items() if d.get("status") == "ok" and d.get("height_m")
               and not d.get("fragment") and s.split(" ")[0] == prov]
    words, nm = n_words(rec), n_names(rec)
    out = {
        "height_m": dims.get("height_m"), "height_pct": _percentile(dims.get("height_m"), heights) if not dims.get("fragment") else None,
        "rune_height_cm": dims.get("rune_height_cm"), "fragment": bool(dims.get("fragment")), "kmr_url": dims.get("kmr_url"),
        "n_words": words, "n_words_pct": _percentile(words, [n_words(r) for r in same]),
        "n_names": nm, "n_names_pct": _percentile(nm, [n_names(r) for r in same]),
        "categories": [CATEGORIES[k][0] for k in categories(rec)], "status_words": status_words(rec),
        "style": rec.get("style"), "style_uncertain": rec.get("style_uncertain"), "dating": rec.get("dating"),
        "material": rec.get("material"), "lost": rec["flags"].get("lost"), "province": prov, "n_province": len(same),
    }
    if r_rows:
        ch = r_rows.get("chronology", {}).get(rec["signum"])
        if ch:
            out["seriation"] = {"year": ch.get("est"), "lo": ch.get("lo"), "hi": ch.get("hi")}
        cl = r_rows.get("clusters", {}).get(rec["signum"])
        if cl:
            out["cluster"] = cl.get("cluster")
    return out
