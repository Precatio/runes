"""R-analysernas resultat som fynd i Forskningsluckor.

Fynd per sten (samma bedömning som övriga fynd: stämmer / nytt / motsäger, med belägg × nyhet × relevans):

  statistisk modell (R)  attribueringsmodellens förstaval för stenar utan säker ristare, eller avvikelser
                         från Rundata. Belägget är modellens korsvaliderade träffsäkerhet vid den sannolikhet
                         den anger – inte sannolikheten själv, som är försiktig (underskattar).
  seriation (R)          tidig eller sen placering i Upplands seriation för stenar utan stilgrupp; svagt
                         belägg, eftersom tidsskattningen bara är något bättre än att gissa medelåret.

Mönster i korpusen (geografi, dialekter, formler, klustring, seriation) redovisas separat och märks
"bekräftar" när de stämmer med vad forskningen redan utgår från (ristare arbetade regionalt, stavningen
varierar geografiskt, Gräslunds kronologi) och "mönster att pröva" när appen inte kan knyta dem till tid,
geografi eller något den känner till ur litteraturen. Appen känner bara till Rundata, Axelson (1993) och
Gräslund (1998); ett "mönster att pröva" kan alltså vara beskrivet i litteratur som appen inte har.
"""
from __future__ import annotations

from src.findings import _carver_text, _finding, _oeuvre, _province_coverage, relevance
from src.research_gaps import AXELSON_PROVINCES, has_carver, province

MODEL = "statistisk modell (R)"
SERIATION = "seriation (R)"


def _d(v: float, digits: int = 2) -> str:
    return f"{v:.{digits}f}".replace(".", ",")


def _pct(v: float) -> str:
    return f"{round(v * 100)} %"


def _reliability(att: dict, p: float) -> tuple[float, str]:
    """Korsvaliderad träffsäkerhet för förstaval med minst denna sannolikhet."""
    best = None
    for r in att["calibration"]["reliability"]:
        if p >= r["threshold"] and r.get("accuracy") is not None:
            best = r
    if not best:
        return 0.3, "modellens förstaval är osäkra vid så låg sannolikhet"
    return best["accuracy"], (f"när modellen ger minst {_d(best['threshold'], 1)} till sitt förstaval är det rätt i "
                              f"{_pct(best['accuracy'])} av fallen ({best['n']} korsvaliderade stenar)")


CIRCULARITY = ("träningsdata är Rundatas attribueringar, i Mälardalen främst Axelsons (1993), som själv vägde in "
               "stil, stavning och geografi")


def _closed_set_share(inscriptions: list[dict], carvers: set[str]) -> dict[str, float]:
    """Per landskap: andelen runstenar med säker ristare där ristaren är en av modellens."""
    from collections import Counter
    from src.research_gaps import certain_carvers, is_runestone
    tot, hit = Counter(), Counter()
    for r in inscriptions:
        cs = certain_carvers(r)
        if is_runestone(r) and cs:
            tot[province(r)] += 1
            hit[province(r)] += any(c in carvers for c in cs)
    return {p: hit[p] / tot[p] for p in tot}


def model_findings(att: dict, lookup, inscriptions: list[dict], oof: list[dict] | None = None,
                   min_p: float = 0.5) -> list[dict]:
    coverage, oeuvre = _province_coverage(inscriptions), _oeuvre(inscriptions)
    in_model = set(att.get("carvers") or [])
    closed = _closed_set_share(inscriptions, in_model)
    out = []
    for pr in att.get("predictions") or []:
        if pr["p"] < min_p:
            continue
        rec = lookup(pr["signum"])
        if not rec:
            continue
        listed = [c["name"] for c in rec["carvers"] if c["kind"] in ("S", "A")]
        # The model can only choose among its own carvers; a stone by someone else says nothing about the model
        if listed and not any(n in in_model for n in listed):
            continue
        acc, acc_text = _reliability(att, pr["p"])
        margin = pr["p"] - (pr.get("p2") or 0)
        share = closed.get(province(rec), 0.0)
        evidence = acc * min(1.0, 0.5 + margin) * (share if not listed else 1.0)
        ours = (f"Modellen föreslår {pr['top']} (sannolikhet {_d(pr['p'])}; därefter {pr['second']} {_d(pr['p2'])})")
        ev = [acc_text, f"marginal {_d(margin)} till nästa ristare", CIRCULARITY,
              f"närmaste träningssten {_d(pr['near_km'], 1)} km bort"]
        if not listed:
            ev.append(f"modellen väljer bara bland sina {len(in_model)} ristare; de har ristat {_pct(share)} av de "
                      f"attribuerade runstenarna i landskapet")
        rel, rel_reasons = relevance(rec, pr["top"], coverage, oeuvre)
        uncertain = [c for c in (pr.get("rundata_uncertain") or "").split(";") if c]
        if not has_carver(rec):
            novelty = 0.85 if province(rec) in AXELSON_PROVINCES else 0.55
            nov = ("Axelson (1993) attribuerade inte stenen" if province(rec) in AXELSON_PROVINCES
                   else "attribueringar utanför Mälardalen kan finnas i litteraturen utan att stå i Rundata")
            out.append(_finding(rec, MODEL, "nytt", ours, _carver_text(rec), evidence, novelty, rel,
                                {"belägg": ev, "nyhet": [nov], "relevans": rel_reasons}, True, suggested=pr["top"]))
        elif uncertain:
            if pr["top"] in uncertain:
                out.append(_finding(rec, MODEL, "stämmer", ours, _carver_text(rec), evidence, 0.4, rel,
                                    {"belägg": ev, "nyhet": ["stöder en osäker attribuering i Rundata"],
                                     "relevans": rel_reasons}, True, suggested=pr["top"]))
            else:
                signed = any(c["kind"] == "S" for c in rec["carvers"])
                if signed:
                    continue  # a signature outweighs the model
                out.append(_finding(rec, MODEL, "motsäger", ours, _carver_text(rec), evidence, 0.6, rel,
                                    {"belägg": ev, "nyhet": ["pekar på en annan ristare än Rundatas osäkra attribuering"],
                                     "relevans": rel_reasons}, True, suggested=pr["top"]))
    # Stones with a certain carver: out-of-fold predictions that disagree with Rundata
    for row in oof or []:
        if row["p"] < min_p or row["top"] == row["carver"]:
            continue
        rec = lookup(row["signum"])
        if not rec:
            continue
        acc, acc_text = _reliability(att, row["p"])
        signed = any(c["kind"] == "S" and c["name"] == row["carver"] for c in rec["carvers"])
        novelty, nov = ((0.05, "stenen är signerad – avvikelsen talar mot modellen, inte mot ristaren") if signed
                        else (0.6, "ifrågasätter en attribuering (A) i litteraturen"))
        rel, rel_reasons = relevance(rec, row["top"], coverage, oeuvre)
        out.append(_finding(rec, MODEL, "motsäger",
                            f"Modellen (som inte såg stenen) föreslår {row['top']} ({_d(row['p'])}); "
                            f"{row['carver']} får {_d(row['p_truth'])}",
                            _carver_text(rec), acc * 0.8, novelty, rel,
                            {"belägg": [acc_text, "korsvaliderad: stenen ingick inte i den modell som bedömde den",
                                        CIRCULARITY], "nyhet": [nov], "relevans": rel_reasons},
                            True, suggested=row["top"]))
    return out


def seriation_findings(chron: dict, stones: list[dict], lookup, inscriptions: list[dict],
                       tail: float = 0.15) -> list[dict]:
    """Stenar utan stilgrupp som seriationen placerar tydligt tidigt eller sent (Uppland)."""
    v = chron.get("validation") or {}
    if not v.get("usable"):
        return []
    coverage, oeuvre = _province_coverage(inscriptions), _oeuvre(inscriptions)
    scores = sorted(s["score"] for s in stones)
    n = len(scores)
    out = []
    gain = max(0.0, (v["mae_naive_years"] - v["mae_loo_years"]) / max(1, v["mae_naive_years"]))
    for s in stones:
        if s["dated_by_style"]:
            continue
        pct = sum(1 for x in scores if x <= s["score"]) / n
        if tail < pct < 1 - tail:
            continue
        rec = lookup(s["signum"])
        if not rec:
            continue
        early = pct <= tail
        ours = (f"Seriationen placerar stenen bland de {_pct(pct if early else 1 - pct)} "
                f"{'tidigaste' if early else 'senaste'} i Uppland (skattat ca {s['est']}, 80 % intervall "
                f"{s['lo']}–{s['hi']})")
        evidence = min(0.6, abs(v["rho"])) * (0.5 + gain)
        rel, rel_reasons = relevance(rec, None, coverage, oeuvre)
        out.append(_finding(rec, SERIATION, "nytt", ours, "ingen stilgrupp i Rundata", evidence, 0.6, rel,
                            {"belägg": [f"seriationen följer Gräslunds kronologi med rho {_d(v['rho'])}",
                                        f"tidsskattningens medelfel {v['mae_loo_years']} år mot {v['mae_naive_years']} år "
                                        "om man gissar medelåret – ordningen är säkrare än årtalet"],
                             "nyhet": ["stenen saknar stilgrupp och därmed datering i Rundata"],
                             "relevans": rel_reasons}, True))
    return out


def corpus_patterns(res: dict) -> list[dict]:
    """Mönster i hela korpusen, märkta 'bekräftar' eller 'mönster att pröva'."""
    out = []
    g = res.get("geography") or {}
    if g.get("carvers"):
        n = len(g["carvers"])
        out.append({"topic": "Geografi", "status": "bekräftar",
                    "text": f"{g['n_compact']} av {n} ristare med minst {g['min_inscriptions']} säkra stenar arbetade inom ett "
                            "mindre område än slumpvisa stenar ur samma landskap (permutationstest, q < 0,05).",
                    "note": "Att ristare var regionalt verksamma är en grund för Axelsons attribueringar; resultatet "
                            "visar att det också gäller statistiskt."})
        w = g.get("water") or {}
        if w.get("available"):
            o = w["overall"]
            out.append({"topic": "Geografi", "status": "bekräftar" if o["p"] < 0.05 else "mönster att pröva",
                        "text": f"Runstenarna står närmare vatten än slumpvisa punkter på land (median {_d(o['median_stones_km'])} "
                                f"mot {_d(o['median_random_km'])} km, p {_d(o['p'], 3) if o['p'] >= 0.001 else '< 0,001'}).",
                        "note": "Att stenar restes vid färdleder, även vattenleder, är en etablerad tolkning. Vattenlagret är grovt (1:10 milj.)."})
            b = w.get("bridges") or {}
            if b and b.get("median_bridge_km", 0) > b.get("median_other_km", 0):
                out.append({"topic": "Geografi", "status": "begränsning",
                            "text": f"Stenar som nämner bro- eller vägbygge står längre från vattnet i kartlagret "
                                    f"(median {_d(b['median_bridge_km'])} mot {_d(b['median_other_km'])} km).",
                            "note": "Broarna gick oftast över mindre vattendrag och våtmarker som saknas i Natural Earth; "
                                    "resultatet visar kartlagrets gräns, inte att broarna låg långt från vatten."})
    a = res.get("attribution") or {}
    if a.get("ablation"):
        ab = {x["features"]: x for x in a["ablation"]}
        out.append({"topic": "Attribuering", "status": "bekräftar",
                    "text": f"Modellen hittar rätt ristare i {_pct(ab['Alla']['accuracy'])} av fallen (bland tre främsta "
                            f"{_pct(ab['Alla']['top3'])}); språk och innehåll ensamt {_pct(ab['Språk och innehåll']['accuracy'])}, "
                            f"geografi ensamt {_pct(ab['Geografi']['accuracy'])}, mot {_pct(a['majority_baseline'])} om man "
                            "alltid gissar på den vanligaste ristaren.",
                    "note": a.get("caveat")})
    t = res.get("text") or {}
    if t.get("lemmas"):
        top = t["lemmas"][0]
        out.append({"topic": "Språk", "status": "bekräftar",
                    "text": f"Stavningen av vanliga ord skiljer ristarna åt; tydligast för '{top['lemma']}' (Cramérs V "
                            f"{_d(top['cramers_v'])}).",
                    "note": "Att ristare har egna stavningsvanor är en grund för ortografisk attribuering."})
    dl = res.get("dialect") or {}
    if dl.get("mantel"):
        m = dl["mantel"]
        out.append({"topic": "Språk", "status": "bekräftar" if m["p"] < 0.05 else "mönster att pröva",
                    "text": f"Ju längre ifrån varandra två härader ligger, desto mer skiljer sig stavningen (Mantel r "
                            f"{_d(m['r'])}, p {_d(m['p'], 3)}, {dl['n_districts']} härader).",
                    "note": dl.get("caveat")})
    c = res.get("clusters") or {}
    if c.get("k"):
        out.append({"topic": "Stil och innehåll", "status": "mönster att pröva" if c["best_silhouette"] >= 0.25 else "svagt",
                    "text": f"Klustringen ger {c['k']} grupper med {c['structure']} struktur (silhuett {_d(c['best_silhouette'])}). "
                            f"Grupperna sammanfaller inte med ristarna (justerat Rand-index {_d(c['carvers']['ari'])}).",
                    "note": "Grupperna speglar främst kors, stungna runor och bön, alltså tid och kristnande snarare än ristare."})
    ch = res.get("chronology") or {}
    v = ch.get("validation") or {}
    if v:
        out.append({"topic": "Datering", "status": "bekräftar" if v.get("usable") else "svagt",
                    "text": f"I Uppland ordnar seriationen av språk och innehåll stenarna i samma följd som Gräslunds "
                            f"stilkronologi (rho {_d(v['rho'])}, {_d(v['partial_rho'])} med latituden konstant), utan att "
                            "ornamentiken ingick.",
                    "note": f"Oberoende stöd för kronologin. Årtalen är osäkra: medelfel {v['mae_loo_years']} år mot "
                            f"{v['mae_naive_years']} år utan modell."})
        for dim in ch.get("corpus_dimensions") or []:
            if dim["unexplained"]:
                out.append({"topic": "Datering", "status": "mönster att pröva",
                            "text": f"I hela korpusen följer CA-dimension {dim['dim']} ({_d(dim['inertia_pct'], 1)} % av inertin) "
                                    f"varken tid (rho {_d(dim['rho_time'])}) eller geografi (rho latitud {_d(dim['rho_lat'])}, "
                                    f"eta² landskap {_d(dim['eta2_province'])}). Den skiljer "
                                    f"{', '.join(dim['positive'][:3]).lower()} från {', '.join(dim['negative'][:3]).lower()}.",
                            "note": f"Sambandet med ristare är eta² {_d(dim['eta2_carver'] or 0)}. Mönstret kan vara ristarens eller "
                                    "beställarens val snarare än tid och plats; appen känner inte till någon förklaring i "
                                    "litteraturen och det bör prövas."})
    nw = res.get("network") or {}
    for k in nw.get("kinship") or []:
        if k.get("q_period") is not None and k["q_period"] < 0.05 and k["n"] >= 20:
            trend = "vanligare" if (k["late"] or 0) > (k["early"] or 0) else "ovanligare"
            out.append({"topic": "Släkt och formler", "status": "mönster att pröva",
                        "text": f"Relationen '{k['relation']}' är {trend} på sena stenar (efter ca 1050: {_pct(k['late'])}, "
                                f"före: {_pct(k['early'])}; q {_d(k['q_period'], 3)}).",
                        "note": "Tidsindelningen bygger på Gräslunds stilgrupper och gäller stenar med säker stilgrupp."})
    return out
