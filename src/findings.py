"""Våra resultat mot befintlig forskning.

Varje fynd från appens analyser – ortografisk stilometri, huggteknik i mätkorpusen och, när statistiken i R
är beräknad, attribueringsmodellen, de okända ristarna och seriationen – ställs mot Rundata, som här får
representera den publicerade forskningen.
Fyndet klassas som

  stämmer   – samma slutsats som i Rundata
  nytt      – Rundata saknar uppgiften (t.ex. ingen ristare angiven)
  motsäger  – en annan slutsats än i Rundata

och får en uppskattning i tre delar, alla mellan 0 och 1 och redovisade öppet:

  belägg     hur pålitlig analysen är i just detta fall (korsvaliderad träffsäkerhet, textlängd,
             avstånd till nästa kandidat)
  nyhet      hur mycket fyndet tillför jämfört med Rundata (en bekräftelse tillför lite, en ny
             attribuering mycket – men mindre utanför Axelsons område, där attribueringar kan finnas i
             litteraturen utan att stå i Rundata)
  relevans   hur mycket det betyder för forskningen (landskap med få kända ristare, ristare med stort
             verk, stenar som finns kvar att undersöka)

Uppskattningen är en tumregel för att prioritera, inte en granskning av forskningsläget.
"""
from __future__ import annotations

import math
from collections import Counter, defaultdict

import numpy as np

from src.research_gaps import (AXELSON_PROVINCES, CARVER_NOTES, carver_home, certain_carvers, has_carver, is_runestone,
                               model_carvers, province)
from src.stats import METRICS, attribute, reliability as technique_reliability
from src.synthesis import language_check, material_check, smoothed_precision

VERDICTS = ("stämmer", "nytt", "motsäger")


def _p(v: float) -> str:
    return "< 0,001" if v < 0.001 else f"{v:.3f}".replace(".", ",")


def _d(v: float, digits: int = 2) -> str:
    return f"{v:.{digits}f}".replace(".", ",")


def _province_coverage(inscriptions: list[dict]) -> dict[str, float]:
    tot, with_carver = Counter(), Counter()
    for r in inscriptions:
        if is_runestone(r):
            tot[province(r)] += 1
            with_carver[province(r)] += has_carver(r)
    return {p: with_carver[p] / tot[p] for p in tot}


def _oeuvre(inscriptions: list[dict]) -> Counter:
    n = Counter()
    for r in inscriptions:
        for c in certain_carvers(r):
            n[c] += 1
    return n


def relevance(rec: dict, carver: str | None, coverage: dict[str, float], oeuvre: Counter) -> tuple[float, list[str]]:
    reasons = []
    cov = coverage.get(province(rec))
    if cov is None:
        # The coverage table counts Swedish runestones only: a stone outside it gets the middle value, not a false 0 %
        r = 0.35 + 0.3 * 0.5
        reasons.append("ristartäckningen räknas bara för svenska runstenar; ingen jämförelse för landskapet")
    else:
        r = 0.35 + 0.3 * (1 - cov)
        reasons.append(f"{round(cov * 100)} % av stenarna i landskapet har ristare i Rundata")
    if carver:
        n = oeuvre.get(carver, 0)
        r += 0.25 * min(1.0, math.log1p(n) / math.log(100))
        reasons.append(f"{carver} har {n} säkra inskrifter")
    if rec["flags"]["lost"]:
        r -= 0.2
        reasons.append("stenen är försvunnen och kan inte undersökas vidare")
    else:
        r += 0.1
    return max(0.0, min(1.0, r)), reasons


def stone_relevance(rec: dict) -> tuple[float, list[str]]:
    """Relevans för fynd om en sten som inte gäller en ristare (luckor i texten, Runor 2020, släktlänkar, egna fynd):
    hur många stenar i landskapet som har ristare säger inget om dem, så bara om stenen finns kvar att undersöka räknas."""
    if rec["flags"]["lost"]:
        return 0.3, ["stenen är försvunnen och kan inte undersökas vidare"]
    return 0.6, ["stenen finns kvar och kan undersökas"]


def assessment(verdict: str, evidence: float, novelty: float, relevance_: float, independent: bool) -> str:
    score = evidence * novelty * relevance_
    if verdict == "stämmer":
        return "Oberoende bekräftelse" if independent and evidence >= 0.4 else "Bekräftar befintlig forskning"
    if verdict == "nytt":
        if score >= 0.2:
            return "Sannolikt ny och relevant kunskap – värd att pröva"
        if score >= 0.08:
            return "Möjlig ny kunskap – behöver fler belägg"
        return "Svagt underlag"
    if evidence >= 0.5 and score >= 0.15:
        return "Värd en omprövning"
    return "Avvikelse – troligen osäkerhet i metoden"


# Bergarten och språkdragen beror bara på stenen, ristaren och korpusen, så de räknas en gång per sten och ristare (nyckeln
# innehåller korpusens och namnlistans identitet, så att en ny Rundata räknas om)
_EXTRAS: dict[tuple, dict] = {}


def stone_extras(rec: dict, carver: str | None, inscriptions: list[dict], names) -> dict:
    """Bergart och språkdrag för en sten, jämförda med den föreslagna ristaren."""
    key = (rec["signum"], carver, id(inscriptions), id(names))
    if key not in _EXTRAS:
        if len(_EXTRAS) > 20000:
            _EXTRAS.clear()
        _EXTRAS[key] = _stone_extras(rec, carver, inscriptions, names)
    out = _EXTRAS[key]
    return {**out, "language": dict(out["language"]) if out.get("language") else out.get("language")}


def _stone_extras(rec: dict, carver: str | None, inscriptions: list[dict], names) -> dict:
    out = {"material": rec.get("material") or None, "material_fit": None, "language": None}
    if carver:
        m = material_check(rec, carver, inscriptions)
        if m:
            out["material_fit"] = m["fits"]
            out["material_text"] = m["text"]
        lang = language_check(rec, carver, inscriptions, names)
        if lang:
            out["language"] = {"agree": lang["agree"], "comparable": lang["comparable"], "text": lang["text"],
                               "fits": lang["fits"]}
    return out


def _finding(rec, method, verdict, ours, existing, evidence, novelty, rel, reasons, independent, **extra) -> dict:
    note = CARVER_NOTES.get(extra.get("suggested") or "")
    if note:  # a group name (such as "Traen") must never be presented as a carver on the card
        reasons = {**reasons, "nyhet": list(reasons.get("nyhet") or []) + [note]}
    return {
        "signum": rec["signum"], "place": rec["place"], "province": province(rec), "method": method,
        "verdict": verdict, "ours": ours, "existing": existing,
        "evidence": round(evidence, 3), "novelty": round(novelty, 3), "relevance": round(rel, 3),
        "score": round(evidence * novelty * rel, 3),
        "assessment": assessment(verdict, evidence, novelty, rel, independent),
        "reasons": reasons, **extra,
    }


def _carver_text(rec: dict) -> str:
    cs = [c for c in rec["carvers"] if c["kind"] in ("S", "A")]
    if not cs and rec.get("same_carver_as"):
        return f"namnlös ristare, samma som gjort {', '.join(rec['same_carver_as'])}"
    return ", ".join(f"{c['name']} ({c['kind']}{'?' if c['uncertain'] else ''})" for c in cs) or "ingen ristare angiven"


def orthographic_findings(model, inscriptions: list[dict], min_words=8, min_margin=0.05,
                          min_similarity=0.6) -> list[dict]:
    """Ortografin (lämna-en-ute: stenen själv ingår aldrig i ristarens profil) mot Rundatas ristare."""
    evaluation = model.evaluate() or {}
    per_carver = evaluation.get("per_carver", {})
    home = carver_home(inscriptions)
    coverage, oeuvre = _province_coverage(inscriptions), _oeuvre(inscriptions)
    known = model_carvers(model)
    out = []
    for rec in model.records:
        if not is_runestone(rec):
            continue
        rk = model.rank_carvers(rec["signum"], 3)
        if not rk or len(rk["ranking"]) < 2 or rk["n_words"] < min_words:
            continue
        top, second = rk["ranking"][0], rk["ranking"][1]
        margin = top["similarity"] - second["similarity"]
        precision = smoothed_precision(per_carver.get(top["carver"]))
        in_area = province(rec) in home.get(top["carver"], {})
        length = 1.0 if rk["n_words"] >= 12 else 0.7
        evidence = precision * (1.0 if in_area else 0.5) * length * min(1.0, 0.5 + margin * 5)
        ev_reasons = [f"modellen har rätt i omkring {round(precision * 100)} % av fallen när den föreslår {top['carver']} "
                      f"({per_carver.get(top['carver'], {}).get('predicted', 0)} förslag)",
                      f"{rk['n_words']} läsbara ord", f"marginal {_d(margin)} till {second['carver']}"]
        if not in_area:
            ev_reasons.append("stenen ligger utanför ristarens kända område")
        sig = top.get("significance")
        ours = (f"Ortografin pekar på {top['carver']} (likhet {_d(top['similarity'])}"
                + (f", p {_p(sig['p_value'])}" if sig else "") + f"; därefter {second['carver']})")
        if sig:
            ev_reasons.append(f"{round(sig['p_value'] * 100, 1)} % av andra ristares inskrifter är minst lika lika "
                              f"{top['carver']}s profil (p {_p(sig['p_value'])}; justerat för att den bästa av "
                              f"{sig['n_carvers']} ristare valts: p {_p(sig['p_adjusted'])})")
            # A similarity that may be chance once the choice of the best carver is taken into account weighs less
            pa = sig["p_adjusted"]
            if pa >= 0.05:
                evidence *= 0.75 if pa < 0.2 else 0.5
                ev_reasons.append("likheten är inte signifikant efter justeringen för urvalet, vilket sänker belägget")
        attributed = [c["name"] for c in rec["carvers"] if c["kind"] in ("S", "A") and not c["uncertain"]]
        # Structured values for the interpretation (src/interpretation.py)
        stats = {"similarity": round(top["similarity"], 3), "margin": round(margin, 3), "n_words": rk["n_words"],
                 "precision": round(precision, 3), "in_area": in_area, "second": second["carver"],
                 "p": sig["p_value"] if sig else None, "p_adjusted": sig["p_adjusted"] if sig else None}
        if not has_carver(rec):
            if top["similarity"] < min_similarity or margin < min_margin:
                continue
            novelty = 0.85 if province(rec) in AXELSON_PROVINCES else 0.55
            nov_reason = ("Axelson (1993) attribuerade inte stenen" if province(rec) in AXELSON_PROVINCES
                          else "attribueringar utanför Mälardalen kan finnas i litteraturen utan att stå i Rundata")
            rel, rel_reasons = relevance(rec, top["carver"], coverage, oeuvre)
            out.append(_finding(rec, "ortografi", "nytt", ours, _carver_text(rec), evidence, novelty, rel,
                                {"belägg": ev_reasons, "nyhet": [nov_reason], "relevans": rel_reasons}, True,
                                suggested=top["carver"], stats=stats))
        elif len(attributed) == 1 and attributed[0] in known:
            truth = attributed[0]
            signed = any(c["kind"] == "S" for c in rec["carvers"])
            order = [r["carver"] for r in rk["ranking"]]
            rel, rel_reasons = relevance(rec, truth, coverage, oeuvre)
            if order[0] == truth:
                # Attributions may themselves rest on orthography, so agreement is not fully independent
                out.append(_finding(rec, "ortografi", "stämmer", ours, _carver_text(rec), evidence,
                                    0.1 if not signed else 0.05, rel,
                                    {"belägg": ev_reasons, "nyhet": ["samma ristare som i litteraturen"],
                                     "relevans": rel_reasons}, independent=False, suggested=top["carver"], stats=stats))
            elif truth not in order and margin >= min_margin:
                if signed:
                    novelty, nov = 0.05, "stenen är signerad – avvikelsen talar mot metoden, inte mot ristaren"
                else:
                    novelty, nov = 0.7, "ifrågasätter en attribuering (A) i litteraturen"
                out.append(_finding(rec, "ortografi", "motsäger", ours, _carver_text(rec), evidence, novelty, rel,
                                    {"belägg": ev_reasons, "nyhet": [nov], "relevans": rel_reasons},
                                    independent=True, suggested=top["carver"], stats=stats))
    return out


def technique_findings(corpus: list[dict], lookup, inscriptions: list[dict]) -> tuple[list[dict], str | None]:
    """Huggteknik: varje uppmätt sten ställs mot ristarna i resten av mätkorpusen."""
    by_signum: dict[str, list[list[float]]] = defaultdict(list)
    for e in corpus:
        means = e.get("means") or {}
        if (e.get("feature_type") or "rune") != "rune" or any(means.get(m) is None for m in METRICS):
            continue
        rec = lookup(e.get("signum") or "")
        if rec:
            by_signum[rec["signum"]].append([float(means[m]) for m in METRICS])
    stones = {s: list(np.mean(v, axis=0)) for s, v in by_signum.items()}
    carver_of = {}
    for s in stones:
        cs = certain_carvers(lookup(s))
        carver_of[s] = cs[0] if len(cs) == 1 else None
    from src.synthesis import material_family
    reference_all = [{"group": carver_of[s], "label": s, "values": v, "family": material_family(lookup(s))}
                     for s, v in stones.items() if carver_of[s]]
    groups = Counter(r["group"] for r in reference_all)
    if sum(1 for n in groups.values() if n >= 2) < 2:
        return [], ("Mätkorpusen har ännu för få ristare med minst två uppmätta stenar (runor) för att pröva "
                    "attribueringar med huggteknik.")
    coverage, oeuvre = _province_coverage(inscriptions), _oeuvre(inscriptions)
    out = []
    for s, values in stones.items():
        rec = lookup(s)
        ref = [r for r in reference_all if r["label"] != s]
        res = attribute(ref, values)
        rk = res.get("ranking") or []
        if len(rk) < 2:
            continue
        ev = res.get("evaluation") or {}
        acc = ev.get("top1_accuracy") or 0.0
        gap = rk[1]["distance"] - rk[0]["distance"]
        # Över den strängare av slumpen och en gissning efter bergart (src/stats.reliability), inte rå träffsäkerhet
        evidence = technique_reliability(ev) * min(1.0, 0.4 + gap / 2)
        mat = ev.get("material_top1")
        ev_reasons = [f"korsvaliderad träffsäkerhet {round(acc * 100)} % ({ev.get('n_stones', '?')} stenar, "
                      f"{ev.get('n_groups', '?')} ristare; slump {round((ev.get('chance_top1') or 0) * 100)} %"
                      + (f", en gissning efter bergart {round(mat * 100)} %" if mat is not None else "") + ")",
                      f"avstånd {_d(rk[0]['distance'])} mot {_d(rk[1]['distance'])} för {rk[1]['group']}"]
        ours = f"Huggtekniken liknar mest {rk[0]['group']} (därefter {rk[1]['group']})"
        truth = carver_of[s]
        in_ref = {r["group"] for r in ref}
        if truth is None:
            if has_carver(rec):
                continue  # uncertain or several carvers in Rundata: not testable
            novelty = 0.85 if province(rec) in AXELSON_PROVINCES else 0.6
            rel, rel_reasons = relevance(rec, rk[0]["group"], coverage, oeuvre)
            out.append(_finding(rec, "huggteknik", "nytt", ours, _carver_text(rec), evidence, novelty, rel,
                                {"belägg": ev_reasons, "nyhet": ["Rundata anger ingen ristare"], "relevans": rel_reasons},
                                True, suggested=rk[0]["group"]))
        elif truth in in_ref:
            rel, rel_reasons = relevance(rec, truth, coverage, oeuvre)
            signed = any(c["kind"] == "S" for c in rec["carvers"])
            if rk[0]["group"] == truth:
                out.append(_finding(rec, "huggteknik", "stämmer", ours, _carver_text(rec), evidence,
                                    0.1 if signed else 0.3, rel,
                                    {"belägg": ev_reasons,
                                     "nyhet": ["huggtekniken är ett oberoende belägg för attribueringen"
                                               if not signed else "stenen är signerad"],
                                     "relevans": rel_reasons}, independent=True, suggested=rk[0]["group"]))
            else:
                novelty, nov = ((0.05, "stenen är signerad – avvikelsen talar mot metoden eller visar variation hos ristaren")
                                if signed else (0.7, "ifrågasätter en attribuering (A) i litteraturen"))
                out.append(_finding(rec, "huggteknik", "motsäger", ours, _carver_text(rec), evidence, novelty, rel,
                                    {"belägg": ev_reasons, "nyhet": [nov], "relevans": rel_reasons},
                                    independent=True, suggested=rk[0]["group"]))
    return out, None


def add_extras(findings: list[dict], lookup, inscriptions: list[dict], names) -> list[dict]:
    for f in findings:
        rec = lookup(f["signum"])
        if rec:
            f.update(stone_extras(rec, f.get("suggested"), inscriptions, names))
    return findings


def summarize(findings: list[dict]) -> dict:
    out = {v: 0 for v in VERDICTS}
    by_method: dict[str, Counter] = defaultdict(Counter)
    for f in findings:
        if f.get("verdict") not in out:  # a hand-entered finding with a misspelt verdict must not fail the whole list
            continue
        out[f["verdict"]] += 1
        by_method[f["method"]][f["verdict"]] += 1
    # The headline count of likely new knowledge: a family link stands on both its stones (src/stone_findings.
    # link_findings) but is one piece of knowledge, so each linked pair counts once; findings about objects other than
    # Swedish Viking-age runestones (own findings may concern any object) are counted for themselves, not in the headline
    from src.stone_findings import LINK
    likely, link_pairs, other_objects = 0, set(), 0
    for f in findings:
        if f.get("stone_finding") and f.get("runestone") is False:
            other_objects += 1
            continue
        if not f["assessment"].startswith("Sannolikt ny"):
            continue
        if f.get("method") == LINK and f.get("linked"):
            link_pairs.add(tuple(sorted((f["signum"], f["linked"]))))
        else:
            likely += 1
    return {"counts": out, "by_method": {m: dict(c) for m, c in by_method.items()},
            "likely_new": likely + len(link_pairs), "likely_new_links": len(link_pairs), "other_objects": other_objects}
