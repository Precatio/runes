"""R-analysernas resultat som fynd i Forskningsluckor.

Fynd per sten (samma bedömning som övriga fynd: stämmer / nytt / motsäger, med belägg × nyhet × relevans):

  statistisk modell (R)  attribueringsmodellens förstaval för stenar utan säker ristare, eller avvikelser
                         från Rundata. Belägget är modellens korsvaliderade träffsäkerhet vid den sannolikhet
                         den anger – inte sannolikheten själv, som är försiktig (underskattar).
  seriation (R)          tidig eller sen placering i Upplands seriation för stenar utan stilgrupp; svagt
                         belägg, eftersom tidsskattningen bara är något bättre än att gissa medelåret.
  okänd ristare (R)      stenen ingår i en grupp av stenar utan ristare som liknar varandra lika mycket som en
                         ristares stenar och inte liknar någon känd ristare i närheten (arbetsnamn efter typstenens
                         socken). Belägget är hur rena grupperna blev när metoden prövades på stenar med känd ristare.

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
ANONYMOUS = "okänd ristare (R)"


def _d(v: float, digits: int = 2) -> str:
    return f"{v:.{digits}f}".replace(".", ",")


def _pct(v: float) -> str:
    return f"{round(v * 100)} %"


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95 % konfidensintervall för en andel (Wilson); rimligt även för 20 av 20."""
    if n == 0:
        return 0.0, 1.0
    p = k / n
    den = 1 + z * z / n
    centre, half = (p + z * z / (2 * n)) / den, z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / den
    return max(0.0, centre - half), min(1.0, centre + half)


def _reliability(att: dict, p: float) -> tuple[float, str]:
    """Korsvaliderad träffsäkerhet för förstaval med minst denna sannolikhet, med 95 % konfidensintervall."""
    best = _bin(att, p)
    if not best:
        return 0.3, "modellens förstaval är osäkra vid så låg sannolikhet"
    k = round(best["accuracy"] * best["n"])
    lo, hi = wilson(k, best["n"])
    return best["accuracy"], (f"när modellen ger minst {_d(best['threshold'], 1)} till sitt förstaval har det varit rätt i "
                              f"{k} av {best['n']} korsvaliderade stenar ({_pct(best['accuracy'])}, 95 % konfidensintervall "
                              f"{_pct(lo)}–{_pct(hi)})")


def _bin(att: dict, p: float) -> dict | None:
    best = None
    for r in att["calibration"]["reliability"]:
        if p >= r["threshold"] and r.get("accuracy") is not None:
            best = r
    return best


def _bin_stats(att: dict, p: float) -> dict:
    """Antal stenar och konfidensintervall för träffsäkerheten vid modellens sannolikhet (till tolkningen)."""
    b = _bin(att, p)
    if not b:
        return {}
    k = round(b["accuracy"] * b["n"])
    lo, hi = wilson(k, b["n"])
    return {"bin_n": b["n"], "bin_correct": k, "acc_lo": round(lo, 3), "acc_hi": round(hi, 3)}


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


def model_significance(findings: list[dict], oof: list[dict]) -> None:
    """Signifikanstest för modellens förslag (max-statistik, som för ortografin): på stenar med känd ristare, som
    modellen inte såg (korsvalidering), hur ofta en felaktig ristare fick minst lika hög sannolikhet som förslaget.
    p = (1 + antal sådana stenar) / (1 + antal stenar); en sten jämförs aldrig med sig själv. Justeras med
    Benjamini–Hochberg över alla modellens förslag. Förutsätter, liksom sannolikheten, att ristaren är en av
    modellens ristare."""
    from src.stone_size import bh
    null = [(r["signum"], r["p_wrong_max"]) for r in oof if r.get("p_wrong_max") is not None]
    if not null or not findings:
        return
    pvals = []
    for f in findings:
        prob = f["stats"]["probability"]
        others = [w for sg, w in null if sg != f["signum"]]
        pvals.append((1 + sum(w >= prob for w in others)) / (1 + len(others)))
    for f, p, q in zip(findings, pvals, bh(pvals)):
        f["stats"].update({"p_value": round(p, 4), "q_value": round(q, 4), "null_n": len(null)})


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
                                {"belägg": ev, "nyhet": [nov], "relevans": rel_reasons}, True, suggested=pr["top"],
                                stats={"probability": pr["p"], "margin": round(margin, 3), "second": pr.get("second"),
                                       "accuracy": acc, **_bin_stats(att, pr["p"])}))
        elif uncertain:
            if pr["top"] in uncertain:
                out.append(_finding(rec, MODEL, "stämmer", ours, _carver_text(rec), evidence, 0.4, rel,
                                    {"belägg": ev, "nyhet": ["stöder en osäker attribuering i Rundata"],
                                     "relevans": rel_reasons}, True, suggested=pr["top"],
                                    stats={"probability": pr["p"], "margin": round(margin, 3), "accuracy": acc, **_bin_stats(att, pr["p"])}))
            else:
                signed = any(c["kind"] == "S" for c in rec["carvers"])
                if signed:
                    continue  # a signature outweighs the model
                out.append(_finding(rec, MODEL, "motsäger", ours, _carver_text(rec), evidence, 0.6, rel,
                                    {"belägg": ev, "nyhet": ["pekar på en annan ristare än Rundatas osäkra attribuering"],
                                     "relevans": rel_reasons}, True, suggested=pr["top"],
                                    stats={"probability": pr["p"], "margin": round(margin, 3), "accuracy": acc, **_bin_stats(att, pr["p"])}))
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
                            True, suggested=row["top"],
                            stats={"probability": row["p"], "p_truth": row["p_truth"], "accuracy": acc, "cross_validated": True,
                                   **_bin_stats(att, row["p"])}))
    model_significance(out, oof or [])
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


def anonymous_findings(anon: dict, lookup, inscriptions: list[dict]) -> list[dict]:
    """Stenar i grupper som kan vara en okänd ristare eller verkstad (r/anonymous.R)."""
    v = anon.get("validation") or {}
    if not v.get("purity"):
        return []
    coverage, oeuvre = _province_coverage(inscriptions), _oeuvre(inscriptions)
    out = []
    for g in anon.get("groups") or []:
        if g.get("status") != "candidate" or not g.get("name"):
            continue
        marks = "; ".join(f"{m['feature']} ({_pct(m['share_group'])} mot {_pct(m['share_area'])} i trakten)"
                          for m in (g.get("marks") or [])[:3])
        evidence = min(0.6, v["purity"]) * (g.get("stability") or 0)
        for signum in g["stones"]:
            rec = lookup(signum)
            if not rec or has_carver(rec):
                continue
            rel, rel_reasons = relevance(rec, None, coverage, oeuvre)
            ours = (f"Ingår i en grupp av {g['n']} stenar utan ristare som liknar varandra lika mycket som en ristares "
                    f"stenar – arbetsnamn {g['name']} (typsten {g['type_stone']})")
            out.append(_finding(rec, ANONYMOUS, "nytt", ours, _carver_text(rec), evidence, 0.6, rel,
                                {"belägg": [f"när metoden prövades på stenar med känd ristare bestod en grupp i genomsnitt "
                                            f"till {_pct(v['purity'])} av samma ristare, mot {_pct(v['purity_geography'])} "
                                            "för lika många närliggande stenar",
                                            f"gruppen återkommer till {_pct(g.get('stability') or 0)} när en femtedel av "
                                            "länkarna tas bort"] + ([f"utmärks av {marks}"] if marks else []),
                                 "nyhet": ["ingen ristare i Rundata, och gruppen liknar ingen känd ristare i närheten",
                                           "arbetsnamnet är en etikett för gruppen, inte en person – kontrollera mot "
                                           "litteraturen om gruppen redan är beskriven"],
                                 "relevans": rel_reasons}, True,
                                stats={"group": g["name"], "type_stone": g["type_stone"], "n": g["n"],
                                       "purity": v["purity"], "stability": g.get("stability")}))
    return out


def significance(value: float | None, kind: str = "q", test: str = "") -> dict:
    """Om ett resultat är statistiskt säkerställt: q (justerat för många test) eller p under 0,05. Utan värde finns
    inget signifikanstest (t.ex. en validerad modell eller en beskrivning), och det sägs uttryckligen."""
    if value is None:
        return {"significant": None, "test": test or "inget signifikanstest"}
    return {"significant": value < 0.05, "kind": kind, "value": value, "test": test,
            "label": f"{kind} {'< 0,001' if value < 0.001 else _d(value, 3)}"}


def finding_significance(f: dict) -> dict:
    """Signifikansen för ett fynd per sten, efter metod: ortografins p-värde justerat för att den bästa av alla
    ristare valts, huggteknikens permutationstest och modellens förslag mot de sannolikheter felaktiga ristare får
    (model_significance)."""
    st = f.get("stats") or {}
    method = f.get("method", "")
    if method in ("ortografi", "samlade belägg") and st.get("p_adjusted") is not None:
        return significance(st["p_adjusted"], "justerat p", "andel av andra ristares inskrifter som är minst lika lika, "
                                                            "justerat för att den bästa av alla ristare valts (max-statistik)")
    if method == "huggteknik" and st.get("p") is not None:
        return significance(st["p"], "p", "permutationstest på stennivå")
    if method.startswith("statistisk modell") and st.get("q_value") is not None:
        return significance(st["q_value"], "q", "andel stenar med känd ristare där modellen, utan att ha sett stenen, gav en "
                                                "felaktig ristare minst lika hög sannolikhet; Benjamini–Hochberg över modellens förslag")
    if method.startswith("statistisk modell"):
        return significance(None, test="kalibrerad sannolikhet, prövad med korsvalidering – inget signifikanstest")
    return significance(None)


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
                            "visar att det också gäller statistiskt.",
                    "significance": significance(max((c["compact_q"] for c in g["carvers"] if c.get("compact_q") is not None
                                                      and c["compact_q"] < 0.05), default=None), "q",
                                                 "permutationstest per ristare, Benjamini–Hochberg (högsta q bland de säkerställda)")})
        w = g.get("water") or {}
        if w.get("available"):
            o = w["overall"]
            out.append({"topic": "Geografi", "status": "bekräftar" if o["p"] < 0.05 else "mönster att pröva",
                        "text": f"Runstenarna står närmare vatten än slumpvisa punkter på land (median {_d(o['median_stones_km'])} "
                                f"mot {_d(o['median_random_km'])} km, p {_d(o['p'], 3) if o['p'] >= 0.001 else '< 0,001'}).",
                        "note": "Att stenar restes vid färdleder, även vattenleder, är en etablerad tolkning. Vattenlagret är grovt (1:10 milj.).",
                        "significance": significance(o["p"], "p", "Wilcoxon, ensidigt")})
            b = w.get("bridges") or {}
            if b and b.get("median_bridge_km", 0) > b.get("median_other_km", 0):
                out.append({"topic": "Geografi", "status": "begränsning",
                            "text": f"Stenar som nämner bro- eller vägbygge står längre från vattnet i kartlagret "
                                    f"(median {_d(b['median_bridge_km'])} mot {_d(b['median_other_km'])} km).",
                            "note": "Broarna gick oftast över mindre vattendrag och våtmarker som saknas i Natural Earth; "
                                    "resultatet visar kartlagrets gräns, inte att broarna låg långt från vatten.",
                            "significance": significance(b.get("p"), "p", "Wilcoxon")})
    a = res.get("attribution") or {}
    if a.get("ablation"):
        ab = {x["features"]: x for x in a["ablation"]}
        gtext = ""
        for name, g in (a.get("grouped_cv") or {}).items():
            ga = {x["features"]: x for x in g.get("ablation") or []}.get("Alla")
            if ga and ga.get("accuracy") is not None:
                gtext += f" Med hela {'socknar' if name == 'Socken' else 'härader'} utelämnade: {_pct(ga['accuracy'])}."
        out.append({"topic": "Attribuering", "status": "bekräftar",
                    "text": f"Modellen hittar rätt ristare i {_pct(ab['Alla']['accuracy'])} av fallen (bland tre främsta "
                            f"{_pct(ab['Alla']['top3'])}); språk och innehåll ensamt {_pct(ab['Språk och innehåll']['accuracy'])}, "
                            f"geografi ensamt {_pct(ab['Geografi']['accuracy'])}, mot {_pct(a['majority_baseline'])} om man "
                            "alltid gissar på den vanligaste ristaren." + gtext,
                    "note": (a.get("caveat") or "") + (" Den grupperade korsvalideringen visar hur väl modellen fungerar "
                                                       "på en plats den inte sett." if gtext else ""),
                    "significance": significance(None, test="validerad med korsvalidering i stället för ett signifikanstest")})
    t = res.get("text") or {}
    if t.get("lemmas"):
        top = t["lemmas"][0]
        out.append({"topic": "Språk", "status": "bekräftar",
                    "text": f"Stavningen av vanliga ord skiljer ristarna åt; tydligast för '{top['lemma']}' (Cramérs V "
                            f"{_d(top['cramers_v'])}).",
                    "note": "Att ristare har egna stavningsvanor är en grund för ortografisk attribuering.",
                    "significance": significance(top.get("q"), "q", "χ² med simulerat p, Benjamini–Hochberg")})
    dl = res.get("dialect") or {}
    if dl.get("mantel"):
        m = dl["mantel"]
        out.append({"topic": "Språk", "status": "bekräftar" if m["p"] < 0.05 else "mönster att pröva",
                    "text": f"Ju längre ifrån varandra två härader ligger, desto mer skiljer sig stavningen (Mantel r "
                            f"{_d(m['r'])}, p {_d(m['p'], 3)}, {dl['n_districts']} härader).",
                    "note": dl.get("caveat"), "significance": significance(m["p"], "p", "Mantel-test, 999 permutationer")})
    c = res.get("clusters") or {}
    if c.get("k"):
        out.append({"topic": "Stil och innehåll", "status": "mönster att pröva" if c["best_silhouette"] >= 0.25 else "svagt",
                    "text": f"Klustringen ger {c['k']} grupper med {c['structure']} struktur (silhuett {_d(c['best_silhouette'])}). "
                            f"Grupperna sammanfaller inte med ristarna (justerat Rand-index {_d(c['carvers']['ari'])}).",
                    "note": "Grupperna speglar främst kors, stungna runor och bön, alltså tid och kristnande snarare än ristare.",
                    "significance": significance(None, test="klustring beskriver struktur; inget signifikanstest")})
    ch = res.get("chronology") or {}
    v = ch.get("validation") or {}
    if v:
        out.append({"topic": "Datering", "status": "bekräftar" if v.get("usable") else "svagt",
                    "text": f"I Uppland ordnar seriationen av språk och innehåll stenarna i samma följd som Gräslunds "
                            f"stilkronologi (rho {_d(v['rho'])}, {_d(v['partial_rho'])} med latituden konstant), utan att "
                            "ornamentiken ingick.",
                    "note": f"Oberoende stöd för kronologin. Årtalen är osäkra: medelfel {v['mae_loo_years']} år mot "
                            f"{v['mae_naive_years']} år utan modell.",
                    "significance": significance(v.get("p"), "p", "Spearmans rangkorrelation")})
        for dim in ch.get("corpus_dimensions") or []:
            if dim["unexplained"]:
                out.append({"topic": "Datering", "status": "mönster att pröva",
                            "text": f"I hela korpusen följer CA-dimension {dim['dim']} ({_d(dim['inertia_pct'], 1)} % av inertin) "
                                    f"varken tid (rho {_d(dim['rho_time'])}) eller geografi (rho latitud {_d(dim['rho_lat'])}, "
                                    f"eta² landskap {_d(dim['eta2_province'])}). Den skiljer "
                                    f"{', '.join(dim['positive'][:3]).lower()} från {', '.join(dim['negative'][:3]).lower()}.",
                            "note": f"Sambandet med ristare är eta² {_d(dim['eta2_carver'] or 0)}. Mönstret kan vara ristarens eller "
                                    "beställarens val snarare än tid och plats; appen känner inte till någon förklaring i "
                                    "litteraturen och det bör prövas.",
                            "significance": significance(None, test="beskrivande (korrespondensanalys); inget signifikanstest")})
    nw = res.get("network") or {}
    for k in nw.get("kinship") or []:
        if k.get("q_period") is not None and k["q_period"] < 0.05 and k["n"] >= 20:
            trend = "vanligare" if (k["late"] or 0) > (k["early"] or 0) else "ovanligare"
            out.append({"topic": "Släkt och formler", "status": "mönster att pröva",
                        "text": f"Relationen '{k['relation']}' är {trend} på sena stenar (efter ca 1050: {_pct(k['late'])}, "
                                f"före: {_pct(k['early'])}; q {_d(k['q_period'], 3)}).",
                        "note": "Tidsindelningen bygger på Gräslunds stilgrupper och gäller stenar med säker stilgrupp.",
                        "significance": significance(k["q_period"], "q", "Fishers exakta test, Benjamini–Hochberg")})
    an = res.get("anonymous") or {}
    if an.get("groups"):
        v = an["validation"]; cands = [g for g in an["groups"] if g["status"] == "candidate"]
        out.append({"topic": "Okända ristare", "status": "mönster att pröva",
                    "text": f"{len(cands)} {'grupp' if len(cands) == 1 else 'grupper'} av stenar utan ristare "
                            f"({sum(g['n'] for g in cands)} stenar) liknar "
                            "varandra lika mycket som en ristares stenar och liknar ingen känd ristare i närheten, bland "
                            "dem " + ", ".join(f"{g['name']} ({g['n']} stenar)" for g in cands[:4]) + ". "
                            f"{len(an['groups']) - len(cands)} andra grupper liknar en känd ristare.",
                    "note": f"Prövat på stenar med känd ristare bestod en grupp i genomsnitt till {_pct(v['purity'])} av "
                            f"samma ristare, mot {_pct(v['purity_geography'])} för lika många närliggande stenar. En grupp "
                            "kan vara en ristare, en verkstad eller en lokal tradition; arbetsnamnen är etiketter, inte "
                            "personer, och grupperna kan redan vara beskrivna i litteratur som appen inte har.",
                    "significance": significance(None, test="validerad på stenar med känd ristare i stället för ett signifikanstest")})
    out += change_patterns(res.get("change") or {})
    return out


SHAPE_TEXT = {"rises": "blir vanligare över tid", "falls": "blir ovanligare över tid",
              "peak": "är vanligast omkring {y}", "trough": "är ovanligast omkring {y}", "flat": "förändras knappt"}
CHANGE_NOTE = ("Tiden bygger på Gräslunds stilgrupper (intervall, inte år) och gäller daterade stenar, främst i Uppland "
               "och Södermanland. Stavning kan spegla skrivtradition och ristarens skola lika mycket som uttal.")


def _q(q: float) -> str:
    return "< 0,001" if q < 0.001 else _d(q, 3)


def change_patterns(ch: dict) -> list[dict]:
    """Mönster ur förändringsmodulen (r/change.R): drag som förändras över tid, skillnader mellan landskap och
    bro- och vägstenarnas kristna drag. Bara Holm-justerade resultat under 0,05."""
    out = []
    for f in ch.get("features") or []:
        t = f.get("time") or {}
        if t.get("tested") and t.get("q") is not None and t["q"] < 0.05:
            dr = t.get("draws") or {}
            robust = (f" {round((dr.get('share_sig') or 0) * dr['n'])} av {dr['n']} omräkningar med årtal dragna inom "
                      "stilgruppernas intervall gav också ett säkerställt samband." if dr.get("n") else "")
            known = f["key"] == "stungna" and t["shape"] == "rises"
            out.append({"topic": "Förändring", "status": "bekräftar" if known else "mönster att pröva",
                        "text": f"{f['label']} {SHAPE_TEXT[t['shape']].format(y=t.get('peak_year'))}, med plats och ristare "
                                f"konstanta: {_pct(t['first'])} omkring {t['year_first']} och {_pct(t['last'])} omkring "
                                f"{t['year_last']} (q {_q(t['q'])}).{robust}",
                        "note": ("Att stungna runor blir vanligare under 1000-talet stämmer med den gängse bilden (se t.ex. "
                                 "Lagman 1990); här prövat med plats och ristare konstanta. " if known else "") + CHANGE_NOTE,
                        "significance": significance(t["q"], "q", "logistisk regression (mgcv), Holm")})
        pv = f.get("provinces") or {}
        rows = pv.get("rows") or []
        if len(rows) >= 2 and pv.get("p_differ") is not None and pv["p_differ"] < 0.01:
            hi = max(rows, key=lambda r: r["share1050"]); lo = min(rows, key=lambda r: r["share1050"])
            cross = [r for r in rows if r.get("cross_year")]
            ctext = (" Draget passerar hälften av stenarna " + ", ".join(
                f"omkring {r['cross_year']} i {r['province']}" for r in sorted(cross, key=lambda r: r["cross_year"])) + "."
                     if len(cross) >= 2 else "")
            out.append({"topic": "Förändring", "status": "mönster att pröva",
                        "text": f"{f['label']}: omkring år 1050 skiljer sig landskapen (p {_q(pv['p_differ'])}), från "
                                f"{_pct(hi['share1050'])} i {hi['province']} till {_pct(lo['share1050'])} i {lo['province']} "
                                f"för en typisk ristare.{ctext}",
                        "note": "Landskap med minst 25 daterade stenar. Ett landskap där draget tidigt är vanligt kan vara "
                                "där förändringen började, men också där en ristarskola hade sina vanor. " + CHANGE_NOTE,
                        "significance": significance(pv["p_differ"], "p", "Wald-test")})
    for a in ch.get("assoc") or []:
        al = a.get("all") or {}
        if al.get("q") is not None and al["q"] < 0.05:
            out.append({"topic": "Förändring", "status": "mönster att pröva",
                        "text": f"{a['label']}: {_pct(a['share_x'])} mot {_pct(a['share_other'])} på andra stenar "
                                f"(oddskvot {_d(al['or'])}, 95 % KI {_d(al['lo'])}–{_d(al['hi'])}, q {_q(al['q'])}), med plats "
                                "och ristare konstanta.",
                        "note": "Prövar tolkningen av brobyggen som kristna själagåvor. Brostenarna är få (omkring 110).",
                        "significance": significance(al["q"], "q", "logistisk regression (mgcv), Holm")})
    return out
