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

import math

from src.findings import _carver_text, _finding, _oeuvre, _province_coverage, relevance
from src.research_gaps import AXELSON_PROVINCES, has_carver, province
from src.stats import wilson

MODEL = "statistisk modell (R)"
SERIATION = "seriation (R)"
ANONYMOUS = "okänd ristare (R)"


def _d(v: float, digits: int = 2) -> str:
    return f"{v:.{digits}f}".replace(".", ",")


def _pct(v: float | None) -> str:
    return "–" if v is None else f"{round(v * 100)} %"


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
    for f, p, q in zip(findings, pvals, bh(pvals), strict=False):
        f["stats"].update({"p_value": round(p, 4), "q_value": round(q, 4), "null_n": len(null)})


def model_findings(att: dict, lookup, inscriptions: list[dict], oof: list[dict] | None = None,
                   min_p: float = 0.5) -> list[dict]:
    coverage, oeuvre = _province_coverage(inscriptions), _oeuvre(inscriptions)
    in_model = set(att.get("carvers") or [])
    closed = _closed_set_share(inscriptions, in_model)
    out = []
    for pr in att.get("predictions") or []:
        if pr["p"] < min_p or pr.get("someone_else"):  # "någon annan": no name to suggest
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
            ev.append("träffsäkerheten är mätt på stenar av modellens egna ristare; hur modellen beter sig på stenar av "
                      "andra ristare (t.ex. namnlösa) är inte mätt, och just då är ett högt förstaval mest missvisande")
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
        evidence = min(0.6, v["purity"]) * min(g.get("stability") or 0, g.get("robust_no_time") if g.get("robust_no_time") is not None else 1)
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
                                            "länkarna tas bort och till "
                                            f"{_pct(g.get('robust_no_time') or 0)} när dragen som följer tiden tas bort"]
                                           + ([f"utmärks av {marks}"] if marks else []),
                                 "nyhet": ["ingen ristare i Rundata, och gruppen liknar ingen känd ristare i närheten",
                                           "metoden är prövad där ristare är kända (nästan bara Uppland och Södermanland), "
                                           "inte i det här landskapet",
                                           "arbetsnamnet är en etikett för gruppen, inte en person – kontrollera mot "
                                           "litteraturen om gruppen redan är beskriven"],
                                 "relevans": rel_reasons}, True,
                                stats={"group": g["name"], "type_stone": g["type_stone"], "n": g["n"],
                                       "purity": v["purity"], "stability": g.get("stability")}))
    return out


def significance(value: float | None, kind: str = "q", test: str = "") -> dict:
    """Om ett resultat är statistiskt signifikant: q (justerat för många test) eller p under 0,05. Utan värde finns
    inget signifikanstest (t.ex. en validerad modell eller en beskrivning), och det sägs uttryckligen."""
    if value is None:
        return {"significant": None, "test": test or "inget signifikanstest"}
    return {"significant": value < 0.05, "kind": kind, "value": value, "test": test,
            "label": f"{kind} {'< 0,001' if value < 0.001 else _d(value, 3)}"}


def finding_significance(f: dict) -> dict:
    """Signifikansen för ett fynd per sten, efter metod: ortografins p-värde justerat för att den bästa av alla
    ristare valts, huggteknikens permutationstest och modellens förslag mot de sannolikheter felaktiga ristare får
    (model_significance) samt släktlänkarnas andel falska länkar i nollmodellen (q, src/linking.py)."""
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
    from src.stone_findings import LINK
    if method == LINK and f.get("q") is not None:
        return significance(f["q"], "q", "andel falska länkar vid samma styrka i nollmodellen (namnen blandade inom "
                                         "landskapet)")
    return significance(None)


def _pole(label: str) -> str:
    """'Kristen bön: nej' -> 'utan kristen bön'; 'Resarformel: gjorde' -> 'med resarformel gjorde'."""
    trait, _, value = label.partition(": ")
    t = trait[:1].lower() + trait[1:]
    return f"utan {t}" if value == "nej" else f"med {t}" if value in ("ja", "") else f"med {t} {value}"


def _poles(dim: dict) -> str:
    """Vad dimensionens två ändar består av, i läsbar form."""
    def side(labels):
        return ", ".join(dict.fromkeys(_pole(x) for x in labels[:3]))
    return (f"I ena änden av dimensionen ligger stenar {side(dim['positive'])}, i den andra stenar "
            f"{side(dim['negative'])}.")


def _viking_shore(v: dict, today: dict, today_provinces: list[dict] | None = None) -> list[dict]:
    """Avståndet till en grovt modellerad strandlinje omkring år 1000 (r/geography.R), mot samma slumppunkter."""
    if not v.get("n_stones") or v.get("p") is None:
        return []
    closer = v["p"] < 0.05 and v["median_stones_km"] < v["median_random_km"]
    ratio_now = today["median_stones_km"] / today["median_random_km"] if today.get("median_random_km") else None
    ratio = v["median_stones_km"] / v["median_random_km"] if v["median_random_km"] else None
    held = [r["province"] for r in v.get("provinces") or [] if r["p"] < 0.05 and r["median_stones_km"] < r["median_random_km"]]
    tested = [r["province"] for r in v.get("provinces") or []]
    p_txt = _d(v["p"], 3) if v["p"] >= 0.001 else "< 0,001"
    text = (f"Mot en modellerad strandlinje omkring år 1000 står runstenarna {'närmare' if closer else 'inte närmare'} "
            f"vatten än slumpvisa punkter i samma landskap (median {_d(v['median_stones_km'])} mot "
            f"{_d(v['median_random_km'])} km, p {p_txt}; {v['n_stones']} stenar).")
    if ratio is not None and ratio_now is not None:
        text += (f" Stenarnas avstånd är {_pct(ratio)} av slumppunkternas, mot {_pct(ratio_now)} med dagens vatten"
                 + (" – närheten blir tydligare med dåtidens strand." if ratio < ratio_now - 0.02 else
                    " – ungefär samma närhet som med dagens vatten." if abs(ratio - ratio_now) <= 0.02 else
                    " – närheten blir svagare med den modellerade stranden."))
    if tested:
        text += f" Håller i {len(held)} av {len(tested)} landskap" + (f" ({', '.join(held)})." if held else ".")
    # The province with the most stones where it holds: stones' distance as a share of the random points', today and
    # c. AD 1000 (not the largest shift, which in flat land with little uplift can come from the terrain model's error)
    now = {r["province"]: r for r in today_provinces or [] if r.get("median_random_km")}
    rows = [r for r in v.get("provinces") or [] if r["province"] in held and r["province"] in now and r.get("median_random_km")]
    if rows:
        r = max(rows, key=lambda x: x["n"])
        a = now[r["province"]]["median_stones_km"] / now[r["province"]]["median_random_km"]
        b = r["median_stones_km"] / r["median_random_km"]
        text += f" I {r['province']} ({r['n']} stenar): {_pct(a)} med dagens vatten, {_pct(b)} omkring år 1000."
    note = ("Strandlinjen är grov: dagens höjd (terrängmodell med omkring 300 m upplösning) under landskapets "
            "landhöjning sedan omkring år 1000 (omkring fem meter i Mälardalen, mer i norr och nära noll i Skåne) räknas "
            "som hav, tillsammans med dagens sjöar och vattendrag. Höjdmodellens noggrannhet (några meter) är av samma "
            "storleksordning som landhöjningen, särskilt i flack terräng och där landhöjningen är liten (Öland, Småland). "
            "Låglänta inlandsområden kan räknas som hav, och igenslamning och dämning ingår inte. SGU:s strandförskjutningsmodell och en finare höjdmodell skulle ge en "
            "säkrare strand. Stenar i par räknas var för sig, så p-värdet blir något för litet.")
    return [{"key": "water_viking", "topic": "Geografi", "status": "mönster att pröva" if closer else "begränsning",
             "text": text, "note": note,
             "significance": significance(v["p"], "p", "Wilcoxon, ensidigt, mot samma lokala slumppunkter")}]


def _remains(r: dict) -> list[dict]:
    """Runstenarna bland Kulturmiljöregistrets lämningar (r/remains.R): gravfält och högar, vägar och broar."""
    if not r.get("available") or not r.get("distances"):
        return []
    dist = {x["key"]: x for x in r["distances"]}
    tests = r.get("tests") or {}
    m = round((r.get("near_km") or 0.5) * 1000)
    out = []
    g, h = dist.get("gravfalt"), dist.get("hog")
    if g and g.get("q_bh") is not None:
        closer = g["q_bh"] < 0.05 and g["near_stones"] > g["near_random"]
        text = (f"{_pct(g['near_stones'])} av runstenarna står inom {m} m från ett registrerat gravfält, mot "
                f"{_pct(g['near_random'])} av slumpvisa punkter på land i samma trakter (median {_d(g['median_stones_km'])} "
                f"mot {_d(g['median_random_km'])} km).")
        if h:
            text += f" Inom {m} m från en hög: {_pct(h['near_stones'])} mot {_pct(h['near_random'])}."
        provs = [p["province"] for p in r.get("gravfalt_provinces") or [] if p["p"] < 0.05 and p["near_stones"] > p["near_random"]]
        if provs:
            text += f" Gäller i {', '.join(provs)}."
        tg, cg = tests.get("time_gravfalt") or {}, tests.get("christian_gravfalt") or {}
        same_time = tg.get("q_bh") is not None and tg["q_bh"] >= 0.05
        same_christ = cg.get("q_bh") is not None and cg["q_bh"] >= 0.05
        if same_time and tg.get("periods"):
            text += (f" Närheten består över tiden (före omkring 1050 {_pct(tg['periods']['early'])}, efter "
                     f"{_pct(tg['periods']['late'])})")
            text += " och är lika stor för stenar med kristna markörer." if same_christ else "."
        note = ((r.get("note") or "") + " Att runstenar ofta står vid gravfält är känt sedan länge; det nya är att "
                "närheten kan mätas mot slumpen i hela korpusen, per landskap, över tiden och för kristna stenar. "
                "Kulturmiljöregistret kan i enstaka fall ha registrerat ett gravfält just där en runsten står.")
        out.append({"key": "remains_graves", "topic": "Geografi", "status": "bekräftar" if closer else "begränsning",
                    "text": text, "note": note,
                    "significance": significance(g["q_bh"], "q", "Wilcoxon, ensidigt, mot lokala slumppunkter, Benjamini–Hochberg")})
    bv = tests.get("bridge_vag") or {}
    if bv.get("or") is not None and bv.get("q_bh") is not None:
        found = bv["q_bh"] < 0.05 and bv["or"] > 1
        rep = (bv.get("halves") or {}).get("replicated")
        v = dist.get("vag") or {}
        text = (f"Stenar som nämner bro- eller vägbygge står {'oftare' if found else 'inte oftare'} inom {m} m från en "
                f"registrerad färdväg än andra stenar (oddskvot {_d(bv['or'])}, {_d(bv['lo'])}–{_d(bv['hi'])}, med "
                f"landskapet konstant).")
        if v:
            text += (f" Alla runstenar: {_pct(v['near_stones'])} inom {m} m från en färdväg, mot {_pct(v['near_random'])} "
                     "av slumppunkterna.")
        if rep is not None:
            text += " Håller i båda halvorna av korpusen, uppdelad per socken." if rep else \
                " Håller inte i båda halvorna av korpusen."
        note = ((r.get("note") or "") + " Färdvägarna i registret är mest hålvägar, vägbankar och äldre vägsträckningar, "
                "ofta odaterade och många yngre än stenarna; att brostenarna ändå står nära dem talar för att vägarna "
                "följer äldre stråk. Registrerade broar är oftast medeltida eller yngre.")
        status = ("mönster att pröva" if rep else "indikation") if found else "begränsning"
        out.append({"key": "remains_bridges", "topic": "Geografi", "status": status, "text": text, "note": note,
                    "replicated": rep if found else None,
                    "significance": significance(bv["q_bh"], "q", "logistisk regression med landskapet konstant, Benjamini–Hochberg")})
    return out


def _cult(c: dict, scan: dict | None = None) -> list[dict]:
    """Kristna budskap nära ortnamn som kan tyda på förkristen kult, och kyrkor nära samma namn (r/remains.R). Med
    genomsökningen (scan) jämförs radieprovet med avståndsmodellen utan vald radie."""
    if not c.get("available") or not c.get("tests"):
        return []
    cells = {(x["feature"], x["kind"]): x for x in (scan or {}).get("cells") or []}
    t = c["tests"]
    km = c.get("near_km") or 2
    out = []
    pa = t.get("prayer_a") or {}
    if pa.get("or") is not None and pa.get("q_bh") is not None:
        found = pa["q_bh"] < 0.05 and pa["or"] > 1
        rep = (pa.get("halves") or {}).get("replicated")
        text = (f"Kristen bön är {'vanligare' if found else 'inte tydligt vanligare'} på runstenar inom {km} km från ett "
                f"teoforiskt ortnamn (ett gudanamn med en sakral efterled, som Torsvi, Odensala, Ullevi och Frösö): "
                f"{_pct(pa['share_near'])} mot {_pct(pa['share_far'])} av övriga stenar (oddskvot {_d(pa['or'])}, "
                f"{_d(pa['lo'])}–{_d(pa['hi'])}, med landskapet konstant; {pa['n_near']} stenar vid "
                f"{pa.get('n_places', '–')} namn).")
        if rep is not None:
            text += " Håller i båda halvorna av korpusen, uppdelad per socken." if rep else \
                " Håller inte i båda halvorna av korpusen."
        pc, pac = t.get("prayer_central") or {}, t.get("prayer_a_central") or {}
        if pc.get("or") is not None:
            text += (f" Vid centralortsnamn utan kult (Husby, -tuna) är bönen inte vanligare (oddskvot {_d(pc['or'])})"
                     + (f", och med närheten till dem konstant består skillnaden vid de teofora namnen (oddskvot "
                        f"{_d(pac['or'])})." if pac.get("or") is not None else "."))
        ca = t.get("christian_a") or {}
        if ca.get("or") is not None:
            text += (f" Kristna markörer överlag ({_pct(ca['share_near'])} mot {_pct(ca['share_far'])}) och kors pekar åt "
                     "samma håll men håller inte i alla kontroller." if not (ca.get("halves") or {}).get("replicated")
                     else f" Kristna markörer överlag: {_pct(ca['share_near'])} mot {_pct(ca['share_far'])}.")
        radius = {r["km"]: r for r in c.get("radius") or []}
        loo = pa.get("loo") or {}
        pagan = c.get("pagan") or []
        pagan_txt = ""
        if pagan:
            near = [x["signum"] for x in pagan if x.get("km_a") is not None and x["km_a"] < km]
            pagan_txt = (f" De {len(pagan)} stenarna med uttryckligt hedniska markörer (Torsåkallan, vígi-formler, Tormotiv) "
                         + (f"står inom {km} km från ett teoforiskt namn i {len(near)} fall: {', '.join(near)}."
                            if near else f"står inte inom {km} km från något teoforiskt namn i registret."))
        note = (f"Radien {km} km valdes i förväg. "
                + (f"Med 1 km ({radius[1]['n_near']} stenar) är oddskvoten {_d(radius[1]['or'])} och med 3 km "
                   f"{_d(radius[3]['or'])}, åt samma håll men inte signifikant; resultatet hänger alltså delvis på radien. "
                   if 1 in radius and 3 in radius else "")
                + (f"Utan stenarna vid ett namn i taget ligger oddskvoten mellan {_d(loo['min_or'])} och "
                   f"{_d(loo['max_or'])}. " if loo else "")
                + "Ortnamnen kommer ur OpenStreetMap (Lantmäteriets namn) och är belagda långt efter vikingatiden; att ett "
                "gudanamn med sakral efterled betecknar en kultplats är den gängse tolkningen (Vikstrand 2001), men ortens läge "
                "är dagens by eller gård, inte kultplatsen själv. Flyttade stenar räknas inte. Teofora namn markerar ofta "
                "centralorter; jämförelsen med Husby och -tuna prövar den förklaringen." + pagan_txt)
        sb = cells.get(("bon", "cult_a"))
        if sb:
            strong = [x for x in cells.values() if x["q_bh"] < 0.05 and (x.get("halves") or {}).get("replicated")
                      and x["feature"] in ("kristen", "kors", "bon", "sjal")]
            note += (f" I genomsökningen av landskapet, där avståndet används utan vald radie, är sambandet mellan bön och "
                     f"teofora namn {'svagare' if not (sb.get('halves') or {}).get('replicated') else 'detsamma'} "
                     f"(oddskvot {_d(sb['or'])} när avståndet halveras, q {_d(sb['q_bh'], 3)}"
                     + (", inte i båda halvorna)" if not (sb.get("halves") or {}).get("replicated") else ")")
                     + (". Starkare och stabilare är kristna markörer nära centralortsnamn och böner nära medeltida kyrkor"
                        " – det talar för att eliten och de tidiga kyrkorna förklarar en del av mönstret."
                        if any(x["kind"] in ("central", "church") for x in strong) else "."))
        status = ("mönster att pröva" if rep else "indikation") if found else "begränsning"
        out.append({"key": "cult_prayer", "topic": "Geografi", "status": status, "text": text, "note": note,
                    "replicated": rep if found else None,
                    "significance": significance(pa["q_bh"], "q", "logistisk regression med landskapet konstant, "
                                                                   "Benjamini–Hochberg")})
    ch = c.get("churches") or {}
    a = next((r for r in ch.get("rows") or [] if r["tier"] == "A"), None)
    if a and a.get("p") is not None:
        found = a["p"] < 0.05 and a["or"] > 1
        text = (f"Teofora ortnamn ligger {'oftare' if found else 'inte oftare'} inom {ch.get('near_km', 1)} km från en "
                f"medeltida kyrka än andra ortnamn i samma trakter ({_pct(a['near_church'])} av {a['n']} namn mot "
                f"{_d(ch['near_church_other'] * 100, 1)} %; oddskvot {_d(a['or'])}).")
        note = (f"Kyrkorna är Wikidatas {ch['n_churches']} kyrkobyggnader i Sverige med ett uppförandeår före 1350, långt "
                "ifrån alla medeltida kyrkor; täckningen är ojämn. Jämförelsen gäller ortnamn av samma slag (byar, gårdar) "
                "inom 10 km från en runsten. Att kyrkor byggdes på eller vid gamla kultplatser är en gammal och omdiskuterad "
                "tanke; resultatet är förenligt med den men visar inte att kyrkan ersatte en kultplats.")
        out.append({"key": "cult_churches", "topic": "Geografi", "status": "indikation" if found else "begränsning",
                    "text": text, "note": note, "significance": significance(a["p"], "p", "Fishers exakta test")})
    age = ch.get("age") or {}
    bon = next((x for x in age.get("tests") or [] if x["feature"] == "bon"), None)
    if bon and bon.get("early") and bon.get("late"):
        e, l, et = bon["early"], bon["late"], bon.get("early_time") or {}
        found = e["p"] < 0.05 and e["or"] > 1
        rep = (e.get("halves") or {}).get("replicated")
        y = age["early_year"]
        text = (f"Kristen bön följer {'de tidiga kyrkorna' if found else 'inte tydligt de tidiga kyrkorna'}: oddskvoten för "
                f"en bön är {_d(e['or'])} ({_d(e['lo'])}–{_d(e['hi'])}) när avståndet till närmaste kyrka uppförd {y} eller "
                f"tidigare halveras, men {_d(l['or'])} ({_d(l['lo'])}–{_d(l['hi'])}) för kyrkor uppförda senare, med "
                f"landskapet konstant (skillnaden p {_d(bon['p_diff'], 3)}). Inom {age['near_km']} km från en tidig kyrka "
                f"bär {_pct(bon['share_early'])} av stenarna en bön, nära bara en sen kyrka {_pct(bon['share_late'])} och "
                f"längre bort {_pct(bon['share_none'])}.")
        if rep is not None:
            text += " Håller i båda halvorna av korpusen" + (f" och med tiden konstant (oddskvot {_d(et['or'])})."
                                                             if et.get("p") is not None and et["p"] < 0.05 else ".") \
                if rep else " Håller inte i båda halvorna av korpusen."
        kors = next((x for x in age["tests"] if x["feature"] == "kors"), None)
        note = (f"Kyrkorna är Wikidatas kyrkobyggnader i Sverige med ett uppförandeår före 1350 ({age['n_early']} till och "
                f"med {y}, {age['n_late']} senare). Åren gäller oftast den kyrka som står i dag och är ofta avrundade, så "
                "uppdelningen är grov; en äldre träkyrka kan ha föregått en sen stenkyrka. Stenar som står vid en kyrka i dag "
                "räknas som flyttade och ingår inte."
                + (f" Korset följer varken de tidiga (oddskvot {_d(kors['early']['or'])}) eller de sena kyrkorna."
                   if kors and kors.get("early") and kors["early"]["p"] >= 0.05 else ""))
        out.append({"key": "prayer_early_churches", "topic": "Geografi",
                    "status": ("mönster att pröva" if rep else "indikation") if found else "begränsning",
                    "text": text, "note": note, "replicated": rep if found else None,
                    "significance": significance(e["p"], "p", "logistisk regression med landskapet och de sena kyrkorna "
                                                              "konstant")})
    return out


# Hypotheses for the scan's combinations that hold in both halves (pattern, kind of place); others get the general one
SCAN_HYPOTHESES = {
    ("kristen", "central"): ("Kristna monument restes oftare vid centralorterna, där eliten tidigt tog till sig den nya tron "
                             "och visade den.",
                             "Pröva mot andra tecken på elit – statusord, storhögar, Husby-gårdar – och mot stenarnas datering: "
                             "bör korsen vid centralorterna vara tidiga?"),
    ("kors", "central"): ("Korset kan ha varit ett elitmärke: det restes oftare vid centralorterna.",
                          "Jämför korsformerna vid centralorterna med dem på andra håll (Lager 2002)."),
    ("bon", "church"): ("Bönestenarna står där kyrkor senare byggdes: gårdar med tidiga kristna monument kan ha fått de första "
                        "kyrkorna.",
                        "Jämför stenarnas datering med kyrkornas äldsta byggnadsfas; tidiga bönestenar bör stå vid de äldsta "
                        "kyrkorna, och flyttade stenar bör hållas isär."),
    ("sjal", "church"): ("Själsbönen kan höra till samma miljö som de tidiga kyrkorna.",
                         "Pröva med ett fullständigt kyrkoregister och kyrkornas äldsta fas."),
}
SCAN_GENERAL = ("Sambandet kan spegla var bygden var tätast och rikast, eller en verklig koppling mellan budskapet och platsen.",
                "Pröva med andra platser av samma slag i samma trakter, och se om sambandet håller inom landskap och över tid.")


def _scan(sc: dict) -> list[dict]:
    """Genomsökningen av landskapet (r/remains.R): ett mönster per kombination som håller i båda halvorna, och en
    sammanfattning av resten."""
    if not sc.get("available") or not sc.get("cells"):
        return []
    from src import places
    from src.pattern_map import PATTERNS
    flabel = {k: l for k, l, *_ in PATTERNS}
    klabel = {k: l for k, l, *_ in places.KINDS}
    sig = [c for c in sc["cells"] if c["q_bh"] < 0.05 and c["feature"] != "neutral"]
    rep = sorted([c for c in sig if (c.get("halves") or {}).get("replicated")], key=lambda c: c["q_bh"])
    other = [c for c in sig if c not in rep]
    out = []
    for c in rep[:6]:
        more = c["or"] > 1
        t = c.get("time") or {}
        text = (f"{flabel.get(c['feature'], c['feature'])} blir {'vanligare' if more else 'ovanligare'} ju närmare "
                f"{klabel.get(c['kind'], c['kind']).lower()} stenen står: oddskvot {_d(c['or'])} ({_d(c['lo'])}–{_d(c['hi'])}) "
                f"när avståndet halveras, med landskapet konstant (q {_d(c['q_bh'], 3) if c['q_bh'] >= 0.001 else '< 0,001'}). "
                f"Inom {_d(c['radius_km'], 1)} km: {_pct(c['share_near'])} av {c['n_near']} stenar, mot {_pct(c['share_far'])} "
                "av övriga. Håller i båda halvorna av korpusen"
                + (f" och med tiden konstant (oddskvot {_d(t['or'])})." if t.get("p") is not None and t["p"] < 0.05 else "."))
        note = (f"Ur en genomsökning av {sc['n_tests']} kombinationer av mönster och platser, justerade tillsammans "
                "(Benjamini–Hochberg); avståndet används direkt, utan vald radie. Flyttade stenar räknas inte. "
                "Platsernas data har sina gränser: ortnamnen är belagda långt efter vikingatiden, kyrkoregistret är "
                "ofullständigt och fornlämningsregistret olika väl inventerat.")
        h, test = SCAN_HYPOTHESES.get((c["feature"], c["kind"]), SCAN_GENERAL)
        out.append({"key": f"scan_{c['feature']}_{c['kind']}", "topic": "Geografi", "status": "mönster att pröva",
                    "replicated": True, "text": text, "note": note, "hypothesis": h, "test": test,
                    "significance": significance(c["q_bh"], "q", "logistisk regression på avståndet med landskapet "
                                                                  "konstant, Benjamini–Hochberg")})
    if other:
        names = "; ".join(f"{flabel.get(c['feature'], c['feature']).lower()} och {klabel.get(c['kind'], c['kind']).lower()}"
                          for c in sorted(other, key=lambda c: c["q_bh"])[:6])
        out.append({"key": "scan_indications", "topic": "Geografi", "status": "indikation",
                    "text": (f"Genomsökningen av landskapet ger {len(other)} samband till som klarar justeringen men inte "
                             f"håller i båda halvorna: {names}."),
                    "note": "Idéer att pröva vidare, inte resultat; se genomsökningen på kartan.",
                    "significance": significance(min(c["q_bh"] for c in other), "q", "Benjamini–Hochberg")})
    return out


def _hotspots(h: dict) -> list[dict]:
    """Kluster ur Kulldorffs scanstatistik (r/hotspots.R): ett mönster per kluster som håller i båda halvorna."""
    from src.pattern_map import PATTERNS
    flabel = {k: l for k, l, *_ in PATTERNS}
    out = []
    for p in h.get("patterns") or []:
        if p["key"] == "neutral":
            continue
        for c in p.get("clusters") or []:
            rep_ = (c.get("halves") or {}).get("replicated")
            if not rep_:
                continue
            strong = (c.get("q_bh") or 1) < 0.05
            provs = ", ".join(f"{k} {v}" for k, v in sorted((c.get("provinces") or {}).items(), key=lambda x: -x[1]))
            text = (f"{flabel.get(p['key'], p['key'])} klustrar: inom {_d(c['radius_km'], 1)} km från klustrets mitt har "
                    f"{_pct(c['rate_in'])} av {c['n']} stenar mönstret, mot {_pct(c['rate_out'])} av övriga "
                    f"({_d(c['rr'])} gånger så vanligt; Kulldorffs scanstatistik, p {_d(c['p'], 3)}). Håller i båda "
                    f"halvorna av korpusen. Klustrets mitt: {c['center']}. Stenar per landskap: {provs}.")
            note = ("Klustret söktes bland alla cirklar som rymmer högst en tiondel av stenarna, med 999 simuleringar; "
                    "flyttade stenar räknas inte. "
                    + ("Klarar justeringen över alla mönster (Benjamini–Hochberg). " if strong else
                       "Klarar inte justeringen över alla mönster (Benjamini–Hochberg); en indikation. ")
                    + f"Mönstret som helhet: Morans I {_d(p['moran']['i'])} (q {_q(p['moran']['q_bh'])}). Ett kluster "
                    "är en plats att titta närmare på – en ristare, en verkstad eller en bygd – inte en förklaring.")
            out.append({"key": f"hotspot_{p['key']}_{c['center']}", "topic": "Geografi",
                        "status": "mönster att pröva" if strong else "indikation", "replicated": True, "text": text,
                        "note": note,
                        "hypothesis": "Klustret kan vara en ristares eller verkstads vana, eller en lokal sed i bygden.",
                        "test": "Jämför klustrets stenar med ristarattribueringarna och med grannstenarna utanför: följer "
                                "mönstret en ristare, eller alla som ristade i bygden?",
                        "significance": significance(c.get("q_bh") or c["p"], "q" if c.get("q_bh") is not None else "p",
                                                     "Kulldorffs scanstatistik, Benjamini–Hochberg över mönstren")})
    return out


def corpus_patterns(res: dict) -> list[dict]:
    """Mönster i hela korpusen, märkta 'bekräftar' eller 'mönster att pröva'."""
    out = []
    g = res.get("geography") or {}
    if g.get("carvers"):
        n = len(g["carvers"])
        st = g.get("strict") or {}
        ratios = sorted(c["compact_ratio"] for c in g["carvers"] if c.get("compact_ratio") is not None)
        med = ratios[len(ratios) // 2] if ratios else None
        strict_txt = "; ".join(
            f"{lbl}: {st[k]['n_compact']} av {st[k]['n_tested']} (område i median {_pct(st[k]['median_ratio'])} av nollmodellens)"
            for k, lbl in (("signed", "bara signerade stenar"), ("style", "mot stenar ur samma stilgrupp och landskap"),
                           ("district", "mot stenar ur samma härad")) if st.get(k))
        out.append({"key": "areas", "topic": "Geografi", "status": "bekräftar",
                    "text": f"Stöder antagandet om regional verksamhet: {g['n_compact']} av {n} ristare med minst "
                            f"{g['min_inscriptions']} säkra stenar arbetade inom ett mindre område än slumpvisa stenar ur samma "
                            f"landskap (q < 0,05); deras område är i median {_pct(med)} av slumpstenarnas."
                            + (f" Med strängare jämförelser – {strict_txt}." if strict_txt else "")
                            + (" Ristarna var alltså regionala på landskapsnivå, men inte mer lokala än stenresningen i samma "
                               "härad." if st.get("district") and st["district"]["n_compact"] <= 0.2 * st["district"]["n_tested"]
                               else ""),
                    "note": "Att ristare var regionalt verksamma är en grund för attribueringarna. Testet på bara signerade "
                            "stenar är oberoende av attribueringar som själva kan ha vägt in geografin; jämförelsen mot samma "
                            "härad prövar om ristarna var mer lokala än den lokala stenresningstraditionen. Fyndplats är inte "
                            "alltid ursprunglig plats (flyttade, inmurade stenar), ristare som verkade över landskapsgränser "
                            "jämförs med flera landskap, och en ristare som inte klarar testet är inte belagd som kringvandrande "
                            "– med få stenar är testet svagt. Resultatet stöder en generell premiss men validerar inga "
                            "enskilda attribueringar; används det för att motivera närhet i nya attribueringar, som sedan "
                            "matas in i testet, uppstår en självförstärkande slinga.",
                    "significance": significance(max((c["compact_q"] for c in g["carvers"] if c.get("compact_q") is not None
                                                      and c["compact_q"] < 0.05), default=None), "q",
                                                 "permutationstest per ristare, Benjamini–Hochberg (högsta q bland de signifikanta)")})
        w = g.get("water") or {}
        if w.get("available"):
            o = w["overall"]
            reg = w.get("overall_regional") or {}
            local = o.get("local_km")
            closer = o["p"] < 0.05
            null = f"slumpvisa punkter på land inom {local} km från andra runstenar" if local else "slumpvisa punkter på land"
            out.append({"key": "water", "topic": "Geografi", "status": "bekräftar" if closer else "begränsning",
                        "text": (f"Runstenarna står {'närmare vatten än' if closer else 'inte närmare vatten än'} {null} "
                                 f"(median {_d(o['median_stones_km'])} mot {_d(o['median_random_km'])} km, "
                                 f"p {_d(o['p'], 3) if o['p'] >= 0.001 else '< 0,001'})."
                                 + (f" Mot hela landskapets runstensområde: {_d(reg['median_random_km'])} km." if reg else "")),
                        "note": ("Känt sedan tidigare: stenar restes vid färdleder, även vattenleder. Jämförelsen görs i landskapet "
                                 "runt stenarna, där folk bodde och rörde sig, och inte mot hela landskapet, som också rymmer "
                                 "obebodd skog och inland. Vattnet är dagens (1:10 milj.): landhöjningen gör att strandlinjen "
                                 "låg högre under vikingatiden (i Mälardalen omkring fem meter), så stenar vid dåtidens stränder "
                                 "och vikar kan i dag stå långt från vatten. "
                                 + ("Jämförelsen med en modellerad strandlinje omkring år 1000 redovisas för sig. "
                                    if (w.get("viking_shore") or {}).get("n_stones") else
                                    "En jämförelse med en rekonstruerad strandlinje för omkring år 1000 återstår. ")
                                 + "Stenar som står i par eller i samma monument räknas var för sig, "
                                 "så observationerna är inte helt oberoende och p-värdet blir något för litet."),
                        "significance": significance(o["p"], "p", "Wilcoxon, ensidigt, mot den lokala nollmodellen")})
            out += _viking_shore(w.get("viking_shore") or {}, o, w.get("provinces"))
            b = w.get("bridges") or {}
            if b and b.get("median_bridge_km", 0) > b.get("median_other_km", 0):
                out.append({"key": "water_bridges", "topic": "Geografi", "status": "begränsning",
                            "text": f"Stenar som nämner bro- eller vägbygge står längre från vattnet i kartlagret "
                                    f"(median {_d(b['median_bridge_km'])} mot {_d(b['median_other_km'])} km).",
                            "note": "Broarna gick oftast över mindre vattendrag och våtmarker som saknas i Natural Earth; "
                                    "resultatet visar kartlagrets gräns, inte att broarna låg långt från vatten.",
                            "significance": significance(b.get("p"), "p", "Wilcoxon")})
    out += _remains(res.get("remains") or {})
    out += _cult((res.get("remains") or {}).get("cult") or {}, (res.get("remains") or {}).get("scan"))
    out += _scan((res.get("remains") or {}).get("scan") or {})
    out += _hotspots(res.get("hotspots") or {})
    a = res.get("attribution") or {}
    if a.get("ablation"):
        ab = {x["features"]: x for x in a["ablation"]}
        gtext = ""
        for name, g in (a.get("grouped_cv") or {}).items():
            ga = {x["features"]: x for x in g.get("ablation") or []}.get("Alla")
            if ga and ga.get("accuracy") is not None:
                gtext += f" Med hela {'socknar' if name == 'Socken' else 'härader'} utelämnade: {_pct(ga['accuracy'])}."
        out.append({"key": "model", "topic": "Attribuering", "status": "bekräftar",
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
        out.append({"key": "spelling", "topic": "Språk", "status": "bekräftar",
                    "text": f"Stavningen av vanliga ord skiljer ristarna åt; tydligast för '{top['lemma']}' (Cramérs V "
                            f"{_d(top['cramers_v'])}).",
                    "note": "Att ristare har egna stavningsvanor är en grund för ortografisk attribuering.",
                    "significance": significance(top.get("q"), "q", "χ² med simulerat p, Benjamini–Hochberg")})
    dl = res.get("dialect") or {}
    if dl.get("mantel"):
        m = dl["mantel"]
        ck = dl.get("checks") or {}
        wp = ck.get("within_province") or {}
        parts = [f"inom {pv} r {_d(x['r'])} (p {_d(x['p'], 3)}, {x['n_districts']} härader)" for pv, x in wp.items() if x.get("tested")]
        ua = ck.get("unattributed") or {}
        if ua.get("tested"):
            parts.append(f"bara stenar utan ristare r {_d(ua['r'])} (p {_d(ua['p'], 3)})")
        pt = ck.get("partial_time") or {}
        if pt.get("tested"):
            parts.append(f"med skillnaden i medeldatering konstant r {_d(pt['r'])}")
        out.append({"key": "dialect", "topic": "Språk", "status": "bekräftar" if m["p"] < 0.05 else "mönster att pröva",
                    "text": f"Geografisk struktur i stavningen: ju längre ifrån varandra två härader ligger, desto mer skiljer "
                            f"sig stavningen (Mantel r {_d(m['r'])}, p {_d(m['p'], 3)}, {dl['n_districts']} härader)."
                            + (f" Kontroller: {'; '.join(parts)}." if parts else ""),
                    "note": "Sambandet är måttligt svagt (avståndet förklarar under en tiondel av skillnaderna) och väntat, och "
                            "Mantel-testet ger för låga p-värden när båda matriserna har rumslig struktur. Testet visar att "
                            "stavningen är geografiskt strukturerad, inte att strukturen är dialektal: ristarverkstäder, "
                            "landskapsnormer och tid kan ge samma mönster, vilket kontrollerna ovan prövar. Avståndsklasserna "
                            "(Statistik) visar på vilka avstånd likheten finns. " + (dl.get("caveat") or ""),
                    "significance": significance(m["p"], "p", "Mantel-test, 999 permutationer (optimistiskt vid rumsliga data)")})
    c = res.get("clusters") or {}
    if c.get("k"):
        sn, cv = c.get("silhouette_null") or {}, c.get("carvers") or {}
        beats = sn and c["best_silhouette"] > (sn.get("max") or 1)
        nest = (f" Ristarna hålls ihop: i genomsnitt {_pct(cv['nesting'])} av en ristares stenar hamnar i samma grupp, mot "
                f"{_pct(cv['nesting_null'])} om grupperna vore slumpmässiga." if cv.get("nesting") is not None else "")
        out.append({"key": "clusters", "topic": "Stil och innehåll", "status": "bekräftar" if beats else "svagt",
                    "text": f"Klustringen ger {c['k']} grupper med {c['structure']} struktur (silhuett {_d(c['best_silhouette'])}"
                            + (f", mot högst {_d(sn['max'])} i {sn['n']} datamängder där varje variabel blandats om" if sn else "")
                            + f").{nest}",
                    "note": "Grupperna speglar främst kors, stungna runor och bön, alltså tid och kristnande – en bekräftelse av "
                            "tidssignalen snarare än ett nytt mönster. Det justerade Rand-indexet mot ristarna "
                            f"({_d(cv.get('ari'))}) blir lågt redan för att tre grupper inte kan motsvara många ristare; "
                            "andelen av ristarens stenar i samma grupp svarar bättre på frågan.",
                    "significance": significance(sn.get("p") if sn else None, "p",
                                                 f"silhuetten mot {sn.get('n')} omblandade datamängder" if sn else "")})
    ch = res.get("chronology") or {}
    v = ch.get("validation") or {}
    if v:
        out.append({"key": "seriation", "topic": "Datering", "status": "bekräftar" if v.get("usable") else "svagt",
                    "text": f"I Uppland ordnar seriationen av språk och innehåll stenarna i samma följd som Gräslunds "
                            f"stilkronologi (rho {_d(v['rho'])}, {_d(v['partial_rho'])} med latituden konstant), utan att "
                            "ornamentiken ingick.",
                    "note": "Ett av de mer självständiga resultaten: språk och innehåll bestämmer inte ornamentiken, så "
                            "överensstämmelsen är oberoende stöd för den relativa kronologin. "
                            + seriation_robust_text(v.get("robustness"))
                            + f" Årtalen är osäkra: korsvaliderat medelfel {v['mae_loo_years']} år mot "
                            f"{v['mae_naive_years']} år utan modell, och facit är själv mittpunkter i Gräslunds intervall. "
                            "Resultatet bekräftar inte de absoluta årtalen, ger inga precisa dateringar av enskilda stenar och "
                            "gäller Uppland. Seriationen använder drag vars förändring också mäts för sig (stungna runor, "
                            "monoftongen); de två resultaten är därför inte helt oberoende, vilket den strängaste varianten "
                            "prövar.",
                    "significance": significance(v.get("p"), "p", "Spearmans rangkorrelation")})
        for dim in ch.get("corpus_dimensions") or []:
            only_carver = list(dim.get("explained_by") or []) == ["ristare"]
            if only_carver and dim.get("eta2_time") is not None:
                d1 = (ch.get("dim1_checks") or {}) if dim["dim"] == 1 else {}
                extra = []
                sg = d1.get("signed_carver") or {}
                if sg.get("eta2") is not None:
                    extra.append(f"bara signerade stenar (n {sg['n']}): ristaren {_pct(sg['eta2'])} (slumpnivå {_pct(sg['null95'])})")
                for k, lbl in (("no_soul", "utan själsbönen (som annars ger bönen dubbel vikt)"),
                               ("intact", "bara stenar med bevarat inskriftsslut")):
                    x = d1.get(k) or {}
                    if x.get("tested"):
                        extra.append(f"{lbl}: ristaren {_pct(x['eta2_carver'])} (slump {_pct(x['eta2_carver_null95'])}), stilgruppen "
                                     f"{_pct(x['eta2_time'])} (slump {_pct(x['eta2_time_null95'])})")
                exc_c = (dim["eta2_carver"] or 0) - (dim.get("eta2_carver_null95") or 0)
                exc_t = (dim["eta2_time"] or 0) - (dim.get("eta2_time_null95") or 0)
                out.append({"key": f"formula:{dim['dim']}", "topic": "Formelval", "status": "bekräftar",
                            "text": f"Formelvalet följer ristaren mer än tiden (CA-dimension {dim['dim']}, {_d(dim['inertia_pct'], 1)} % "
                                    f"av inertin, daterade stenar): ristaren förklarar {_pct(dim['eta2_carver'])} av variationen "
                                    f"(slumpnivå {_pct(dim['eta2_carver_null95'])}, alltså {round(exc_c * 100)} procentenheter "
                                    f"över), stilgruppen {_pct(dim['eta2_time'])} (slumpnivå {_pct(dim.get('eta2_time_null95'))}, "
                                    f"{round(exc_t * 100)} över). {_poles(dim)}"
                                    + (f" Kontroller: {'; '.join(extra)}." if extra else ""),
                            "note": "Att formelvalet följer ristare och verkstäder diskuteras i forskningen; här mätt. Dimensionen "
                                    "handlar i praktiken om bön eller inte bön. Tiden är mätt grovare än ristaren (stilgruppen är "
                                    "ett intervall på flera decennier), vilket drar ned tidens andel, och ristare verkar under en "
                                    "begränsad period, så ristarens andel innehåller också tid och plats. Attribueringarna kan "
                                    "bygga på formulärbruket; testet på signerade stenar prövar det. Själsbönen visar ändå en "
                                    "tidstopp med ristaren konstant, så en tidseffekt finns, men den är mindre.",
                            "significance": significance(dim.get("p_carver"), "p", "eta² för ristare mot permutationer")})
            if dim["unexplained"]:
                out.append({"key": f"ca_unexplained:{dim['dim']}", "topic": "Datering", "status": "mönster att pröva",
                            "text": f"I hela korpusen följer CA-dimension {dim['dim']} ({_d(dim['inertia_pct'], 1)} % av inertin) "
                                    f"varken tid (rho {_d(dim['rho_time'])}"
                                    + (f"; eta² mot stilgrupp {_d(dim['eta2_time'])}" if dim.get("eta2_time") is not None else "")
                                    + ") eller "
                                    f"geografi (rho latitud {_d(dim['rho_lat'])}, eta² landskap {_d(dim['eta2_province'])}). "
                                    f"{_poles(dim)}",
                            "note": f"Sambandet med ristare är eta² {_d(dim['eta2_carver'] or 0)}"
                                    + (f" (slumpnivå {_d(dim['eta2_carver_null95'])})" if dim.get("eta2_carver_null95") is not None else "")
                                    + ". Mönstret kan vara ristarens, verkstadens eller beställarens val; formulärtraditioner "
                                    "knutna till ristare diskuteras i forskningen.",
                            "significance": significance(None, test="beskrivande (korrespondensanalys); inget signifikanstest")})
    nw = res.get("network") or {}
    for k in nw.get("kinship") or []:
        if k.get("q_period") is not None and k["q_period"] < 0.05 and k["n"] >= 20:
            trend = "vanligare" if (k["late"] or 0) > (k["early"] or 0) else "ovanligare"
            weak = abs((k["late"] or 0) - (k["early"] or 0)) < WEAK_EFFECT
            strat = k.get("q_period_strat")
            gone = strat is not None and strat >= 0.05
            comp = (nw.get("kinship_strata") or {}).get("composition") or []
            ctext = "; ".join(f"{c['period']}: {_pct(c['share_top'])} från {c['top']}" for c in comp)
            if gone:
                out.append({"key": f"kinship:{k['relation']}", "topic": "Släkt och formler", "status": "begränsning",
                            "text": f"Relationen '{k['relation']}' ser {trend} ut på sena stenar ({_pct(k['late'])} mot "
                                    f"{_pct(k['early'])}; q {_d(k['q_period'], 3)}), men skillnaden försvinner inom landskapen "
                                    f"(q {_d(strat, 3)}).",
                            "note": f"De sena stenarna kommer från andra trakter än de tidiga ({ctext}); skillnaden speglar "
                                    "var stenarna står, inte en förändring över tid.",
                            "significance": significance(strat, "q", "Cochran–Mantel–Haenszel per landskap, Benjamini–Hochberg")})
                continue
            out.append({"key": f"kinship:{k['relation']}", "topic": "Släkt och formler", "status": "mönster att pröva", "small": bool(weak),
                        "text": f"Relationen '{k['relation']}' är {trend} på sena stenar (efter ca 1050: {_pct(k['late'])}, "
                                f"före: {_pct(k['early'])}; q {_d(k['q_period'], 3)}).",
                        "note": ((WEAK_NOTE + " ") if weak else "") + "Tidsindelningen bygger på Gräslunds stilgrupper och gäller "
                                "stenar med säker stilgrupp.",
                        "significance": significance(k["q_period"], "q", "Fishers exakta test, Benjamini–Hochberg")})
    an = res.get("anonymous") or {}
    if an.get("groups"):
        v = an["validation"]; cands = [g for g in an["groups"] if g["status"] == "candidate"]
        out.append({"key": "anonymous", "topic": "Okända ristare", "status": "mönster att pröva",
                    "text": f"{len(cands)} {'ny grupp' if len(cands) == 1 else 'nya grupper'} av stenar utan ristare "
                            f"({sum(g['n'] for g in cands)} stenar) liknar varandra lika mycket som en ristares stenar och "
                            "liknar ingen känd ristare i närheten. Appen har gett dem arbetsnamn efter typstenens socken: "
                            + ", ".join(f"{g['name']} ({g['n']} stenar)" for g in cands[:4]) + ". "
                            f"{len(an['groups']) - len(cands)} andra grupper liknar en känd ristare.",
                    "note": f"Prövat på stenar med känd ristare bestod en grupp i genomsnitt till {_pct(v['purity'])} av "
                            f"samma ristare, mot {_pct(v['purity_geography'])} för lika många närliggande stenar – omkring en "
                            "tredjedel av en typisk grupp kommer alltså från andra ristare, och geografin förklarar redan mycket. "
                            + (f"Utan de tidsberoende dragen (stil, kors, stungna runor, böner, åsrunan, signatur) blir renheten "
                               f"{_pct(v['purity_no_time'])} och grupperna återkommer i genomsnitt till "
                               f"{_pct((an.get('time_free') or {}).get('mean_robust'))}, så de samlar inte bara stenar från samma tid. "
                               if v.get("purity_no_time") is not None else "")
                            + ((f"När gränsen togs fram på andra ristare än de som prövades var renheten {_pct(v['heldout']['purity'])} mot "
                                f"{_pct(v['heldout']['purity_geography'])} för närliggande stenar. ") if (v.get("heldout") or {}).get("purity") else "")
                            + ((f"Nästan alla kända ristare finns i Uppland och Södermanland ({an['coverage']['carvers_by_province'].get('U', 0)} "
                                f"och {an['coverage']['carvers_by_province'].get('Sö', 0)} av {an['coverage']['n_carvers']}), så om "
                                "gränsen gäller i landskapen med kandidaterna är inte prövat. ") if (an.get("coverage") or {}).get("n_carvers") else "")
                            + "Stenar med känd ristare är ofta signerade och mer standardiserade, så träffsäkerheten kan vara "
                            "lägre för de okända. Grupperna är hypoteser om verkstäder eller lokala traditioner, inte individer, "
                            "tills oberoende drag (runformer, ornamentik, huggteknik) bekräftar dem. Arbetsnamnen är appens "
                            "etiketter och kan krocka med benämningar i litteratur som appen inte har.",
                    "significance": significance(None, test="validerad på stenar med känd ristare i stället för ett signifikanstest")})
    out += change_patterns(res.get("change") or {})
    out += _message_patterns(res.get("messages") or {})
    out += _people_patterns(res.get("people") or {})
    # A significant test on a pattern that is only an indication or a weak effect: the mark says both, so that
    # "Signifikant" and "indikation" do not stand side by side unexplained
    reasons = {"indikation": "testet är signifikant i huvudmodellen, men resultatet håller inte i alla kontroller eller i "
                             "båda halvorna av korpusen (se förklaringen)",
               "begränsning": "testet är signifikant, men resultatet är inte oberoende (se förklaringen)"}
    for pt in out:
        sig = pt.get("significance") or {}
        if sig.get("significant") and pt.get("status") in reasons:
            pt["significance"] = {**sig, "qualified": reasons[pt["status"]]}
        kind = str(pt.get("key") or "").split(":")[0]
        hyp = (HYPOTHESES.get((pt.get("topic"), pt.get("key"))) or HYPOTHESES.get((pt.get("topic"), kind))
               or HYPOTHESES.get((pt.get("topic"), None)))
        if hyp and pt.get("status") != "begränsning":
            pt["hypothesis"], pt["test"] = hyp
    return out


_NUMBER_WORDS = {1: "Ett", 2: "Två", 3: "Tre", 4: "Fyra", 5: "Fem", 6: "Sex", 7: "Sju", 8: "Åtta"}


def _count_word(n: int, one: str, many: str) -> str:
    """'Ett budskap', 'Två budskap', '9 budskap'."""
    return f"{_NUMBER_WORDS.get(n, str(n))} {one if n == 1 else many}"


def _and_list(items: list[str]) -> str:
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " och " + items[-1]


def _dn(v, digits: int = 2) -> str:
    return "–" if v is None else _d(v, digits)


def _odds(o: dict | None, digits: int = 1) -> str:
    """'oddskvot 5,5, 95 % KI 1,7–24'."""
    if not o or o.get("or") is None:
        return "oddskvot –"
    hi = o.get("hi")
    return (f"oddskvot {_d(o['or'], digits)}, 95 % KI {_dn(o.get('lo'), digits)}–"
            + ("∞" if hi is None or math.isinf(hi) else _d(hi, 0 if hi >= 10 else digits)))


def message_separated(els: dict) -> list[tuple[str, str, list[dict]]]:
    """Budskap som finns i bara den ena av Götaland och Svealand (Fishers exakta test, p < 0,05), grupperade efter
    landsdelen där de finns: [(finns i, saknas i, [{key, label, br, p}])]. Används av mönstren och förklaringen."""
    groups: dict[tuple[str, str], list[dict]] = {}
    for e in els.values():
        p = (e.get("fisher") or {}).get("p")
        if not e.get("separation") or p is None or p >= 0.05:
            continue
        br = {b["region"]: b for b in e.get("by_region") or []}
        gk, sk = (br.get("Götaland") or {}).get("k") or 0, (br.get("Svealand") or {}).get("k") or 0
        if bool(gk) == bool(sk):
            continue
        present, absent = ("Svealand", "Götaland") if sk else ("Götaland", "Svealand")
        groups.setdefault((present, absent), []).append({"key": e["key"], "label": e["label"], "br": br, "p": p})
    return [(pr, ab, sep) for (pr, ab), sep in groups.items()]


def separation_sentence(present: str, absent: str, sep: list[dict]) -> str:
    """'Arv och rest åt sig själv i livstiden finns i Svealand men inte i Götaland.'"""
    labels = [e["label"] for e in sep]
    labels = [labels[0]] + [x[:1].lower() + x[1:] for x in labels[1:]]
    return f"{_and_list(labels)} finns i {present} men inte i {absent}."


def _direction_row(name: str, x: dict | None) -> str:
    """En riktning: Fishers exakta test (oddskvot, intervall och p ur samma test) och modellen med tidsskikt (oddskvot,
    intervall och p ur modellen). Äldre resultat utan Fishers oddskvot visar modellen och Fishers p för sig."""
    x = x or {}
    model = f"med tidsskikt {_odds(x)}, p {_dn(x.get('p'), 3)}"
    if x.get("fisher"):
        return f"{name} Fishers exakta test {_odds(x['fisher'])}, p {_dn(x['fisher'].get('p'), 3)}; {model}"
    return f"{name} {model}; Fishers exakta test utan justering p {_dn(x.get('fisher_p'), 3)}"


def travel_direction_text(t: dict) -> str:
    """Vad interaktionen säger om väst och öst, utan att läsa ett högt p som bevis för samma skillnad."""
    p_int, ia = t.get("p_interaction"), t.get("interaction") or {}
    cells = {(c["region"], c["direction"]): c for c in t.get("cells") or []}
    gw, ge = (cells.get(("Götaland", "väst")) or {}).get("n", 0), (cells.get(("Götaland", "öst")) or {}).get("n", 0)
    bd = {x["direction"]: x for x in t.get("by_direction") or []}
    per_dir = (f"Riktning för riktning: {_direction_row('västerut', bd.get('väst'))}; "
               f"{_direction_row('österut', bd.get('öst'))}.")
    if p_int is None:
        return per_dir
    ratio = (f" Kvoten mellan oddskvoterna öst och väst är {_d(ia['or'], 2)} (95 % KI {_dn(ia.get('lo'), 2)}–"
             f"{_dn(ia.get('hi'), 1)}); 1 betyder samma skillnad åt båda håll, och intervallet visar hur osäker kvoten är."
             if ia.get("or") is not None and p_int >= 0.05 else "")
    if p_int >= 0.05:
        return (f"Någon skillnad mellan väst och öst går inte att visa (interaktion p {_d(p_int, 2)}), men det betyder inte "
                f"att skillnaden är densamma: testet är svagt med {gw} götländska resestenar västerut och {ge} österut."
                + ratio + " " + per_dir)
    return f"Skillnaden mellan landsdelarna är inte densamma i väst och öst (interaktion p {_d(p_int, 3)}). " + per_dir


def travel_direction_agreement(t: dict) -> tuple[bool | None, bool]:
    """(säger Götalands resestenar oftare att mannen dog borta enligt Mantel–Haenszel-kvoten, pekar båda riktningarnas
    råa andelar åt samma håll som kvoten). None när kvoten saknas."""
    mh = t.get("mh") or {}
    if mh.get("or") is None:
        return None, False
    more = mh["or"] > 1
    cells = {(c["region"], c["direction"]): c for c in t.get("cells") or []}
    same = True
    for d in ("väst", "öst"):
        g, s = cells.get(("Götaland", d)) or {}, cells.get(("Svealand", d)) or {}
        if not g.get("n") or not s.get("n"):
            same = False
            continue
        gs, ss = g["k"] / g["n"], s["k"] / s["n"]
        same = same and ((gs > ss) if more else (gs < ss))
    return more, same


def travel_scope_text(t: dict) -> str:
    """Vilka resestenar testen gäller: bara de med en enda riktning (väst eller öst)."""
    aj = t.get("all_journeys") or []
    if not aj:
        return ""
    left = sum(x["n"] - x["single"] for x in aj)
    per = ", ".join(f"{x['region']} {x['n'] - x['single']}" for x in aj)
    return (f"Testen gäller de {sum(x['single'] for x in aj)} resestenar i Götaland och Svealand som har en enda riktning; "
            f"{left} med båda riktningarna eller ingen ({per}) räknas inte." if left else "")


def travel_tests_text(t: dict) -> str:
    """Vilka test skillnaden mellan landsdelarna håller i, och vad varje test tar hänsyn till."""
    mh, mh_t, glm, gam = (t.get("mh") or {}), (t.get("mh_time") or {}), (t.get("common_glm") or {}), (t.get("common") or {})
    out = [f"Exakt Mantel–Haenszel med riktningen som skikt: {_odds(mh)}, p {_dn(mh.get('p'), 4)}."]
    if mh_t.get("p") is not None:
        kept = (f" ({mh_t['strata']} skikt med båda landsdelarna och båda utfallen, {mh_t['n']} av {t['n']} resestenar; "
                "skikt där alla stenar kommer från samma landsdel eller har samma utfall bär ingen information)"
                if mh_t.get("strata") and mh_t.get("n") is not None and t.get("n") else "")
        out.append(f"Med riktning × tidsskikt (stilgruppernas period, odaterade som eget skikt) som skikt: {_odds(mh_t)}, "
                   f"p {_dn(mh_t['p'], 3)}" + kept + ".")
    if glm.get("p") is not None:
        out.append(f"Logistisk regression med riktning och tidsskikt: {_odds(glm)}, p {_dn(glm['p'], 3)}.")
    ms = t.get("mh_strict") or {}
    if ms.get("p") is not None:
        out.append(f"Exakt Mantel–Haenszel med riktningen som skikt, bara på stenar med minst {ms['words']} läsbara ord: "
                   f"{_odds(ms)}, p {_dn(ms['p'], 4)} ({ms.get('n')} resestenar).")
    scope = travel_scope_text(t)
    if scope:
        out.append(scope)
    if gam.get("p") is not None:  # sist, så att en förklaring av socknen kan följa
        out.append(f"Med ristaren eller socknen som slumpeffekt: {_odds(gam)}, p {_dn(gam['p'], 2)}"
                   + (" – skillnaden blir osäker, eftersom de götländska resestenarna är få och spridda över många socknar."
                      if gam["p"] >= 0.05 else "."))
    return " ".join(out)


def strict_text(e: dict, digits: int = 2) -> str:
    """Känsligheten för läsbarhetsgränsen: samma modell på stenar med minst STRICT_WORDS läsbara ord."""
    st = e.get("strict") or {}
    m = st.get("model") or {}
    if m.get("p") is None:
        return ""
    br = {x["region"]: x for x in st.get("by_region") or []}
    g, v = br.get("Götaland") or {}, br.get("Svealand") or {}
    n_ = lambda x: f"{x:,}".replace(",", "\u00a0") if isinstance(x, int) else str(x)  # noqa: E731
    return (f"Bara stenar med minst {st['words']} läsbara ord: {n_(g.get('k'))} av {n_(g.get('n'))} mot {n_(v.get('k'))} av "
            f"{n_(v.get('n'))}, oddskvot {_d(m['or'], digits)} (95 % KI {_dn(m.get('lo'), digits)}–{_dn(m.get('hi'), digits)}), "
            f"p {_dn(m['p'], 3)} efter tid och ristare.")


def legibility_text(m: dict) -> str:
    """Hur fragmentariska de läsbara stenarna är per landsdel: läsbara stenar med färre än STRICT_WORDS ord."""
    lg = m.get("legibility") or {}
    br = {x["region"]: x for x in lg.get("by_region") or []}
    g, v = br.get("Götaland"), br.get("Svealand")
    if not g or not v or not g.get("legible") or not v.get("legible"):
        return ""
    n_ = lambda x: f"{x:,}".replace(",", "\u00a0")  # noqa: E731
    return (f"Läsbar betyder minst {lg['min_words']} läsbara ord, och då räknas ett fragment som en sten utan budskapet. "
            f"Färre än {lg['strict_words']} läsbara ord har {n_(g['legible'] - g['strict'])} av {n_(g['legible'])} läsbara "
            f"stenar i Götaland ({_pct((g['legible'] - g['strict']) / g['legible'])}) och {n_(v['legible'] - v['strict'])} "
            f"av {n_(v['legible'])} i Svealand ({_pct((v['legible'] - v['strict']) / v['legible'])}).")


_UNCHECKED_WORDS = {"gald": "gäld", "arv": "arv", "gard": "gård", "egen": "egen sten", "berom": "beröm",
                    "resa": "resa", "dod_borta": "död borta", "dod_uppgift": "dödsuppgift"}


def rule_check_text(rc: dict | None) -> str:
    """Hur väl budskapsreglerna stämmer med handkodningarna (data/messages_check.json via r/messages.R)."""
    if not rc:
        return ("Budskapen klassas med en regel per budskap i den engelska översättningen; hur väl reglerna stämmer med "
                "handkodningarna redovisar scripts/check_messages.py (METHODS.md 1o).")
    w, e = rc.get("west") or {}, rc.get("east") or {}
    al, sl = (e.get("samples") or {}).get("alla") or {}, (e.get("samples") or {}).get("slump") or {}
    f = lambda x: f"{x[0]} av {x[1]}" if x else "–"  # noqa: E731
    out = ("Budskapen klassas med en regel per budskap i den engelska översättningen. Mot handkodningen av "
           f"{w.get('n')} västerinskrifter ({w.get('file')}) stämmer död borta i {f(w.get('dod_borta'))}; mot "
           f"{al.get('n')} handkodade stenar om österfärder och angränsande fall ({e.get('file')}) stämmer resa i "
           f"{f(al.get('resa'))}, död borta i {f(al.get('dod_borta'))}, dödsuppgift i {f(al.get('dod_uppgift'))} och "
           f"riktningen i {f(al.get('riktning'))}.")
    if sl.get("n"):
        out += (f" Österurvalet kodades medan reglerna rättades; i dess slumpvisa del ({sl['n']} stenar) stämmer resa i "
                f"{f(sl.get('resa'))} och död borta i {f(sl.get('dod_borta'))}.")
    un = [_UNCHECKED_WORDS.get(k, k) for k in rc.get("unchecked") or []]
    if un:
        out += f" {_and_list(un)[:1].upper()}{_and_list(un)[1:]} är bara stickprovskontrollerade."
    if rc.get("stale"):
        out += " Kontrollen gjordes med en tidigare version av reglerna."
    return out


def _people_patterns(m: dict) -> list[dict]:
    """Mönstren ur människomodulen (r/people.R, låst plan analysplaner/2026-10-28-manniskorna.md): kvinnor bland
    resarna efter landsdel och tid, drengr och þegn efter den dödes plats i släkten, död utanför Norden efter samma,
    och broarna. Status som modulen satte den enligt planen; 'ingen skillnad påvisad' för broarna blir en begränsning."""
    out = []
    tests = {t["key"]: t for t in m.get("tests") or []}
    note = ("Kön och relation läses ur Rundatas engelska översättning med regler (src/people.py) som har fel på omkring en "
            "sten av tjugo, oftast där texten har luckor (METHODS.md). Prövat enligt en låst plan med landsdel, tidsskikt och "
            "ristaren som slumpeffekt, och i två halvor av korpusen delade socken för socken.")
    sig = lambda mm: significance(mm.get("p_holm"), "p", "logistisk regression med ristaren som slumpeffekt, "  # noqa: E731
                                                          "Holm-korrigerat över sex test")
    ok = {"bekräftar", "mönster att pröva", "indikation"}

    def odds(mm, k=2):
        return f"oddskvot {_d(mm['or'], k)}, troligen mellan {_d(mm['lo'], k)} och {_d(mm['hi'], k)}"

    t = tests.get("kvinna_landsdel")
    if t and t.get("status") in ok:
        mm, sr = t["main"], t["main"].get("shares_region") or {}
        out.append({"key": "people_kvinna_landsdel", "topic": "Människorna", "status": t["status"],
                    "text": f"En kvinna finns bland resarna på {_pct(sr.get('Svealand', 0))} av stenarna i Svealand mot "
                            f"{_pct(sr.get('Götaland', 0))} i Götaland, med tid och ristare konstanta ({odds(mm)}; "
                            f"{mm['k']} av {mm['n']} stenar med känd resare har en kvinna bland resarna).",
                    "note": note, "significance": sig(mm)})
    t = tests.get("kvinna_tid")
    if t and t.get("status") in ok:
        mm = t["main"]
        out.append({"key": "people_kvinna_tid", "topic": "Människorna", "status": t["status"],
                    "text": f"Kvinnor bland resarna blir {'vanligare' if mm['or'] > 1 else 'ovanligare'} under 1000-talet: "
                            f"oddsen ändras med en faktor {_d(mm['or'], 2)} per 50 år, med landsdel och ristare konstanta.",
                    "note": note, "significance": sig(mm)})
    for key, word, young_first in (("drengr_ung", "drengr", True), ("thegn_ung", "þegn", False)):
        t = tests.get(key)
        if t and t.get("status") in ok:
            mm, sh = t["main"], t["main"].get("shares") or {}
            y, o = sh.get("1", 0), sh.get("0", 0)
            out.append({"key": f"people_{key}", "topic": "Människorna", "status": t["status"],
                        "text": (f"{word} sägs om söner och bröder snarare än om fäder och makar: {_pct(y)} av stenarna efter "
                                 f"söner och bröder mot {_pct(o)} efter fäder och makar" if young_first else
                                 f"{word} sägs om fäder och makar snarare än om söner och bröder: {_pct(o)} av stenarna efter "
                                 f"fäder och makar mot {_pct(y)} efter söner och bröder")
                                + f", med landsdel, tid och ristare konstanta ({odds(mm)}).",
                        "note": note + " Orden kan också säga något om ställning och följe, inte bara om ålder.",
                        "significance": sig(mm)})
    t = tests.get("dod_borta_ung")
    if t and t.get("status") in ok:
        mm, sh = t["main"], t["main"].get("shares") or {}
        out.append({"key": "people_dod_borta_ung", "topic": "Människorna", "status": t["status"],
                    "text": f"Söner och bröder dog oftare utanför Norden än fäder och makar: {_pct(sh.get('1', 0))} av stenarna efter "
                            f"söner och bröder säger att den döde dog utanför Norden, mot {_pct(sh.get('0', 0))} efter fäder och "
                            f"makar, med landsdel, tid och ristare konstanta ({odds(mm)}).",
                    "note": note + " Söner och bröder sörjs av föräldrar och syskon, fäder och makar av barn och änkor: "
                                   "färderna tycks ha varit de ungas, före familjen.",
                    "significance": sig(mm)})
    t = tests.get("bro_kvinna")
    if t and t.get("status") == "ingen skillnad påvisad" and not (t["main"].get("too_few")):
        mm, sh = t["main"], t["main"].get("shares") or {}
        out.append({"key": "people_bro_kvinna", "topic": "Människorna", "status": "begränsning",
                    "text": f"Stenar med en kvinna bland resarna nämner inte oftare bro eller väg än andra ({_pct(sh.get('1', 0))} "
                            f"mot {_pct(sh.get('0', 0))}, med landsdel, tid och ristare konstanta; {odds(mm)}).",
                    "note": note, "significance": sig(mm)})
    return out


def _message_patterns(m: dict) -> list[dict]:
    """Mönstren ur budskapsmodellen (r/messages.R): resestenarnas dödsuppgift i Götaland och Svealand, budskap som
    bara finns i den ena landsdelen, och beröm och resor efter landsdel."""
    out = []
    n_ = lambda x: f"{x:,}".replace(",", "\u00a0") if isinstance(x, int) else str(x)  # noqa: E731  (1 287)
    els = {e["key"]: e for e in m.get("elements") or []}
    t = m.get("travel") or {}
    mh, mh_t = t.get("mh") or {}, t.get("mh_time") or {}
    if t.get("n") and mh.get("p") is not None and mh["p"] < 0.05:
        cells = {(c["region"], c["direction"]): (c["k"], c["n"]) for c in t.get("cells") or []}
        g = [sum(cells.get(("Götaland", d), (0, 0))[i] for d in ("väst", "öst")) for i in (0, 1)]
        v = [sum(cells.get(("Svealand", d), (0, 0))[i] for d in ("väst", "öst")) for i in (0, 1)]
        timed = mh_t.get("p") is not None
        holds_time = timed and mh_t["p"] < 0.05
        more, same = travel_direction_agreement(t)
        raw_more = g[0] / max(1, g[1]) > v[0] / max(1, v[1])
        out.append({"key": "messages_travel_death", "topic": "Budskap",
                    "status": "mönster att pröva" if holds_time or not timed else "indikation",
                    "text": f"När en sten nämner en resa utanför Norden säger den i Götaland {'oftare' if more else 'mer sällan'} "
                            f"än i Svealand att mannen dog utanför Norden"
                            + (" i båda riktningarna" if same else " sammantaget över riktningarna") +
                            f": {n_(g[0])} av {n_(g[1])} ({_pct(g[0] / max(1, g[1]))}) mot {n_(v[0])} av {n_(v[1])} "
                            f"({_pct(v[0] / max(1, v[1]))})"
                            + (" (de råa andelarna pekar åt andra hållet, eftersom riktningarna är olika vanliga i "
                               "landsdelarna)" if raw_more != more else "") + ". "
                            + travel_direction_text(t)
                            + (" Om skillnaden speglar en sed i hur man berättade eller att götländska resenärer oftare dog "
                               "borta skiljer stenarna inte åt." if more else ""),
                    "note": travel_tests_text(t) + " Budskapen klassas med regler i den engelska översättningen "
                            "(src/messages.py); en sten som inte säger att mannen dog borta kan gälla en levande resenär, "
                            "en sten som resenären reste själv eller ett fragment, inte nödvändigtvis någon som kom hem.",
                    "significance": significance(mh_t["p"], "p", "exakt Mantel–Haenszel, riktning × tidsskikt som skikt")
                    if timed else significance(mh["p"], "p", "exakt Mantel–Haenszel, riktningen som skikt")})
    for present, absent, sep in message_separated(els):
        keys = {e["key"] for e in sep}
        known = present == "Svealand" and keys <= {"arv", "egen"}
        parts = []
        for e in sep:
            br = e["br"]
            parts.append(f"{e['label'].lower()} ({n_(br.get(present, {}).get('k'))} av {n_(br.get(present, {}).get('n'))} "
                         f"läsbara stenar i {present}, {n_(br.get(absent, {}).get('k'))} av {n_(br.get(absent, {}).get('n'))} "
                         f"i {absent})")
        named = [x for k, x in (("arv", "arvsstenarna"),
                                ("egen", "stenarna som resarna reste åt sig själva i livstiden (som Jarlabankes)")) if k in keys]
        out.append({"key": f"messages_{'svealand' if present == 'Svealand' else 'gotaland'}_only", "topic": "Budskap",
                    "status": "bekräftar" if known else "mönster att pröva",
                    "text": f"{_count_word(len(sep), 'budskap', 'budskap')} finns i {present} men inte i {absent}: "
                            + "; ".join(parts) + ".",
                    "note": ("Känt sedan tidigare: " + " och ".join(named) + " hör till Uppland och Södermanland. Här "
                             "bekräftat med samma regler för hela landet." if known else
                             f"Budskapet saknas helt bland de läsbara stenarna i {absent}, så ingen oddskvot går att skatta; "
                             "Fishers exakta test står i stället.")
                            + " Budskapen klassas med regler i den engelska översättningen (src/messages.py).",
                    "significance": significance(max(e["p"] for e in sep), "p", "Fishers exakta test (högsta p)")})
    b = els.get("berom") or {}
    if (b.get("model") or {}).get("p") is not None and b["model"]["p"] < 0.05 and b["model"]["or"] > 1:
        br = {x["region"]: x for x in b.get("by_region") or []}
        out.append({"key": "messages_praise", "topic": "Budskap", "status": "bekräftar",
                    "text": f"Götalandsstenarna berömmer den döde oftare än Svealandsstenarna ({n_(br['Götaland']['k'])} av "
                            f"{n_(br['Götaland']['n'])} mot {n_(br['Svealand']['k'])} av {n_(br['Svealand']['n'])}; oddskvot "
                            f"{_d(b['model']['or'], 1)} efter tid och ristare).",
                    "note": "Känt sedan tidigare för Västergötlands drengr- och þegn-stenar; här prövat för hela Götaland med tid och "
                            "ristare som kontroll. Beröm räknas med en ordlista (god, dugande, bäst, givmild …). "
                            + strict_text(b, 1),
                    "significance": significance(b["model"]["p"], "p", "logistisk regression med ristaren som slumpeffekt")})
    r = els.get("resa") or {}
    if (r.get("model") or {}).get("p") is not None and r["model"]["p"] < 0.05 and r["model"]["or"] < 1:
        br = {x["region"]: x for x in r.get("by_region") or []}
        aj = {x["region"]: x for x in t.get("all_journeys") or []}.get("Götaland")
        if aj:  # alla resestenar, också de med båda riktningarna eller ingen
            gk, gn = aj["k"], aj["n"]
        else:
            gc = [c for c in t.get("cells") or [] if c.get("region") == "Götaland"]
            gk, gn = sum(c["k"] for c in gc), sum(c["n"] for c in gc)
        sm = ((r.get("strict") or {}).get("model") or {})
        holds_strict = sm.get("p") is not None and sm["p"] < 0.05 and sm["or"] < 1
        out.append({"key": "messages_travel_less", "topic": "Budskap",
                    "status": "mönster att pröva" if holds_strict or sm.get("p") is None else "indikation",
                    "text": f"Götalandsstenarna nämner resor utanför Norden mer sällan än Svealandsstenarna ({n_(br['Götaland']['k'])} av "
                            f"{n_(br['Götaland']['n'])} mot {n_(br['Svealand']['k'])} av {n_(br['Svealand']['n'])}; oddskvot "
                            f"{_d(r['model']['or'], 2)} efter tid och ristare)" + (
                                f" – men när de gör det, säger {n_(gk)} av {n_(gn)}"
                                + ("" if aj else " med en enda riktning") + " att mannen dog utanför Norden."
                                if gn and gk / gn > 0.5 else ".")
                            + (" " + strict_text(r) + (" Skillnaden håller alltså också på de mer fullständiga stenarna, men "
                                                       "svagare." if holds_strict else " På de mer fullständiga stenarna "
                                                       "går skillnaden inte att säkerställa.") if sm.get("p") is not None else ""),
                    "note": "Färre resestenar kan betyda färre resor eller att resan bara berättades när den slutade i döden; "
                            "datan skiljer inte de två åt. " + legibility_text(m),
                    "significance": significance(r["model"]["p"], "p", "logistisk regression med ristaren som slumpeffekt")})
    return out


# A hypothesis for each kind of pattern, in the app's two vocabularies: a claim says "visar" or "är förenligt med", a
# hypothesis says "vi föreslår" or "kan tyda på". The hypothesis is bold on purpose; the test says what would show it
# wrong. (topic, key) → (hypothesis, test); a key such as "kinship:son" or "formula:1" also finds its kind
# ("kinship", "formula"), and (topic, None) is the default for the topic.
HYPOTHESES: dict[tuple[str, str | None], tuple[str, str]] = {
    ("Förändring", None): (
        "Vi föreslår att förändringen spreds som en ny vana – i skrift eller tro – genom ristarnätverken, och att den bars av "
        "nya ristargenerationer snarare än av enskilda ristare som bytte vana.",
        "Om det stämmer syns förändringen mellan ristare men svagt inom dem, och den börjar i en trakt för att spridas därifrån. "
        "Hypotesen faller om förändringen kommer samtidigt överallt och hos ristare i alla åldrar."),
    ("Förändring", "stungna"): (
        "Vi föreslår att prickningen spreds som en skriftreform med Mälardalens senare ristarskolor – först i enskilda "
        "formelord och sedan allmänt – snarare än som ett svar på ljudförändringar.",
        "De tidigaste stungna runorna bör samlas i formelord och hos ett fåtal ristare. Hypotesen faller om prickningen kommer "
        "samtidigt i alla ord och hos många ristare."),
    ("Förändring", "stungen_e"): (
        "Vi föreslår att stungen i först spreds som en skrivvana för æftiʀ, ett formelord som ristarna lärde sig som helhet, "
        "och först senare blev ett allmänt sätt att skilja e från i.",
        "Ristare som stinger i:et i æftiʀ bör inte göra det oftare i andra ord, och de tidigaste stungna i:na bör finnas i "
        "æftiʀ. Hypotesen faller om prickningen kommer samtidigt i alla ord."),
    ("Förändring", "stungen_y"): (
        "Stungen u kan ha införts för att skilja y från u där förväxling ändrade betydelsen, till exempel i namn.",
        "Stungen u bör först dyka upp i ord där y och u annars kan förväxlas; jämför ord för ord och ristare för ristare."),
    ("Förändring", "o_runa"): (
        "Vi föreslår att åsrunan fick en ny användning för /o/ medan den behöll den gamla för ą – användningen vidgades, "
        "värdet byttes inte ut.",
        "Om värdet byttes ut bör runan överges för ą när den tas i bruk för /o/; vidgades användningen, använder samma "
        "ristare den för båda samtidigt."),
    ("Förändring", "ai_alla"): (
        "Vi föreslår att diftongstavningen (stain) blev en skrivnorm i den sena uppländsk-sörmländska stenresningen, "
        "oberoende av uttalet.",
        "En skrivnorm bör spridas genom ristarskolor och synas mellan ristargenerationer; ett ljudbyte bör synas i alla ord "
        "och hos alla ristare samtidigt."),
    ("Förändring", "au_och"): (
        "Kortformen uk för 'och' kan vara en svagtonsreduktion eller en fast förkortning, inte ett tidigt belägg för "
        "monoftongeringen au > ø.",
        "Är det svagtonsreduktion bör uk vara vanligare än monoftong i betonade au-ord hos samma ristare."),
    ("Förändring", "r_for_R"): (
        "r för ʀ i æftiʀ kan spegla en lokal skrivvana snarare än att ʀ och r redan föll samman i talet.",
        "Ett sammanfall i talet bör också ge omvänd stavning (ʀ för r) hos samma ristare."),
    ("Förändring", "bon"): (
        "Vi föreslår att bönerna toppar när kristendomen behövde markeras och blir ovanligare när den blivit självklar.",
        "Om det stämmer bör nedgången komma tidigare där kyrkor byggdes tidigt och där kristna monument var många tidigt; "
        "det kan prövas mot de medeltida kyrkornas datering."),
    ("Förändring", "sjal"): (
        "Själsbönen kan ha en egen topp knuten till själagåvor som brobyggen, inte bara till bönerna i allmänhet.",
        "Jämför själsbönens topp med brostenarnas datering och med bönerna utan själ."),
    ("Förändring", "signatur"): (
        "Vi föreslår att signaturerna blev vanliga när runristning blev ett yrke, där ristare med många uppdrag satte sitt "
        "namn på verket.",
        "Signerade stenar bör samlas hos ristare med många stenar och i trakter där flera ristare var verksamma samtidigt."),
    ("Förändring", "bro"): (
        "Brobyggen som själagåva kan höra till en bestämd fas av kristnandet.",
        "Brostenarnas datering bör sammanfalla med själsbönernas topp."),
    ("Regional skillnad", None): (
        "Vi föreslår att skillnaden speglar regionala skrivtraditioner eller ristarskolor snarare än dialekt.",
        "Ristare som arbetade i båda landskapen visar vilket: behåller de sin form är det ristarens vana, följer de landskapet "
        "är det en lokal norm, kanske beställarnas."),
    ("Regional skillnad", "bon"): (
        "Vi föreslår att bönerna var en uppländsk sed som spreds genom Mälardalens tidiga kyrkliga miljöer.",
        "Nära tidiga kyrkor och Sigtuna bör bönerna vara vanligast; det kan prövas mot medeltida kyrkors läge och datering."),
    ("Regional skillnad", "sjal"): (
        "Själsbönen kan ha spridits från Uppland som en del av samma kyrkliga miljö som bönerna i allmänhet.",
        "Jämför själsbönens andel med avståndet till tidiga kyrkor, landskap för landskap."),
    ("Regional skillnad", "stungen_e"): (
        "Vi föreslår att stungen i nådde Östergötland och Västergötland före Uppland – en spridning norrut.",
        "De tidigaste stungna i:na i Götaland bör finnas hos ristare med kontakter söderut; hypotesen faller om dateringen "
        "där inte håller."),
    ("Regional skillnad", "cross"): (
        "Korset kan ha varit vanligare i Uppland för att kristnandet där tog sig uttryck i monument i större utsträckning.",
        "Jämför korsens andel med andra kristna markörer (böner) landskap för landskap; måttet är delvis inbyggt i "
        "stilgrupperna."),
    ("Geografi", "areas"): (
        "Vi föreslår att ristarna arbetade för beställare inom häradet – att stenresningen organiserades lokalt kring "
        "häradets nätverk.",
        "En ristare som arbetade i flera härad bör där följa släktnätverk, med samma personnamn på stenar i olika härad."),
    ("Geografi", "cult_prayer"): (
        "Vi föreslår att kristna böner sattes upp demonstrativt vid de gamla kultplatserna: det kristna budskapet "
        "markerades där den gamla tron hade haft sin plats, inte bara där eliten bodde.",
        "Om det stämmer bör bönestenarna vid kultnamnen höra till kristnandets tidiga skede och stå närmare platsen än "
        "gården; jämför med arkeologiskt undersökta kultplatser och med de medeltida kyrkornas ålder och läge."),
    ("Geografi", "cult_churches"): (
        "Kyrkan kan ha byggts vid den gamla kultplatsen för att ta över dess betydelse.",
        "Pröva med ett fullständigt register över medeltida kyrkor och deras äldsta byggnadsfas, och med undersökta "
        "kultplatser: ligger de äldsta kyrkorna närmast?"),
    ("Geografi", "prayer_early_churches"): (
        "Vi föreslår att de släkter som lät hugga böner på sina runstenar var de som byggde de första kyrkorna, på sin "
        "egen mark: bönen för den dödes själ är ett tidigt spår av den privata fromhet som behövde präst, kyrka och vigd "
        "jord. Korset var i stället ett offentligt tecken vid makten.",
        "Om det stämmer bör undersökningar under de tidiga kyrkorna nära bönestenar oftare visa träkyrkor eller kristna "
        "gravar från 1000-talet, och sambandet bör hålla med ett fullständigt register över kyrkornas äldsta byggnadsfas."),
    ("Geografi", "remains_graves"): (
        "Vi föreslår att gravfälten förblev släktens minnesplatser genom kristnandet: den kristna stenen restes där "
        "förfäderna låg, även när den döde själv kanske begravdes vid en kyrka.",
        "Jämför med gravfält där sena, kristna gravar (östvästliga skelettgravar) är undersökta: står kristna stenar oftare "
        "vid sådana gravfält levde gravfältet vidare; står de vid gravfält utan sena gravar var platsen ett minnesmärke."),
    ("Geografi", "remains_bridges"): (
        "Vi föreslår att bron var en del av en väg som redan fanns: själagåvan förbättrade en färdled som släkten och "
        "grannarna använde.",
        "Om det stämmer bör brostenarna ligga på linjer mellan gårdar, tingsplatser och kyrkor; en väganalys i terrängen "
        "(least-cost path) mellan brostenarna och bygdens centra kan visa det."),
    ("Geografi", "water_viking"): (
        "Om stenarna restes vid färdleder på vattnet bör de ha stått vid dåtidens stränder och vikar, och närheten bör vara "
        "störst där landhöjningen flyttat stranden mest.",
        "Pröva med SGU:s strandförskjutningsmodell och Lantmäteriets höjdmodell: skillnaden mot slumppunkterna bör bestå, "
        "och stenar vid forna vikar som nu är land bör ligga i rad längs den gamla stranden."),
    ("Geografi", "water"): (
        "Stenarna kan ha rests vid dåtidens vattenleder, som var viktigare färdvägar än i dag.",
        "Jämför med dåtidens strand: närheten bör bli större. En grov modell av strandlinjen omkring år 1000 redovisas som "
        "eget mönster; SGU:s strandförskjutningsmodell skulle ge en säkrare prövning."),
    ("Språk", "dialect"): (
        "Vi föreslår att stavningsgränserna följer ristarverkstäder och skrivtraditioner mer än dialekter.",
        "Gränserna bör sammanfalla med ristarnas verksamhetsområden; följer de i stället senare dialektgränser talar det för "
        "uttalet."),
    ("Datering", "seriation"): (
        "Språk och ornamentik kan ha förändrats i samma takt eftersom båda bars av samma ristarskolor.",
        "Pröva seriationen utanför Uppland: följer den stilgrupperna även där gäller kronologin bredare."),
    ("Formelval", "formula"): (
        "Vi föreslår att formelvalet var ristarens kännetecken lika mycket som ornamentiken – att ristare hade fasta formulär.",
        "Pröva på signerade stenar och på ristare som arbetade länge: ändrade de formulär över tid, eller följde de "
        "beställaren?"),
    ("Okända ristare", "anonymous"): (
        "Grupperna kan vara verkstäder eller ristare som forskningen inte har namngett.",
        "Jämför ornamentik, runformer och huggteknik på gruppens stenar; en verklig ristare bör synas i alla tre."),
    ("Samband", None): (
        "Vi föreslår att brobyggen var själagåvor och att själsbönen förstärkte budskapet.",
        "Brostenar med själsbön bör stå närmare kyrkor eller färdvägar till kyrkor än brostenar utan; det kan prövas mot "
        "medeltida kyrkors läge."),
    ("Släkt och formler", "kinship"): (
        "Förändringen i släktorden kan spegla nya sätt att visa arv och tillhörighet.",
        "Pröva inom landskap och mot arvsformlerna: följer släktorden arvsuppgifterna?"),
}


SHAPE_TEXT = {"rises": "blir vanligare över tid", "falls": "blir ovanligare över tid",
              "peak": "är vanligast omkring {y}", "trough": "är ovanligast omkring {y}", "flat": "förändras knappt"}
TIME_NOTE = ("Tiden bygger på Gräslunds stilgrupper (intervall, inte år) och gäller daterade stenar, främst i Uppland "
             "och Södermanland, där kronologin är utarbetad.")
# The caveat that fits the kind of feature: spelling, script, formula or ornament
TYPE_NOTE = {
    "språk": "Stavning kan spegla skrivtradition och ristarens skola lika mycket som uttal.",
    "skrift": "Runformerna kan spegla en skrivtradition eller en ristarskola lika mycket som en allmän förändring.",
    "kristnande": "Formelvalet kan spegla beställarens önskan, ristarens repertoar eller en lokal kyrklig miljö; enligt "
                  "korrespondensanalysen hänger formelvalet mer ihop med ristaren än med tiden.",
    "innehåll": "Formelvalet kan spegla beställarens önskan eller ristarens repertoar.",
    "språkbruk": "Ordvalet kan spegla ristarens eller traktens formulärbruk lika mycket som en språklig förändring.",
    "ornamentik": "Korset hör till bildkompositionen och därmed till ornamentiken som stilgrupperna – och dateringen – bygger "
                  "på; samband med tid är därför delvis inbyggda. Kors kan vara grunt huggna eller ligga på förlorade delar "
                  "och missas i äldre dokumentation, och stenar utan bedömbar ornamentik saknar ofta stilgrupp och faller "
                  "ur analysen.",
}
CARVER_NOTE = ("Ristarna kommer ur Rundatas attribueringar, som delvis bygger på stavning, formulärbruk och ornamentik. "
               "Att hålla ristaren konstant gör jämförelsen oftast försiktigare, men kan också snedvrida den; stenar utan "
               "ristare grupperas per socken som en grov ersättning.")
CHANGE_NOTE = TIME_NOTE + " " + CARVER_NOTE  # kept for older texts
KEY_GROUP = {"ai_alla": "språk", "au_och": "språk", "r_for_R": "språk", "o_runa": "språk", "h": "språk", "nasal": "språk",
             "preposition": "språkbruk", "stungna": "skrift", "stungen_e": "skrift", "stungen_y": "skrift", "stungen_g": "skrift",
             "bon": "kristnande", "sjal": "kristnande", "cross": "ornamentik", "bro": "innehåll", "signatur": "innehåll"}
OVERLAP = {"bon": "Själsbönen är en del av de kristna bönerna, så de två fynden mäter delvis samma sak.",
           "sjal": "Själsbönen är en del av de kristna bönerna, så de två fynden mäter delvis samma sak. Kors och böner "
                   "samvarierar också; en gemensam topp kan vara ett och samma kristna mönster, ett belägg och inte två.",
           "cross": "Kors och kristna böner samvarierar; en gemensam topp kan vara ett och samma kristna mönster, ett belägg och "
                    "inte två."}


def _notes(key: str) -> str:
    """Förbehållen för ett drag: tiden, dragets typ och ristarna (inte stavningsförbehållet för formler)."""
    parts = [TIME_NOTE, TYPE_NOTE.get(KEY_GROUP.get(key, ""), ""), OVERLAP.get(key, ""), CARVER_NOTE]
    return " ".join(x for x in parts if x)
# A significant change smaller than this (in share of stones) is reported as a weak effect
WEAK_EFFECT = 0.10
WEAK_NOTE = ("En liten men stabil förändring (under 10 procentenheter): ett mönster, men ett litet. Små förändringar i "
             "skrivvanor kan ändå vara historiskt betydelsefulla.")
# Changes that earlier research already describes: the contribution is the measurement with place and carver constant
KNOWN_CHANGES = {
    "stungna": ("rises", "Att stungna runor blir vanligare under 1000-talet är känt (se t.ex. Lagman 1990)."),
    "stungen_e": ("rises", "Att stungna runor blir vanligare under 1000-talet är känt (se t.ex. Lagman 1990)."),
    "stungen_y": ("rises", "Att stungna runor blir vanligare under 1000-talet är känt (se t.ex. Lagman 1990)."),
    "o_runa": ("rises", "Åsrunans övergång till o-ljud är beskriven (Williams 1990)."),
    "signatur": ("rises", "Att ristarsignaturer blir vanliga på de senare uppländska stenarna är känt."),
    "bon": (None, "Att kristna böner och formler hör till 1000-talets runstenar är känt."),
    "sjal": (None, "Att kristna böner och formler hör till 1000-talets runstenar är känt."),
    "cross": (None, "Korsens plats i 1000-talets runstenar är känd."),
}
# Features that are part of the ornament, whose style groups give the dates: their change is not independent of the dating
CIRCULAR = {"cross": "Korset är en del av ornamentiken, och tiden kommer ur ornamentikens stilgrupper; förändringen är därför "
                     "inte oberoende av dateringen."}


PROVINCE_FULL = {"U": "Uppland", "Sö": "Södermanland", "Ög": "Östergötland", "Vg": "Västergötland", "Sm": "Småland",
                 "Öl": "Öland", "G": "Gotland", "Vs": "Västmanland", "Nä": "Närke"}


def seriation_robust_text(rob: dict | None) -> str:
    """Seriationens överensstämmelse med Gräslund i varianter som prövar hur oberoende den är (r/chronology.R)."""
    if not rob:
        return ""
    parts = [f"{r['label']} rho {_d(r['rho'])}" + (f" ({r['groups']} grupper)" if r.get("groups") else "")
             for r in rob.values() if r.get("rho") is not None]
    return ("Överensstämmelsen i varianter som prövar oberoendet: " + "; ".join(parts) + "." if parts else "")


GENERATION_NOTE = ("Att trenden syns mellan ristare men inte tydligt inom dem är inget motbelägg: förändringen kan ha spridits "
                   "genom att nya ristargenerationer skrev annorlunda, snarare än att enskilda ristare bytte vana – i sig en "
                   "möjlig iakttagelse.")
TRIM_NOTE = ("Utan den tidigaste och senaste stilgruppen försvinner en stor del av tidsaxeln, så ett svagare resultat där är "
             "väntat och inget motbelägg.")


def _check_reading(weak_labels: list[str]) -> str:
    """Hur kontroller som inte når signifikans ska läsas: inom ristare och utan ändgrupperna besvarar andra frågor."""
    out = []
    if any("inom samma ristare" in x or "inom ristare" in x for x in weak_labels):
        out.append(GENERATION_NOTE)
    if any("utan den tidigaste" in x for x in weak_labels):
        out.append(TRIM_NOTE)
    return " ".join(out)


def checks_text(checks: dict | None, sign: int, what: str) -> str:
    """Hur en trend klarar kontrollerna: hur många varianter som går åt samma håll och är signifikanta, och vilka som
    inte gör det. sign: -1 om trenden är en minskning, +1 om en ökning."""
    tested = [c for c in (checks or {}).values() if c.get("tested")]
    if not tested:
        return ""
    same = [c for c in tested if c["b"] * sign > 0 and c["p"] < 0.05]
    weak = [c for c in tested if c["b"] * sign > 0 and c["p"] >= 0.05]
    other = [c for c in tested if c["b"] * sign <= 0]
    def lab(c):
        return c["label"] + (f" (n {c['n']}" + (f", {c['carvers']} ristare" if c.get("carvers") else "") + ")")
    reading = _check_reading([c["label"] for c in weak])
    return (f"Prövat på {len(tested)} sätt (rak trend): {what} signifikant i {len(same)}"
            + (f"; samma riktning men inte signifikant: {'; '.join(lab(c) for c in weak)}" if weak else "")
            + (f"; motsatt riktning: {'; '.join(lab(c) for c in other)}" if other else "") + "."
            + (f" {reading}" if reading else ""))


def _ends(by_style: list | None, key: str = "n", unit: str = "stenar") -> str:
    rows = [r for r in (by_style or []) if r.get(key)]
    if len(rows) < 2:
        return ""
    return ("Underlaget per stilgrupp: " + ", ".join(f"{r['style']} {_pct(r.get('share') or r.get('share_words'))} "
                                                       f"({r[key]} {unit})" for r in rows) + ".")


def dotted_text(rob: dict | None) -> str:
    if not rob or rob.get("error"):
        return ""
    out = [checks_text(rob.get("checks"), +1, "stungna runor blir vanligare")]
    pr = [r for r in rob.get("per_rune") or [] if r.get("tested")]
    if pr:
        out.append("Per runa, bland ord där den stungna runan kan förväntas: " + "; ".join(
            f"{r['label']} {_pct(r['share'])} av {r['words']} ord, "
            + ("ökar signifikant" if r["b"] > 0 and r["p"] < 0.05 else "ökar inte signifikant" if r["b"] > 0 else "ökar inte")
            for r in pr) + ".")
    yw = rob.get("y_writing") or []
    if yw:
        out.append("Ljudet y skrivs " + ", ".join(f"i {r['style']} {_pct(r['dotted'])} med stungen u, {_pct(r['u'])} med u"
                                                  for r in yw if r.get("words", 0) >= 5) + ".")
    j = rob.get("joint_monophthong") or {}
    if j.get("tested"):
        out.append("På stennivå, med tiden konstant, har stenar med stungna runor "
                   + ("färre" if j["b"] < 0 else "fler") + f" monoftongstavningar (oddskvot {_d(math.exp(j['b']))}, p {_q(j['p'])}; "
                   f"{_pct(j['mono_with_dot'])} mot {_pct(j['mono_without_dot'])})"
                   + (" – i linje med en gemensam rörelse mot fullständigare stavning." if j["b"] < 0 and j["p"] < 0.05 else "."))
    return " ".join(x for x in out if x)


def prayer_text(rob: dict | None) -> str:
    if not rob or rob.get("error"):
        return ""
    out = []
    it = rob.get("intact") or {}
    if it.get("tested"):
        out.append(f"På stenar med bevarat inskriftsslut (n {it['n']}) går trenden "
                   + ("åt samma håll" if it["b"] < 0 else "åt motsatt håll") + (" och är signifikant." if it["p"] < 0.05 else ", men är inte signifikant."))
    w = rob.get("wording") or []
    if w:
        out.append(f"Ordvalet: sál i {_pct(rob.get('share_sal'))} av {rob.get('n_prayers')} själsböner, Guðs móðir i "
                   f"{_pct(rob.get('share_gudsmodir'))}; per stilgrupp " + ", ".join(f"{r['style']} {_pct(r['sal'])} sál ({r['prayers']})"
                                                                               for r in w if r.get("prayers", 0) >= 5) + ".")
    st = rob.get("sal_trend") or {}
    if st.get("tested"):
        out.append("Sál " + ("ökar" if st["b"] > 0 else "minskar") + " på and/ônds bekostnad över tid"
                   + (" (signifikant)." if st["p"] < 0.05 else " (inte signifikant)."))
    return " ".join(out)


def r_text(rob: dict | None) -> str:
    if not rob or rob.get("error"):
        return ""
    parts = []
    for k in ("eftir", "other", "reverse"):
        c = rob.get(k) or {}
        if c.get("words"):
            trend = ("" if not c.get("tested") else
                     ", " + ("ökar" if c["b"] > 0 else "minskar") + (" signifikant" if c["p"] < 0.05 else " inte signifikant"))
            parts.append(f"{c['label']} {_pct(c['share'])} av {c['words']} ord{trend}")
    return ("Ord för ord: " + "; ".join(parts) + ". Omvänd stavning (ʀ för r) är ett bättre mått på ett sammanfall i talet "
            "än r för ʀ ensamt." if parts else "")


def spelling_text(sp: dict | None, key: str) -> str:
    """Ordbaserade andelar för åsrunan (också för ą), stungen i (æftiʀ för sig) och skrivningarna av 'och'."""
    if not sp or sp.get("error"):
        return ""
    def trend(c):
        return ("" if not c.get("tested") else ", " + ("ökar" if c["b"] > 0 else "minskar")
                + (" signifikant" if c["p"] < 0.05 else " inte signifikant"))
    if key == "o_runa":
        o, a = sp.get("o") or {}, sp.get("nasal") or {}
        if not o.get("words"):
            return ""
        return (f"Ord för ord: åsrunan för /o/ i {_pct(o['share'])} av {o['words']} ord med /o/{trend(o)}; för ursprungligt ą "
                f"(and/ônd) i {_pct(a.get('share'))} av {a.get('words')} ord{trend(a)}. Bara ord med etymologiskt /o/ "
                "(broður, bonda, moður, sun, kona) räknas, inte ônd. Om runan överges för ą medan den tas i bruk för /o/ har "
                "värdet förskjutits; annars har användningen bara vidgats.")
    if key == "stungen_e":
        e1, e2 = sp.get("e_eftir") or {}, sp.get("e_other") or {}
        if not e1.get("words"):
            return ""
        return (f"Ord för ord bland ord med e/æ: i æftiʀ {_pct(e1['share'])} av {e1['words']}{trend(e1)}; i andra ord "
                f"{_pct(e2.get('share'))} av {e2.get('words')}{trend(e2)}. æftiʀ redovisas för sig eftersom Södermanland ofta "
                "skriver at i stället, vilket ändrar nämnaren mellan landskapen.")
    if key == "au_och":
        oc = sp.get("och") or {}
        rows = oc.get("by_style") or []
        if not rows:
            return ""
        return ("'och' per förekomst och stilgrupp: " + "; ".join(
            f"{r['style']} auk {_pct(r.get('och_auk'))}, uk {_pct(r.get('och_uk'))}, ok {_pct(r.get('och_ok'))}"
            for r in rows if r.get("words", 0) >= 10) + ". Draget räknar allt utan au som monoftong, också ok med åsrunan.")
    return ""


AU_NOTE = ("'och' står nästan alltid obetonat, och obetonade funktionsord reduceras eller förkortas oberoende av den allmänna "
           "ljudutvecklingen; uk kan därför spegla svagtonsreduktion eller en fast förkortad skrivning snarare än "
           "monoftongeringen au > ø, som dessutom slår igenom senare än ai > ē.")


def ai_robustness_text(rob: dict | None) -> str:
    """De kontroller som en runolog bad om för monoftongen i æi-ord (r/change.R, ai_checks): åt vilket håll trenden går i
    varje variant och om den är signifikant."""
    checks = (rob or {}).get("checks") or {}
    tested = [(k, c) for k, c in checks.items() if c.get("tested")]
    if not tested:
        return ""
    same = [c for _, c in tested if c["b"] < 0 and c["p"] < 0.05]
    weak = [c for _, c in tested if c["b"] < 0 and c["p"] >= 0.05]
    other = [c for _, c in tested if c["b"] >= 0]
    def lab(c):
        return f"{c['label']} (n {c['n']})"
    text = (f"Prövat på {len(tested)} sätt (rak trend, logodds per 50 år): monoftongstavningen blir signifikant ovanligare "
            f"{len(same)} gånger"
            + (f"; samma riktning men inte signifikant: {'; '.join(lab(c) for c in weak)}" if weak else "")
            + (f"; motsatt riktning: {'; '.join(lab(c) for c in other)}" if other else "") + ".")
    reading = _check_reading([c["label"] for c in weak])
    if reading:
        text += f" {reading}"
    w = checks.get("within") or {}
    if w.get("tested"):
        text += (f" Inom samma ristare ({w['carvers']} ristare med stenar i minst två stilgrupper) går trenden "
                 + ("åt samma håll" if w["b"] < 0 else "åt motsatt håll")
                 + (" och är signifikant." if w["p"] < 0.05 else ", men är inte signifikant – se ovan om generationsskifte."))
    if rob.get("share_sten") is not None:
        text += f" Ordet stæinn står för {round(rob['share_sten'] * 100)} % av de {rob['n_words']} æi-orden."
    bs = [r for r in rob.get("by_style") or [] if r.get("mono_i") is not None]
    if bs:
        text += (" Monoftongen räknas både som i (stin) och som stungen i (sten), så en övergång från stin till sten döljs inte; "
                 "per stilgrupp: " + ", ".join(f"{r['style']} i {_pct(r['mono_i'])} och e {_pct(r['mono_e'])}" for r in bs) + ".")
    return text


DOTTED_NOTE = ("Stingningar är små och kan försvinna i vittring eller förväxlas med vittringsgropar; äldre stenar är oftare "
               "vittrade och dokumenterade med äldre metoder, så stungna runor kan vara underskattade i de tidiga grupperna – "
               "en 3D-kontroll av ett urval tidiga stenar kan visa det. Seriationen använder också stungna runor, så "
               "resultaten är inte oberoende.")
BREAKDOWN_NOTE = ("En nedbrytning av resultatet för stungna runor, inte ett separat belägg; ordbaserade andelar per runa, bland "
                  "ord där den stungna runan kan förväntas, redovisas under stungna runor.")
R_NOTE = ("Om stavningen speglade uttalet borde r för ʀ öka över tid när ʀ faller samman med r; en topp går inte ihop med en "
          "enkel ljudhistorisk förklaring. ʀ- och r-runan är lätta att förväxla på vittrade stenar.")
AI_NOTE = ("Riktningen går emot den väntade ljudutvecklingen: monoftongeringen ai > ē sprids över tid och fornsvenskan får "
           "genomgående monoftong. Det talar för en förklaring i skrivvanan snarare än i uttalet – en normering mot stain i "
           "den sena uppländsk-sörmländska stenresningen, en minskande benägenhet att skriva diftongen defektivt (det är "
           "omdiskuterat om stin alls betecknar monoftong) eller skoltraditioner som slår igenom. Resultatet visar inte att "
           "uttalet förändrades och säger inget om trakter utan utarbetad stilkronologi.")


def _pair_p(a: dict, b: dict) -> float | None:
    """Ungefärligt p för skillnaden mellan två landskap, ur deras 95 %-intervall på logitskalan."""
    try:
        def se(r):
            return (math.log(r["hi1050"] / (1 - r["hi1050"])) - math.log(r["lo1050"] / (1 - r["lo1050"]))) / (2 * 1.96)
        def lg(x):
            return math.log(x / (1 - x))
        z = (lg(a["share1050"]) - lg(b["share1050"])) / math.sqrt(se(a) ** 2 + se(b) ** 2)
        return 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
    except (KeyError, ValueError, ZeroDivisionError, TypeError):
        return None


def _peak(t: dict) -> str:
    """Toppåret med intervall (t.ex. 'omkring 1033, 95 % intervall 1010–1060'), aldrig ett exakt år ensamt."""
    y = t.get("peak_year")
    if t.get("peak_lo") is not None and t.get("peak_hi") is not None:
        return f"{y} (95 % intervall {t['peak_lo']}–{t['peak_hi']})"
    return str(y)


def _amplitude(t: dict) -> float:
    curve = [r["share"] for r in t.get("curve") or [] if r.get("share") is not None]
    if t.get("shape") in ("peak", "trough") and curve:
        return max(curve) - min(curve)
    return abs((t.get("last") or 0) - (t.get("first") or 0))


def _q(q: float) -> str:
    return "< 0,001" if q < 0.001 else _d(q, 3)


MID_MIN = 10  # fewer stones from the middle of the period than this: no estimate is reported for the province
MID_NOTE = ("Mittperioden är stenar vars stilgrupp omfattar år 1050; antalet anger hur många sådana stenar landskapet har. "
            "Landskap med färre än %d sådana stenar redovisas som otillräckligt underlag, utan skattning." % MID_MIN)


def _too_few(r: dict) -> bool:
    return r.get("n_mid") is not None and r["n_mid"] < MID_MIN


def _province_share(r: dict) -> str:
    """Ett landskaps skattade andel år 1050 med intervall och underlag; för få stenar ger ingen skattning."""
    if _too_few(r):
        return f"{r['province']} otillräckligt underlag ({r['n_mid']} stenar från mittperioden)"
    parts = []
    if r.get("lo1050") is not None and r.get("hi1050") is not None:
        parts.append(f"{_pct(r['lo1050'])}–{_pct(r['hi1050'])}")
    if r.get("n_mid") is not None:
        parts.append(f"{r['n_mid']} stenar från mittperioden")
    return f"{r['province']} {_pct(r['share1050'])}" + (f" ({', '.join(parts)})" if parts else "")


BH_NOTE = ("Mönstret klarar Benjamini–Hochberg, som begränsar andelen falska upptäckter bland de redovisade, men inte den "
           "striktare Holm-justeringen: en upptäckt att pröva, inte ett bekräftat resultat.")


def _halves_text(h: dict | None) -> str:
    """Om mönstret håller i båda halvorna av korpusen (uppdelad per socken, r/change.R)."""
    if not h:
        return ""
    parts = [f"{k}: p {_q(x['p'])}" for k, x in (("A", h.get("A") or {}), ("B", h.get("B") or {})) if x.get("tested")]
    if h.get("replicated"):
        return f" Håller i båda halvorna av korpusen, uppdelad per socken ({'; '.join(parts)})."
    return (f" Håller inte i båda halvorna av korpusen, uppdelad per socken ({'; '.join(parts)})." if parts else
            " Kunde inte prövas i halvorna av korpusen (för få stenar).")


def change_patterns(ch: dict) -> list[dict]:
    """Mönster ur förändringsmodulen (r/change.R): drag som förändras över tid, skillnader mellan landskap och
    bro- och vägstenarnas kristna drag. Bara Holm-justerade resultat under 0,05."""
    out = []
    # Several features peaking in the same years may reflect where the data are densest, not the features
    peaks = [(f["label"].split(" (")[0], (f.get("time") or {}).get("peak_year")) for f in ch.get("features") or []
             if (f.get("time") or {}).get("shape") in ("peak", "trough") and (f.get("time") or {}).get("q") is not None
             and f["time"]["q"] < 0.05]
    peak_years = [y for _, y in peaks if y]
    crowd = None
    for y0 in peak_years:
        near = [lbl for lbl, y in peaks if y and abs(y - y0) <= 10]
        if len(near) >= 3 and (crowd is None or len(near) > len(crowd[1])):
            crowd = (y0, near)
    for f in ch.get("features") or []:
        t = f.get("time") or {}
        q_disc = t.get("q_bh", t.get("q"))
        if t.get("tested") and q_disc is not None and q_disc < 0.05:
            holm_ok = t.get("q") is not None and t["q"] < 0.05
            halves = t.get("halves") or {}
            tested_halves = bool(halves)
            replicated = bool(halves.get("replicated"))
            dr = t.get("draws") or {}
            robust = (f" {round((dr.get('share_sig') or 0) * dr['n'])} av {dr['n']} omräkningar med årtal dragna inom "
                      "stilgruppernas intervall gav också ett signifikant samband." if dr.get("n") else "")
            kn = KNOWN_CHANGES.get(f["key"])
            known = bool(kn) and (kn[0] is None or kn[0] == t["shape"])
            weak = _amplitude(t) < WEAK_EFFECT
            # Unstable when the years are redrawn within the style groups: an indication, not a pattern
            unstable = dr.get("n") and (dr.get("share_sig") or 0) < 0.8
            humped = t["shape"] in ("peak", "trough")
            edge = humped and t.get("peak_lo") is not None and (t["peak_lo"] <= t["year_first"] or t["peak_hi"] >= t["year_last"])
            status = ("begränsning" if f["key"] in CIRCULAR else "indikation" if unstable or edge
                      else "bekräftar" if known else "mönster att pröva")
            # Confirmed needs Holm and both halves of the corpus; a new pattern needs both halves to be called clear
            if status == "bekräftar" and not (holm_ok and (replicated or not tested_halves)):
                status = "indikation"
            elif status == "mönster att pröva" and tested_halves and not replicated:
                status = "indikation"
            half_txt = _halves_text(halves)
            shape_txt = (f"förändras, men toppens läge går inte att bestämma (95 % intervall {t['peak_lo']}–{t['peak_hi']} når "
                         "periodens kant)" if edge else SHAPE_TEXT[t["shape"]].format(y=_peak(t)))
            peak_txt = (f" Som {'mest' if t['shape'] == 'peak' else 'minst'} {_pct(t.get('peak_share') if t['shape'] == 'peak' else t.get('trough_share'))}"
                        + (f"; {'toppen' if t['shape'] == 'peak' else 'dalen'} hamnar {', '.join(str(y) for y in t['refit_peaks'])} i omräkningarna med nya årtal"
                           if t.get("refit_peaks") else "") + "." if humped and not edge else "")
            last_all = max(((x.get("time") or {}).get("year_last") or 0) for x in ch.get("features") or [])
            end_txt = (f"Kurvan slutar omkring {t['year_last']} eftersom senare stilgrupper har färre än 20 stenar där draget "
                       "kan bestämmas." if t.get("year_last") and t["year_last"] < last_all else "")
            size_txt = (f" Tidsförändringen spänner {_d(t['time_logit_range'])} logitenheter, mot en standardavvikelse på "
                        f"{_d(t['carver_sd'])} mellan ristare." if t.get("time_logit_range") is not None and t.get("carver_sd") is not None else "")
            specific = {"ai_alla": AI_NOTE + " " + ai_robustness_text(ch.get("ai_robustness")),
                        "stungna": dotted_text(ch.get("dotted_robustness")) + " " + DOTTED_NOTE,
                        "stungen_e": BREAKDOWN_NOTE + " " + spelling_text(ch.get("spelling_robustness"), "stungen_e"),
                        "stungen_y": BREAKDOWN_NOTE, "stungen_g": BREAKDOWN_NOTE,
                        "sjal": prayer_text(ch.get("prayer_robustness")),
                        "o_runa": spelling_text(ch.get("spelling_robustness"), "o_runa"),
                        "au_och": AU_NOTE + " " + spelling_text(ch.get("spelling_robustness"), "au_och"),
                        "r_for_R": r_text(ch.get("r_robustness")) + " " + R_NOTE}.get(f["key"], "")
            note = " ".join(x for x in [
                specific, _ends(t.get("by_style")), end_txt,
                (f"Flera drag har sin topp omkring {crowd[0]} ({', '.join(crowd[1])}); det kan spegla var underlaget är "
                 "tätast eller hur stilgrupperna översätts till år snarare än något i dragen själva.")
                if crowd and humped and f["label"].split(" (")[0] in crowd[1] else "",
                size_txt.strip(),
                WEAK_NOTE if weak else "",
                (f"Bara {round((dr.get('share_sig') or 0) * dr['n'])} av {dr['n']} omräkningar med nya årtal höll – en "
                 "indikation, inte ett stabilt mönster.") if unstable and not weak else "",
                CIRCULAR.get(f["key"], ""),
                (kn[1] + " Bidraget här är mätningen med plats och ristare konstanta.") if known else "",
                _notes(f["key"])] if x)
            q_show = t["q"] if holm_ok else q_disc
            out.append({"key": f["key"], "topic": "Förändring", "status": status, "small": bool(weak),
                        "replicated": replicated if tested_halves else None,
                        "text": f"{f['label']} {shape_txt}, med plats och ristare "
                                f"konstanta: {_pct(t['first'])} omkring {t['year_first']} och {_pct(t['last'])} omkring "
                                f"{t['year_last']} (q {_q(q_show)}).{peak_txt}{robust}{half_txt}",
                        "note": note + ("" if holm_ok else " " + BH_NOTE),
                        "significance": (significance(t["q"], "q", "logistisk regression (mgcv), Holm") if holm_ok else
                                         significance(q_disc, "q", f"logistisk regression (mgcv), Benjamini–Hochberg; "
                                                                   f"med Holm q {_q(t['q'])}"))})
        pv = f.get("provinces") or {}
        rows = pv.get("rows") or []
        q_holm = pv.get("q_differ", pv.get("p_differ"))
        q_prov = pv.get("q_bh_differ", q_holm)
        if len(rows) >= 2 and q_prov is not None and q_prov < 0.05:
            holm_prov = q_holm is not None and q_holm < 0.05
            # The pair shown is chosen among provinces with enough stones from the middle of the period: extremes among
            # small groups are often chance (the winner's curse), and q tests the provinces together, not the pair
            adequate = [r for r in rows if (r.get("n_mid") or 0) >= 15]
            pool = adequate if len(adequate) >= 2 else [r for r in rows if not _too_few(r)] or rows
            hi = max(pool, key=lambda r: r["share1050"]); lo = min(pool, key=lambda r: r["share1050"])
            p_pair = _pair_p(hi, lo)
            monotone = t.get("tested") and t.get("q") is not None and t["q"] < 0.05 and t.get("shape") in ("rises", "falls")
            cross = [r for r in rows if r.get("cross_year")] if monotone else []
            ctext = (" Draget passerar hälften av stenarna " + ", ".join(
                f"omkring {r['cross_year']} i {r['province']}" + (f" ({r['cross_lo']}–{r['cross_hi']})" if r.get("cross_lo") else "")
                for r in sorted(cross, key=lambda r: r["cross_year"])) + "."
                     if len(cross) >= 2 else "")
            all_txt = "; ".join(_province_share(r) for r in sorted(rows, key=lambda r: (_too_few(r), -r["share1050"])))
            nocarver = pv.get("p_differ_nocarver")
            holds = nocarver is None or nocarver < 0.05
            known_geo = f["key"] in ("ai_alla", "ai_sten", "au_och")
            outside = [r["province"] for r in (hi, lo) if r["province"] not in ("U", "Sö")]
            few = [f"{'ingen' if r['n_carvers'] == 0 else r['n_carvers']} i {PROVINCE_FULL.get(r['province'], r['province'])}"
                   for r in (hi, lo) if r.get("n_carvers") is not None and r["n_carvers"] < 3]
            thin = [f"{r['n_mid']} i {PROVINCE_FULL.get(r['province'], r['province'])}" for r in (hi, lo)
                    if r.get("n_mid") is not None and r["n_mid"] < 15]
            notes = []
            if known_geo:
                notes.append("Monoftongeringens geografi – vanligare skriven i Götaland än i Mälardalen – är känd"
                             + ("; bidraget är mätningen med ristare konstanta." if not few else
                                ", men där attribuerade ristare saknas är jämförelsen i praktiken en jämförelse mellan "
                                "socknar, inte med ristare konstanta."))
            elif len(cross) >= 2:
                early = [r["province"] for r in sorted(cross, key=lambda r: r["cross_year"])[:2]]
                notes.append("Förloppet mellan landskapen är det intressanta, men inte helt självständigt: "
                             + (f"de tidigaste åren kommer från {' och '.join(PROVINCE_FULL.get(x, x) for x in early)}, där "
                                "dateringen är osäkrast, stenar med sparsam ornamentik kan ha daterats med hjälp av runformerna "
                                "och de stilgruppsbestämda stenarna kanske inte är representativa. "
                                if any(x not in ("U", "Sö") for x in early) else "")
                             + "Skillnader mellan passageår som är mindre än stilgruppernas upplösning går inte att tolka. "
                             "Ett landskap där draget tidigt är vanligt kan vara där förändringen började, men också där en "
                             "ristarskola hade sina vanor.")
            else:
                humped = (t.get("tested") and t.get("q") is not None and t["q"] < 0.05 and t.get("shape") in ("peak", "trough"))
                notes.append("En regional skillnad, inte ett spridningsförlopp"
                             + (". Draget har en topp mitt i perioden, så dateringsfel får riktad verkan: stenar som felaktigt "
                                "förs till mittperioden sänker eller höjer andelen beroende på var de egentligen hör hemma."
                                if humped else "."))
            if outside:
                sh = pv.get("shifted") or {}
                sh_txt = ""
                if sh.get("earlier") and sh.get("later"):
                    held = all((sh[k].get("p") or 1) < 0.05 for k in ("earlier", "later"))
                    sh_txt = (" Med dessa landskaps stenar daterade 25 år tidigare respektive senare "
                              + ("består skillnaden" if held else "består skillnaden inte i båda fallen") + ".")
                notes.append(f"Jämförelsen gäller {' och '.join(PROVINCE_FULL.get(x, x) for x in outside)}, där Gräslunds "
                             "kronologi är minst prövad (den är utarbetad för Uppland); dateringen är där osäkrare." + sh_txt)
            if few:
                notes.append(f"Jämförelsen vilar på få attribuerade ristare ({', '.join(few)}); ristar- och verkstadseffekter "
                             "kan inte skiljas från landskapet.")
            if thin:
                notes.append(f"Få stenar från mittperioden ({', '.join(thin)}); andelarna är osäkra.")
            cbth = pv.get("carvers_both") or {}
            if cbth and {hi["province"], lo["province"]} == {"U", "Sö"}:
                notes.append(f"{cbth['carvers']} ristare har stenar i både Uppland och Södermanland; på deras egna stenar är "
                             f"andelen {_pct(cbth['share_So'])} i Södermanland ({cbth['n_So']} stenar) och {_pct(cbth['share_U'])} "
                             f"i Uppland ({cbth['n_U']})"
                             + (" – de följer landskapet, vilket talar för en lokal norm (kanske beställarnas)"
                                if abs((cbth['share_So'] or 0) - (cbth['share_U'] or 0)) >= 0.15 else
                                " – de behåller sin form, vilket talar för ristarens egen vana")
                             + (f"; med bara {cbth['carvers']} ristare är det ett svagt belägg." if cbth["carvers"] < 5 else "."))
            if not holds:
                notes.append(f"Utan ristaren i modellen är skillnaden inte signifikant (p {_q(nocarver)}); resultatet beror på "
                             "hur attribueringarna gjorts.")
            notes.append(MID_NOTE)
            notes.append("Modellen använder alla daterade stenar i landskapen med tiden i modellen; år 1050 är bara den punkt "
                         "där landskapen jämförs. q gäller den samlade skillnaden mellan landskapen; märket gäller det visade "
                         "paret (ojusterat p, paret är utvalt).")
            notes.append(_notes(f["key"]))
            pair_ok = p_pair is not None and p_pair < 0.05
            # Outside Uppland and Södermanland the dating is less certain; a difference that holds with those stones
            # dated 25 years earlier and later is not a hidden time effect
            sh = pv.get("shifted") or {}
            shift_held = bool(sh.get("earlier") and sh.get("later")) and all(
                (sh[k].get("p") or 1) < 0.05 for k in ("earlier", "later"))
            ph = pv.get("halves") or {}
            tested_h = bool(ph)
            rep_prov = tested_h and all(
                (ph.get(k) or {}).get("tested") and ph[k]["p"] < 0.05
                and ((ph[k].get("level") or {}).get(hi["province"]) or 0) > ((ph[k].get("level") or {}).get(lo["province"]) or 1)
                for k in ("A", "B"))
            status = ("bekräftar" if known_geo and holds and pair_ok and holm_prov and (rep_prov or not tested_h) else
                      "mönster att pröva" if (holds and pair_ok and not thin and not few and (not outside or shift_held)
                                              and (rep_prov or not tested_h)) else "indikation")
            if tested_h:
                parts = [f"{k}: p {_q(ph[k]['p'])}" for k in ("A", "B") if (ph.get(k) or {}).get("tested")]
                notes.append(("Skillnaden mellan paret håller i båda halvorna av korpusen, uppdelad per socken"
                              if rep_prov else "Skillnaden håller inte i båda halvorna av korpusen, uppdelad per socken")
                             + (f" ({'; '.join(parts)})." if parts else "."))
            if not holm_prov:
                notes.append(BH_NOTE)
            out.append({"key": f["key"], "topic": "Regional skillnad", "status": status,
                        "replicated": rep_prov if tested_h else None, "pair": [hi["province"], lo["province"]],
                        "text": f"{f['label']}: landskapen skiljer sig (q {_q(q_prov)} för den samlade skillnaden, justerat för "
                                f"alla drag). Skattat för år 1050 och en typisk ristare: {all_txt}. Bland landskap med "
                                f"tillräckligt underlag störst skillnad mellan {hi['province']} och {lo['province']}"
                                + (f" (p {_q(p_pair)} för paret)" if p_pair is not None else "") + f".{ctext}",
                        "note": " ".join(notes),
                        "significance": significance(p_pair, "p", f"paret {hi['province']}–{lo['province']}, ojusterat; den "
                                                               f"samlade skillnaden q {_q(q_prov)}")})
    n_assoc = len(ch.get("assoc") or [])
    for a in ch.get("assoc") or []:
        al = a.get("all") or {}
        q_a = al.get("q_bh", al.get("q"))
        if q_a is not None and q_a < 0.05:
            dt, ln, it = a.get("dated") or {}, a.get("length") or {}, a.get("intact") or {}
            lt = a.get("length_total") or {}
            ah = a.get("halves") or {}
            lc, lp = a.get("loo_carver") or {}, a.get("loo_parish") or {}
            checks = [(f"med tiden konstant (daterade stenar, n {dt.get('n')})", dt),
                      ("med textlängden utan bro- och bönefraserna konstant" if lt else "med textlängden konstant", ln),
                      (f"bara stenar med bevarat slut (n {it.get('n')})", it)]
            held = [lbl for lbl, c in checks if c.get("p") is not None and c["p"] < 0.05 and c.get("or", 1) > 1]
            lost = [f"{lbl} (oddskvot {_d(c['or'])}, p {_q(c['p'])})" for lbl, c in checks
                    if c.get("p") is not None and not (c["p"] < 0.05 and c.get("or", 1) > 1)]
            fragile = bool(lost) or (lc.get("min_or") is not None and lc["min_or"] <= 1) or al.get("lo", 0) < 1.2
            spread = (f" Brostenarna med draget ({a.get('k_x')}) fördelar sig på {a.get('n_carvers_x')} ristare och "
                      f"{a.get('n_parishes_x')} socknar" + (f"; med en ristare i taget utelämnad ligger oddskvoten mellan "
                                                            f"{_d(lc['min_or'])} och {_d(lc['max_or'])}" if lc else "")
                      + (f", med en socken i taget mellan {_d(lp['min_or'])} och {_d(lp['max_or'])}" if lp else "") + ".")
            failed = [(lbl, c) for lbl, c in checks if c.get("p") is not None and not (c["p"] < 0.05 and c.get("or", 1) > 1)]
            worst = max(failed, key=lambda x: x[1]["p"]) if failed else None
            if lt.get("p") is not None:
                spread += (f" Med hela textlängden konstant, som också räknar brofrasen själv: oddskvot {_d(lt['or'])}, "
                           f"p {_q(lt['p'])}.")
            spread += _halves_text(ah)
            replicated_a = bool(ah.get("replicated"))
            out.append({"key": a.get("key"), "topic": "Samband",
                        "status": "indikation" if fragile or (ah and not replicated_a) else "bekräftar",
                        "replicated": replicated_a if ah else None,
                        "text": f"{a['label']}: {_pct(a['share_x'])} mot {_pct(a['share_other'])} på andra stenar "
                                f"(oddskvot {_d(al['or'])}, 95 % KI {_d(al['lo'])}–{_d(al['hi'])}, q {_q(al['q'])}; en av "
                                f"{n_assoc} prövade kombinationer av stentyp och drag, Holm), med plats och ristare konstanta."
                                + (f" Håller {', '.join(held)}." if held else "")
                                + (f" Håller inte {', '.join(lost)}." if lost else "") + spread,
                        "note": "Ett samband mellan stentyp och formel, inte en förändring över tid. Förenligt med tolkningen "
                                "av brobyggen som kristna, själagagnande verk – det stöder tolkningen snarare än bekräftar den: "
                                "omkring tre av fyra brostenar saknar bön, och brobyggets religiösa innebörd framgår tydligare "
                                "av avsiktsfraserna (fyrir and hans), som inte räknas som bön här. Brostenarna känns igen på "
                                "texten (bro eller väg), inte på fyndplatsen. Brostenarna är få, så några ristare eller socknar "
                                "kan bära mycket av effekten.",
                        # A control that fails decides the badge: the association is not called significant when it
                        # disappears with, for example, the text length held constant
                        "significance": (significance(worst[1]["p"], "p", f"{worst[0]}; huvudmodellen q {_q(al['q'])}")
                                         if worst else significance(al["q"], "q", "logistisk regression (mgcv), Holm"))})
    return out
