"""Fynd per sten utöver attribueringen: sådant om en enskild sten som inte står i Rundata.

Tre slags fynd, i samma form som appens övriga fynd per sten (src/findings._finding: stämmer / nytt / motsäger, med
belägg, nyhet och relevans):

  luckor i texten   en förlorad runa som sannolikhetsmodellen fyller i med minst 80 % kalibrerad säkerhet där Rundata
                    inte har återställt ordet (data/textmodel_candidates.json, METHODS.md 8.1)
  Runor 2020        uppgifter i Riksantikvarieämbetets nyare utgåva som saknas i eller motsäger Rundata 2018: stenar som
                    Runor anger som flyttade men som Rundata inte märker som flyttade, och läsningar med fler runor
                    (data/raa/runor_2020.json, utdata/runor/jamforelse.json; scripts/runor_compare.py)
  egna fynd         det vi kommit fram till om en sten i artiklar och analyser, fört in för hand med källa
                    (data/stone_findings.json)

Uppgifterna från Runor är inte appens upptäckter utan en nyare källa; de står med för att forskaren ska se allt som
avviker från Rundata på ett ställe.
"""
from __future__ import annotations

import json
import os

from src.findings import _finding, _oeuvre, _province_coverage, relevance
from src.research_gaps import is_runestone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANDIDATES = os.path.join(ROOT, "data", "textmodel_candidates.json")
RUNOR = os.path.join(ROOT, "data", "raa", "runor_2020.json")
RUNOR_COMPARE = os.path.join(ROOT, "utdata", "runor", "jamforelse.json")
MANUAL = os.path.join(ROOT, "data", "stone_findings.json")
LINKS = os.path.join(ROOT, "data", "links.json")

TEXTGAP = "luckor i texten (sannolikhetsmodell)"
RUNOR_PLACE = "Runor 2020 (ursprunglig plats)"
RUNOR_READING = "Runor 2020 (läsning)"
OWN = "egna fynd"
LINK = "samma familj (namnlänk)"
# A newer source, not our discovery: it tells the researcher something Rundata lacks, but ranks below the app's own results
NOVELTY_RUNOR = 0.3


def _load(path: str):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def textgap_findings(lookup, inscriptions: list[dict], ctx=None) -> list[dict]:
    d = _load(CANDIDATES) or {}
    sure = d.get("sure_p", 0.8)
    cov, oeu = ctx or (_province_coverage(inscriptions), _oeuvre(inscriptions))
    out = []
    for c in d.get("candidates") or []:
        rec = lookup(c["signum"])
        if not rec or c.get("p") is None or c["p"] < sure:
            continue
        rel, rr = relevance(rec, None, cov, oeu)
        alts = ", ".join(f"{a[0]} {round(a[1] * 100)} %" for a in (c.get("alts") or [])[:2])
        ours = (f"Luckan i '{c['carved']}' kan fyllas med '{c['fill']}', så att ordet blir {c['word']} "
                f"({round(c['p'] * 100)} % kalibrerad säkerhet)"
                + (f"; läsningen blir \"{c['reading']}\"" if c.get("reading") else "") + ".")
        out.append(_finding(rec, TEXTGAP, "nytt", ours, "Rundata lämnar ordet oåterställt", min(1.0, c["p"]), 0.7, rel,
                            {"belägg": [f"kalibrerad sannolikhet {round(c['p'] * 100)} % (modellen ensam "
                                        f"{round((c.get('p_model') or c['p']) * 100)} %)"] + ([f"alternativ: {alts}"] if alts else []),
                             "nyhet": ["Rundata har inte återställt ordet"], "relevans": rr},
                            False, gap=c, source="data/textmodel_candidates.json",
                            model_version=d.get("model_version"), runestone=bool(c.get("runestone"))))
    return out


def runor_findings(lookup, inscriptions: list[dict], ctx=None) -> list[dict]:
    """Stenar som Runor 2020 anger som flyttade men som Rundata inte märker som flyttade, och läsningar med fler runor."""
    from src.r_bridge import is_moved
    runor = _load(RUNOR)
    cov, oeu = ctx or (_province_coverage(inscriptions), _oeuvre(inscriptions))
    out = []
    if isinstance(runor, dict):
        recs = runor.get("inscriptions", runor)
        items = recs.values() if isinstance(recs, dict) else recs
        for x in items:
            if not isinstance(x, dict) or x.get("original") is not False:
                continue
            rec = lookup(x.get("signum") or "")
            if not rec or not is_runestone(rec) or is_moved(rec):
                continue
            rel, rr = relevance(rec, None, cov, oeu)
            where = x.get("original_text") or x.get("placement") or ""
            # Fixed sentences, so that they translate; Runor's own note goes with the evidence
            out.append(_finding(rec, RUNOR_PLACE, "motsäger", "Runor 2020: stenen står inte på sin ursprungliga plats.",
                                "Rundata märker inte stenen som flyttad (räknas som stående på plats)", 0.8, NOVELTY_RUNOR, rel,
                                {"belägg": ["Riksantikvarieämbetets Runor 2020 (original = nej)"] + ([f"Runor: {where}"] if where else []),
                                 "nyhet": ["påverkar alla analyser av stenens omgivning: vatten, lämningar, landskap"],
                                 "relevans": rr},
                                False, source="Runor 2020 (runor.raa.se)"))
    comp = _load(RUNOR_COMPARE) or {}
    for x in comp.get("more_runes_examples") or []:
        rec = lookup(x.get("signum") or "")
        if not rec:
            continue
        rel, rr = relevance(rec, None, cov, oeu)
        out.append(_finding(rec, RUNOR_READING, "nytt", "Runor 2020 läser fler runor än Rundata.",
                            "Rundata 2018 har en kortare läsning", 0.8, NOVELTY_RUNOR, rel,
                            {"belägg": ["Riksantikvarieämbetets Runor 2020", f"Runor 2020: {x['runor_2020']}",
                                        f"Rundata 2018: {x['rundata_2018']}"],
                             "nyhet": ["en nyare läsning med fler runor"], "relevans": rr}, False,
                            source="Runor 2020 (runor.raa.se)", reading_runor=x["runor_2020"], reading_rundata=x["rundata_2018"]))
    return out


def manual_findings(lookup, inscriptions: list[dict], ctx=None) -> list[dict]:
    """Egna fynd om enskilda stenar (data/stone_findings.json): {signum, verdict, ours, existing, evidence, novelty,
    source, date, method?}."""
    d = _load(MANUAL) or {}
    cov, oeu = ctx or (_province_coverage(inscriptions), _oeuvre(inscriptions))
    out = []
    for x in d.get("findings") or []:
        rec = lookup(x["signum"])
        if not rec:
            continue
        rel, rr = relevance(rec, None, cov, oeu)
        out.append(_finding(rec, x.get("method") or OWN, x.get("verdict", "nytt"), x["ours"], x.get("existing", "–"),
                            float(x.get("evidence", 0.5)), float(x.get("novelty", 0.6)), rel,
                            {"belägg": [x.get("evidence_text") or f"källa: {x.get('source', '–')}"], "nyhet": [], "relevans": rr},
                            False, source=x.get("source"), date=x.get("date")))
    return out


def link_findings(lookup, inscriptions: list[dict], ctx=None) -> list[dict]:
    """Stenar som delar namn med en annan sten mer än slumpen ger (data/links.json, src/linking.py), utan motsägelser i
    släktskap eller tid: troligen samma familj. Rundatas parstenar räknas som bekräftelser."""
    d = _load(LINKS) or {}
    cut = d.get("fdr_cut", 0.1)
    pars = {tuple(p) for p in ((d.get("validation") or {}).get("parsten") or {}).get("pairs") or []}
    cov, oeu = ctx or (_province_coverage(inscriptions), _oeuvre(inscriptions))
    out = []
    for x in d.get("links") or []:
        if x["q"] >= cut or x.get("contradictions"):
            continue
        for this, other in ((x["a"], x["b"]), (x["b"], x["a"])):
            rec = lookup(this)
            if not rec:
                continue
            rel, rr = relevance(rec, None, cov, oeu)
            known = tuple(sorted((this, other))) in pars
            where = f", {x['km']:.0f} km bort".replace(".", ",") if x.get("km") is not None else ""
            ev = max(0.0, 1 - x["q"] * 5)
            out.append(_finding(rec, LINK, "stämmer" if known else "nytt",
                                f"Delar namnen {', '.join(x['names'])} med {other}{where}: troligen samma familj.",
                                "Rundata kallar stenarna parstenar" if known else "Rundata länkar inte stenarna",
                                ev, 0.6, rel,
                                {"belägg": [f"andel falska länkar vid samma styrka {round(x['q'] * 100)} % (namnen blandade inom "
                                            f"landskapet), {round(x.get('q_district', 1) * 100)} % inom häradet",
                                            "släktskap och datering motsäger inte länken"],
                                 "nyhet": [] if known else ["en släktlänk mellan stenarna som Rundata inte anger"],
                                 "relevans": rr}, known, linked=other, shared=x["names"], q=x["q"]))
    return out


def all_findings(lookup, inscriptions: list[dict]) -> list[dict]:
    ctx = (_province_coverage(inscriptions), _oeuvre(inscriptions))
    return (textgap_findings(lookup, inscriptions, ctx) + runor_findings(lookup, inscriptions, ctx)
            + manual_findings(lookup, inscriptions, ctx) + link_findings(lookup, inscriptions, ctx))
