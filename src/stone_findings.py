"""Fynd per sten utöver attribueringen: sådant om en enskild sten som inte står i Rundata.

Fyra slags fynd, i samma form som appens övriga fynd per sten (src/findings._finding: stämmer / nytt / motsäger, med
belägg, nyhet och relevans). Alla fyra gäller bara svenska vikingatida runstenar (appens grundregel): en släktlänk till
en dansk eller norsk sten visas på den svenska stenen men ger inget fynd på den andra, och ett eget fynd om något annat
hoppas över:

  luckor i texten   en förlorad runa som sannolikhetsmodellen fyller i med minst 80 % kalibrerad säkerhet där Rundata
                    inte har återställt ordet (data/textmodel_candidates.json, METHODS.md 8.1); kandidater att granska
                    mot foto eller skanning, inte färdiga fynd
  Runor 2020        uppgifter i Riksantikvarieämbetets nyare utgåva som saknas i eller motsäger Rundata 2018: stenar som
                    Runor anger som flyttade men som appens flyttregel (src/r_bridge.is_moved) räknar som stående på
                    plats, och läsningar med fler säkert lästa runor
                    (data/raa/runor_2020.json, utdata/runor/jamforelse.json; scripts/runor_compare.py)
  egna fynd         det vi kommit fram till om en sten i artiklar och analyser, fört in för hand med källa
                    (data/stone_findings.json)
  samma familj      stenar som delar namn med en annan sten mer än slumpen ger, utan motsägelser i släktskap eller tid
                    (data/links.json, src/linking.py); varje länk står på båda stenarna, så antalet fynd är dubbelt så
                    stort som antalet länkar

Uppgifterna från Runor är inte appens upptäckter utan en nyare källa; de står med för att forskaren ska se allt som
avviker från Rundata på ett ställe. Fynden gäller inte en ristare, så relevansen räknas utan ristartäckningen i
landskapet (src/findings.stone_relevance), och de får ingen tolkningsnivå (src/interpretation.py).
"""
from __future__ import annotations

import json
import logging
import os

from src.findings import VERDICTS, _finding, stone_relevance
from src.placement import placement_elsewhere  # noqa: F401  (re-exported)
from src.research_gaps import is_runestone

log = logging.getLogger(__name__)

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
METHODS = (TEXTGAP, RUNOR_PLACE, RUNOR_READING, OWN, LINK)
# A newer source, not our discovery: it tells the researcher something Rundata lacks, but ranks below the app's own results
NOVELTY_RUNOR = 0.3
# Fixed assessments: the method-oriented labels of findings.assessment ("osäkerhet i metoden", "Sannolikt ny …") do not
# fit a fact from a newer edition or a candidate list that is meant to be checked against the stone
ASSESS_TEXTGAP = "Kandidat att granska mot foto eller skanning"
ASSESS_RUNOR_PLACE = "Uppgift i nyare källa – kontrollera platsen"
ASSESS_RUNOR_PLACE_RULE = "Rundatas placering säger detsamma – appens flyttregel missar den"
ASSESS_RUNOR_READING = "Uppgift i nyare källa – kontrollera läsningen"


# Hand-checked 2026-10-27: the stones Runor 2020 calls moved whose Rundata placement text the rule in
# placement_elsewhere gets wrong. The other stones with a placement text were checked against the rule by hand too
# (METHODS.md 1q).
def _stone(f: dict, assessment: str | None = None) -> dict:
    """Märker ett fynd som fynd om en sten (inte om en ristare); en fast bedömning ersätter tumregelns etikett."""
    f["stone_finding"] = True
    if assessment:
        f["assessment"] = assessment
    return f


def _load(path: str):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def textgap_findings(lookup, inscriptions: list[dict], ctx=None) -> list[dict]:
    """Säkra luckfyllnader på svenska vikingatida runstenar; andra föremål visas bara i fliken Luckor i texten, med egna
    tal (METHODS.md 14)."""
    d = _load(CANDIDATES) or {}
    sure = d.get("sure_p", 0.8)
    out = []
    for c in d.get("candidates") or []:
        rec = lookup(c["signum"])
        if not rec or c.get("p") is None or c["p"] < sure:
            continue
        if c.get("runestone") is False or not is_runestone(rec):
            continue
        rel, rr = stone_relevance(rec)
        alts = ", ".join(f"{a[0]} {round(a[1] * 100)} %" for a in (c.get("alts") or [])[:2])
        ours = (f"Luckan i '{c['carved']}' kan fyllas med '{c['fill']}', så att ordet blir {c['word']} "
                f"({round(c['p'] * 100)} % kalibrerad säkerhet)"
                + (f"; läsningen blir \"{c['reading']}\"" if c.get("reading") else "") + ".")
        out.append(_stone(_finding(rec, TEXTGAP, "nytt", ours, "Rundata lämnar ordet oåterställt", min(1.0, c["p"]), 0.7, rel,
                            {"belägg": [f"kalibrerad sannolikhet {round(c['p'] * 100)} % (modellen ensam "
                                        f"{round((c.get('p_model') or c['p']) * 100)} %)"] + ([f"alternativ: {alts}"] if alts else []),
                             "nyhet": ["Rundata har inte återställt ordet"], "relevans": rr},
                            False, gap=c, source="data/textmodel_candidates.json",
                            model_version=d.get("model_version"), runestone=True), ASSESS_TEXTGAP))
    return out


def runor_findings(lookup, inscriptions: list[dict], ctx=None) -> list[dict]:
    """Stenar som Runor 2020 anger som flyttade men som appens flyttregel räknar som stående på plats, och läsningar med
    fler säkert lästa runor. Bara svenska vikingatida runstenar.

    Rundata har ingen flyttflagga: att en sten räknas som stående på plats är appens regel (src/r_bridge.is_moved) över
    Rundatas plats och placering. Där Rundatas placeringstext nämner en annan plats än fyndplatsen (placement_elsewhere)
    säger Rundata i själva verket detsamma som Runor, och fyndet visar en lucka i regeln, inte en motsägelse
    ('stämmer'). En placeringstext som bara beskriver hur stenen står ger ingen flyttuppgift: där står Runor ensam
    ('motsäger'), med Rundatas text bland beläggen."""
    from src.r_bridge import is_moved
    runor = _load(RUNOR)
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
            rel, rr = stone_relevance(rec)
            where = x.get("original_text") or x.get("placement") or ""
            placement = (rec.get("placement") or "").strip()
            ev = ["Riksantikvarieämbetets Runor 2020 (original = nej)"] + ([f"Runor: {where}"] if where else [])
            # Fixed sentences, so that they translate; Runor's and Rundata's own notes go with the evidence
            if placement_elsewhere(rec, lookup):
                out.append(_stone(_finding(
                    rec, RUNOR_PLACE, "stämmer", "Runor 2020: stenen står inte på sin ursprungliga plats.",
                    "Rundatas placering anger var stenen står nu, men appens flyttregel räknar den som stående på plats",
                    0.8, 0.1, rel,
                    {"belägg": ev + [f"Rundata (placering): {placement}"],
                     "nyhet": ["Rundata säger detsamma i placeringstexten; appens flyttregel behöver rättas"],
                     "relevans": rr}, False, source="Runor 2020 (runor.raa.se)", rundata_placement=placement),
                    ASSESS_RUNOR_PLACE_RULE))
            else:
                out.append(_stone(_finding(
                    rec, RUNOR_PLACE, "motsäger", "Runor 2020: stenen står inte på sin ursprungliga plats.",
                    "Rundatas placeringstext anger ingen annan plats än fyndplatsen, så appens flyttregel räknar stenen "
                    "som stående på plats" if placement else
                    "Rundata anger ingen annan placering, så appens flyttregel räknar stenen som stående på plats",
                    0.8, NOVELTY_RUNOR, rel,
                    {"belägg": ev + ([f"Rundata (placering): {placement}"] if placement else []),
                     "nyhet": ["påverkar alla analyser av stenens omgivning: vatten, lämningar, landskap"],
                     "relevans": rr}, False, source="Runor 2020 (runor.raa.se)"), ASSESS_RUNOR_PLACE))
    comp = _load(RUNOR_COMPARE) or {}
    for x in comp.get("more_runes_examples") or []:
        rec = lookup(x.get("signum") or "")
        if not rec or not is_runestone(rec):
            continue
        rel, rr = stone_relevance(rec)
        out.append(_stone(_finding(rec, RUNOR_READING, "nytt", "Runor 2020 läser fler runor än Rundata.",
                                   "Rundata 2018 har en kortare läsning", 0.8, NOVELTY_RUNOR, rel,
                                   {"belägg": ["Riksantikvarieämbetets Runor 2020", f"Runor 2020: {x['runor_2020']}",
                                               f"Rundata 2018: {x['rundata_2018']}"],
                                    "nyhet": ["en nyare läsning med fler säkert lästa runor"], "relevans": rr}, False,
                                   source="Runor 2020 (runor.raa.se)", reading_runor=x["runor_2020"],
                                   reading_rundata=x["rundata_2018"]), ASSESS_RUNOR_READING))
    return out


def manual_findings(lookup, inscriptions: list[dict], ctx=None) -> list[dict]:
    """Egna fynd om enskilda stenar (data/stone_findings.json): {signum, verdict, ours, existing, evidence, novelty,
    source, date, method?}. Rader med fel eller saknade fält hoppas över (och loggas), så att ett skrivfel i filen inte
    fäller hela listan. Bara svenska vikingatida runstenar tas med (appens grundregel); ett eget fynd om ett annat föremål
    eller en sten utanför Sverige hoppas över och loggas."""
    d = _load(MANUAL) or {}
    out = []
    for i, x in enumerate(d.get("findings") or []):
        if not isinstance(x, dict):
            log.warning("stone_findings.json, rad %d: inte ett objekt – hoppas över", i)
            continue
        verdict = x.get("verdict", "nytt")
        try:
            evidence, novelty = float(x.get("evidence", 0.5)), float(x.get("novelty", 0.6))
        except (TypeError, ValueError):
            evidence = novelty = None
        problem = ("signum saknas" if not isinstance(x.get("signum"), str) or not x["signum"].strip()
                   else "ours saknas" if not isinstance(x.get("ours"), str) or not x["ours"].strip()
                   else f"okänt verdict {verdict!r} (ska vara {', '.join(VERDICTS)})" if verdict not in VERDICTS
                   else "evidence och novelty ska vara tal mellan 0 och 1"
                   if evidence is None or not (0 <= evidence <= 1 and 0 <= novelty <= 1) else None)
        if problem:
            log.warning("stone_findings.json, rad %d: %s – hoppas över", i, problem)
            continue
        rec = lookup(x["signum"])
        if not rec:
            log.warning("stone_findings.json, rad %d: %s finns inte i Rundata – hoppas över", i, x["signum"])
            continue
        if not is_runestone(rec):
            log.warning("stone_findings.json, rad %d: %s är inte en svensk vikingatida runsten – hoppas över", i, x["signum"])
            continue
        rel, rr = stone_relevance(rec)
        out.append(_stone(_finding(rec, x.get("method") or OWN, verdict, x["ours"], x.get("existing", "–"),
                                   evidence, novelty, rel,
                                   {"belägg": [x.get("evidence_text") or f"källa: {x.get('source', '–')}"], "nyhet": [],
                                    "relevans": rr}, False, source=x.get("source"), date=x.get("date"),
                                   runestone=is_runestone(rec))))
    return out


def link_findings(lookup, inscriptions: list[dict], ctx=None) -> list[dict]:
    """Stenar som delar namn med en annan sten mer än slumpen ger (data/links.json, src/linking.py), utan motsägelser i
    släktskap eller tid: troligen samma familj. Länkar som Rundata redan gör räknas som bekräftelser: parstenarna och
    stenar som Rundatas anmärkningar knyter ihop på annat sätt ('Utgör ett monument tillsammans med …', fältet
    rundata_linked i data/links.json). Varje länk ger ett fynd på var och en av de två stenarna."""
    d = _load(LINKS) or {}
    cut = d.get("fdr_cut", 0.1)
    pars = {tuple(p) for p in ((d.get("validation") or {}).get("parsten") or {}).get("pairs") or []}
    out = []
    for x in d.get("links") or []:
        if x["q"] >= cut or x.get("contradictions"):
            continue
        for this, other in ((x["a"], x["b"]), (x["b"], x["a"])):
            rec = lookup(this)
            if not rec or not is_runestone(rec):  # Swedish Viking-age runestones only, as the other kinds
                continue
            rel, rr = stone_relevance(rec)
            parsten = tuple(sorted((this, other))) in pars
            known = parsten or bool(x.get("rundata_linked"))
            where = f", {x['km']:.0f} km bort".replace(".", ",") if x.get("km") is not None else ""
            ev = max(0.0, 1 - x["q"] * 5)
            out.append(_stone(_finding(rec, LINK, "stämmer" if known else "nytt",
                                f"Delar namnen {', '.join(x['names'])} med {other}{where}: troligen samma familj.",
                                "Rundata kallar stenarna parstenar" if parsten
                                else "Rundata anger att stenarna hör ihop" if known else "Rundata länkar inte stenarna",
                                ev, 0.6, rel,
                                {"belägg": [f"andel falska länkar vid samma styrka {round(x['q'] * 100)} % (namnen blandade inom "
                                            f"landskapet), {round(x.get('q_district', 1) * 100)} % inom häradet",
                                            "släktskap och datering motsäger inte länken"],
                                 "nyhet": [] if known else ["en släktlänk mellan stenarna som Rundata inte anger"],
                                 "relevans": rr}, known, linked=other, shared=x["names"], q=x["q"])))
    return out


def all_findings(lookup, inscriptions: list[dict]) -> list[dict]:
    # ctx (carver coverage and oeuvres) is kept in the signatures for callers, but stone findings no longer use it
    return (textgap_findings(lookup, inscriptions) + runor_findings(lookup, inscriptions)
            + manual_findings(lookup, inscriptions) + link_findings(lookup, inscriptions))
