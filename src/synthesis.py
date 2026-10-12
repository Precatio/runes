"""Syntes av belägg för ristarattribuering.

Tre oberoende källor vägs samman: Rundata (litteraturen), ortografisk stilometri och huggteknik mot den
delade mätkorpusen. Vikterna för ortografi och huggteknik skalas med metodens korsvaliderade träffsäkerhet
i just det fallet, så att ett svagt belägg inte väger lika tungt som ett starkt. Varje kandidat prövas
dessutom mot geografi (ristarens kända stenar), ristarens stilgrupper (och därmed datering) och – om
kandidatens stenar finns uppmätta – ett permutationstest sten mot sten. Motsägelser mellan källorna
redovisas uttryckligen. Inga sannolikheter anges.
"""
from __future__ import annotations

import math
from collections import Counter

import numpy as np

from src import geology
from src.language_profile import carver_profile, compare as compare_language, traits as language_traits
from src.orthography import OrthographyModel
from src.research_gaps import certain_carvers, province
from src.stats import METRICS, attribute, multivariate_permutation_test, summarize
from src.styles import BY_CODE

MIN_WORDS = 8
STRENGTH_PLURAL = {"stark": "starka", "måttlig": "måttliga", "svag": "svaga"}  # shorter texts give unreliable orthographic rankings


def _d(v: float, digits: int = 2) -> str:
    return f"{v:.{digits}f}".replace(".", ",")


def smoothed_precision(stats: dict | None) -> float:
    """Precision med Laplace-utjämning: (rätt + 1) / (föreslagna + 2). Ett fåtal förslag ger då inte 100 %."""
    stats = stats or {}
    n = stats.get("predicted") or 0
    correct = (stats.get("precision") or 0) * n
    return (correct + 1) / (n + 2)


def _length_factor(n_words: int) -> float:
    return 1.0 if n_words >= 12 else 0.7 if n_words >= MIN_WORDS else 0.3


# ---- measurements --------------------------------------------------------------------------

def complete(slices: list[dict]) -> list[dict]:
    return [s for s in slices if all(s.get(m) is not None and np.isfinite(s[m]) for m in METRICS)]


def means(slices: list[dict]) -> list[float] | None:
    s = complete(slices)
    return [float(np.mean([x[m] for x in s])) for m in METRICS] if s else None


def measurement_summary(analyses: list[dict]) -> dict:
    """Mått per spårtyp ur den senaste analysen av varje typ (inga dubbletter av samma analys)."""
    latest: dict[str, dict] = {}
    for a in analyses:
        latest[a.get("feature_type") or "unknown"] = a
    return {ft: {"n": len(complete(a.get("slices") or [])), "analysis_id": a.get("id"), "saved_at": a.get("savedAt"),
                 "summary": {m: summarize([s.get(m) for s in complete(a.get("slices") or [])]) for m in METRICS}}
            for ft, a in latest.items() if complete(a.get("slices") or [])}


# ---- orthography ---------------------------------------------------------------------------

def orthography(model, rec: dict, home: dict) -> dict | None:
    if rec["signum"] not in model.index:
        return None
    rk = model.rank_carvers(rec["signum"], 5)
    ev = model.evaluate() or {}
    per = ev.get("per_carver", {})
    length = _length_factor(rk["n_words"])
    items = []
    for r in rk["ranking"]:
        precision = smoothed_precision(per.get(r["carver"]))
        in_area = province(rec) in home.get(r["carver"], {})
        items.append({**r, "precision": precision, "predicted": (per.get(r["carver"]) or {}).get("predicted", 0),
                      "in_area": in_area,
                      "reliability": round(precision * (1.0 if in_area else 0.5) * length, 3)})
    return {
        "ranking": items, "n_words": rk["n_words"], "usable": rk["n_words"] >= MIN_WORDS,
        "evaluation": {k: ev.get(k) for k in ("top1_accuracy", "top3_accuracy", "chance_top1", "n_carvers",
                                              "n_inscriptions")} | {"signed_top1": (ev.get("signed_only") or {}).get("top1_accuracy")},
    }


def orthography_from_reading(model, reading: dict, signum: str, home: dict, rec: dict | None) -> dict | None:
    """Ortografin för appens egen läsning – när Rundata saknar en användbar text (t.ex. nyfynd).
    En AI-läsning är osäkrare än en publicerad, så tillförlitligheten sänks med 30 %."""
    translit = (reading or {}).get("transliteration") or ""
    if not translit.strip():
        return None
    rk = model.rank_text(translit, reading.get("normalization") or "", 5,
                         exclude_signum=rec["signum"] if rec else None)
    ev = model.evaluate() or {}
    per = ev.get("per_carver", {})
    length = _length_factor(rk["n_words"])
    prov = (signum or "").split(" ")[0]
    items = []
    for r in rk["ranking"]:
        precision = smoothed_precision(per.get(r["carver"]))
        in_area = prov in home.get(r["carver"], {})
        items.append({**r, "precision": precision, "predicted": (per.get(r["carver"]) or {}).get("predicted", 0),
                      "in_area": in_area, "reliability": round(0.7 * precision * (1.0 if in_area else 0.5) * length, 3)})
    return {
        "ranking": items, "n_words": rk["n_words"], "usable": rk["n_words"] >= MIN_WORDS, "source": "Ortografi (vår läsning)",
        "evaluation": {k: ev.get(k) for k in ("top1_accuracy", "top3_accuracy", "chance_top1", "n_carvers",
                                              "n_inscriptions")} | {"signed_top1": (ev.get("signed_only") or {}).get("top1_accuracy")},
    }


# ---- groove technique ----------------------------------------------------------------------

def _reference(corpus: list[dict], lookup, signum: str, feature_type: str):
    own = lookup(signum)
    ref, stones = [], {}
    for e in corpus:
        rec = lookup(e.get("signum") or "")
        if not rec or (own and rec["signum"] == own["signum"]):
            continue
        if (e.get("feature_type") or "unknown") != feature_type:
            continue
        cs = certain_carvers(rec)
        m = e.get("means") or {}
        if len(cs) != 1 or any(m.get(k) is None for k in METRICS):
            continue
        ref.append({"group": cs[0], "label": rec["signum"], "values": [float(m[k]) for k in METRICS]})
        stones.setdefault(cs[0], []).append({"signum": rec["signum"], "slices": complete(e.get("slices") or [])})
    return ref, stones


def groove(query_slices: list[dict], feature_type: str, corpus: list[dict], lookup, signum: str) -> dict:
    q = means(query_slices)
    if not q:
        return {"ranking": [], "note": "Stenen har inga fullständiga tvärsnitt av vald spårtyp."}
    ref, stones = _reference(corpus, lookup, signum, feature_type)
    res = attribute(ref, q)
    ev = res.get("evaluation")
    reliability = 0.0
    if ev:
        reliability = max(0.0, (ev["top1_accuracy"] - ev["chance_top1"]) / (1 - ev["chance_top1"]))
    return {"ranking": res.get("ranking", [])[:5], "evaluation": ev, "reference_size": len(ref),
            "reliability": round(reliability, 3), "note": res.get("note"), "_stones": stones}


def stone_tests(query_slices: list[dict], stones: list[dict], max_stones: int = 5, n_perm: int = 1000) -> dict:
    """Permutationstest av alla mått samtidigt: stenen mot var och en av kandidatens uppmätta stenar."""
    A = np.array([[s[m] for m in METRICS] for s in complete(query_slices)])
    out = []
    for st in stones[:max_stones]:
        if len(st["slices"]) < 2 or len(A) < 2:
            continue
        B = np.array([[s[m] for m in METRICS] for s in st["slices"]])
        p = multivariate_permutation_test(A, B, n_perm=n_perm)["p_value"]
        out.append({"signum": st["signum"], "n": len(B), "p_value": p, "compatible": p is not None and p >= 0.05})
    k = sum(t["compatible"] for t in out)
    text = (f"Förenlig (p ≥ 0,05) med {k} av {len(out)} uppmätta stenar" if out else
            "Inga av ristarens stenar har tillräckligt många uppmätta tvärsnitt för ett test")
    return {"tests": out, "compatible": k, "n": len(out), "text": text}


# ---- plausibility checks -------------------------------------------------------------------

def _km(a, b) -> float:
    (la1, lo1), (la2, lo2) = a, b
    p1, p2 = math.radians(la1), math.radians(la2)
    dp, dl = p2 - p1, math.radians(lo2 - lo1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def geography(rec: dict, carver: str, inscriptions: list[dict], home: dict) -> dict:
    provinces = home.get(carver, Counter())
    own = (rec["lat"], rec["lon"]) if rec.get("lat") is not None else None
    others = [(r["lat"], r["lon"]) for r in inscriptions
              if carver in certain_carvers(r) and r.get("lat") is not None and r["signum"] != rec["signum"]]
    nearest = min((_km(own, o) for o in others), default=None) if own else None
    in_area = province(rec) in provinces
    if own is None:
        text = "Avståndet kan inte beräknas (stenen saknar koordinater)."
    elif not others:
        text = f"{carver} har inga andra säkra stenar med koordinater att jämföra med."
    else:
        text = (f"En signerad eller attribuerad sten av {carver} står på samma plats (under 1 km)." if nearest < 1 else
                f"Närmaste signerade eller attribuerade sten av {carver} ligger {round(nearest)} km bort.")
    if provinces:
        text += f" Ristarens kända landskap: {', '.join(f'{p} ({n})' for p, n in provinces.most_common(4))}."
    plausible = in_area and (nearest is None or nearest <= 60)
    return {"in_area": in_area, "nearest_km": round(nearest, 1) if nearest is not None else None,
            "provinces": dict(provinces.most_common(6)), "plausible": plausible, "text": text}


STYLE_CORE_SHARE = 0.1   # a style group on at least this share of the carver's stones is part of the core
STYLE_STRONG_GAP = 25    # years between the stone's style and the core that make the suggestion chronologically hard


def carver_styles(rec: dict | None, carver: str, inscriptions: list[dict]) -> dict:
    """Stenens stilgrupp mot stilgrupperna på ristarens säkra stenar. En stilgrupp som bara finns på enstaka stenar
    räknas inte som ristarens; avståndet i år till kärnan (Gräslunds kronologi) avgör om stilen talar emot."""
    styles = Counter(r["style"] for r in inscriptions
                     if carver in certain_carvers(r) and r["style"] and not r["style_uncertain"] and r["style"] != "?")
    total = sum(styles.values())
    years = [(BY_CODE[s]["from"], BY_CODE[s]["to"]) for s in styles if s in BY_CODE and BY_CODE[s]["from"]]
    span = (min(y[0] for y in years), max(y[1] for y in years)) if years else None
    core = [s for s, n in styles.items() if n / total >= STYLE_CORE_SHARE] if total else []
    core_years = [(BY_CODE[s]["from"], BY_CODE[s]["to"]) for s in core if s in BY_CODE and BY_CODE[s]["from"]]
    stone_style = (rec or {}).get("style")
    fits, gap = None, None
    if stone_style and not (rec or {}).get("style_uncertain") and styles:
        st = BY_CODE.get(stone_style)
        if st and st["from"] and core_years:
            lo, hi = min(y[0] for y in core_years), max(y[1] for y in core_years)
            gap = max(0, lo - st["to"], st["from"] - hi)
        # In the core: fits. Outside the core but within its time frame: possible, but rare for the carver, so it does
        # not decide either way. Outside the time frame: speaks against
        fits = (True if stone_style in core else
                (None if gap == 0 else False) if gap is not None else stone_style in styles)
    text = ("Stilgrupper på ristarens stenar (utan frågetecken i Rundata): "
            + ", ".join(f"{s} ({n})" for s, n in styles.most_common()) + "."
            if styles else "Ristarens stenar saknar säker stilgrupp i Rundata.")
    if core_years:
        c_lo, c_hi = min(y[0] for y in core_years), max(y[1] for y in core_years)
        rare = [s for s in styles if s not in core]
        text += (f" Kärnan (stilgrupper på minst en tiondel av stenarna: "
                 f"{', '.join(sorted(core, key=lambda c: BY_CODE.get(c, {}).get('from') or 0))}) motsvarar ungefär "
                 f"{c_lo}–{c_hi} enligt Gräslunds kronologi" + (f"; {', '.join(rare)} finns bara på enstaka stenar." if rare else "."))
    if fits is None and gap == 0 and stone_style not in core:
        n_same = styles.get(stone_style, 0)
        text += (f" Stenens stilgrupp {stone_style} ligger inom kärnans tidsram men finns bara på {n_same} av {total} av "
                 "ristarens stenar; den är möjlig men ovanlig för ristaren och avgör inte frågan.")
    if fits is False:
        n_same = styles.get(stone_style, 0)
        text += (f" Stenens stilgrupp {stone_style} finns {'bara på ' + str(n_same) + ' av ' + str(total) if n_same else 'inte'}"
                 f"{' av ristarens stenar' if n_same else ' bland dem'}")
        if gap:
            text += (f"; ristarens huvudsakliga stilgrupper ({', '.join(sorted(core, key=lambda c: BY_CODE.get(c, {}).get('from') or 0))}) "
                     f"ligger omkring {gap} år {'senare' if (BY_CODE[stone_style]['to'] or 0) < min(y[0] for y in core_years) else 'tidigare'}")
            if gap >= STYLE_STRONG_GAP:
                text += ", vilket gör förslaget kronologiskt problematiskt om stilbestämningen stämmer"
        text += "."
    return {"styles": dict(styles), "span": list(span) if span else None, "core": core, "gap_years": gap,
            "strong": bool(gap is not None and gap >= STYLE_STRONG_GAP), "fits": fits, "text": text}


_family_cache: dict[tuple, tuple[dict, int]] = {}


def _province_families(prov: str, inscriptions: list[dict]) -> tuple[dict, int]:
    """Andelen runstenar i landskapet (med uppgift om material) per bergartsfamilj."""
    key = (prov, len(inscriptions))
    if key not in _family_cache:
        from src.research_gaps import is_runestone
        fams, n = Counter(), 0
        for r in inscriptions:
            if is_runestone(r) and province(r) == prov and r.get("material"):
                n += 1
                for f in geology.families(r["material"]):
                    fams[f] += 1
        _family_cache[key] = ({f: c / n for f, c in fams.items()} if n else {}, n)
    return _family_cache[key]


def material_check(rec: dict, carver: str, inscriptions: list[dict]) -> dict | None:
    """Stenens bergart mot bergarterna på ristarens säkra stenar (Rundata). En bergart som är lika vanlig på andra
    runstenar i landskapet som hos ristaren skiljer inte ristare åt och räknas varken för eller emot."""
    material = (rec or {}).get("material") or ""
    prof = geology.carver_materials(carver, inscriptions, certain_carvers)
    if not material or prof["n"] < 3:
        return None
    fams = geology.families(material)
    used = {f for f, share in prof["families"].items() if share >= 0.1}
    fits = bool(fams & used) if fams else None
    listing = ", ".join(f"{m} ({n})" for m, n in prof["materials"][:4])
    text = f"Stenen: {material}. Säkra stenar av {carver} med uppgift ({prof['n']}): {listing}."
    if fits is False:
        text += " Bergarten förekommer sällan eller aldrig hos ristaren."
    elif fits:
        base, n_base = _province_families(province(rec), inscriptions)
        fam = max(fams & used, key=lambda f: prof["families"].get(f, 0))
        share_c, share_p = prof["families"].get(fam, 0), base.get(fam, 0)
        label = geology.FAMILY_LABEL.get(fam, fam)
        if n_base >= 20 and share_p and share_c / share_p < 1.5:
            fits = None
            text += (f" {label.capitalize()} är inte tydligt vanligare hos ristaren ({round(share_c * 100)} %) än på "
                     f"runstenarna i landskapet i stort ({round(share_p * 100)} %; kvot under 1,5), så bergarten skiljer "
                     "inte ristare åt.")
        else:
            text += (f" {label.capitalize()} är vanligare hos ristaren ({round(share_c * 100)} %) än på runstenarna i "
                     f"landskapet i stort ({round(share_p * 100)} %).")
    return {"material": material, "fits": fits, "carver": prof, "text": text}


_region_cache: dict[tuple, list[tuple[str, frozenset, dict]]] = {}


def _region_stones(prov: str, inscriptions: list[dict], names) -> list[tuple[str, frozenset, dict]]:
    """(signum, säkra ristare, språkdrag) för runstenarna i ett landskap; Rundata ändras inte medan servern kör."""
    key = (prov, len(inscriptions), id(names))
    if key not in _region_cache:
        from src.research_gaps import is_runestone
        _region_cache[key] = [(r["signum"], frozenset(certain_carvers(r)), language_traits(r, names))
                              for r in inscriptions if is_runestone(r) and province(r) == prov]
    return _region_cache[key]


def language_check(rec: dict, carver: str, inscriptions: list[dict], names, selected: bool = False) -> dict | None:
    """Språkdragen mot ristarens profil, vägda mot övriga stenar i landskapet och prövade mot dem: passar stenen
    ristaren bättre än en slumpvis sten i landskapet som inte är av ristaren? selected: ristaren har valts ut av en
    metod som själv bygger på stavningen (ortografin, modellen), så språkdragen är inget oberoende stöd – de kan då
    tala emot men inte för."""
    stone = language_traits(rec, names)
    if not stone:
        return None
    profile = carver_profile(carver, inscriptions, certain_carvers, names, exclude=rec["signum"])
    if profile["n_inscriptions"] < 3:
        return None
    prov = province(rec)
    others = [t for sg, cs, t in _region_stones(prov, inscriptions, names) if sg != rec["signum"] and carver not in cs and t]
    baseline: dict[str, Counter] = {}
    for t in others:
        for k, v in t.items():
            baseline.setdefault(k, Counter())[v] += 1
    c = compare_language(stone, profile, baseline=baseline if len(others) >= 20 else None, others=others, region=prov)
    if c.get("lr_total") is not None:
        p = c.get("p_region")
        favourable = p is not None and p < 0.05 and c["lr_total"] > 1
        if p is not None:
            c["significant"] = favourable
            c["text"] += " Skillnaden mot landskapet är " + ("statistiskt signifikant." if favourable
                                                           else "inte statistiskt signifikant.")
        if selected and favourable:
            c["text"] += (" Ristaren är utvald av en metod som själv bygger på stavningen, så språkdragen räknas inte "
                          "som ett oberoende stöd.")
        # Supports the carver when the stone fits better than nearly all stones in the province (and the carver was not
        # chosen by spelling); speaks against it when the traits are clearly more common elsewhere
        c["fits"] = (True if favourable and not selected else (False if c["lr_total"] <= 1 / 3 else None))
    else:
        c["fits"] = None if c["comparable"] < 2 else c["agree"] / c["comparable"] >= 0.5
    return c


def site_geology(rec: dict | None) -> dict | None:
    if not rec or rec.get("lat") is None or not geology.enabled():
        return None
    try:
        return geology.bedrock(rec["lat"], rec["lon"], rec.get("material") or "")
    except Exception:
        return None


def literature_verdict(rec: dict | None, carver: str) -> dict:
    cs = (rec or {}).get("carvers") or []
    names = {c["name"]: c for c in cs}
    sa = [c for c in cs if c["kind"] in ("S", "A")]
    if carver in names:
        c = names[carver]
        kind = {"S": "signerad", "A": "attribuerad", "P": "parsten", "L": "liknar"}.get(c["kind"], c["kind"])
        verdict = "stämmer" if c["kind"] in ("S", "A") else "stämmer delvis"
        return {"verdict": verdict, "text": f"Rundata anger {carver} ({kind}{', osäker' if c['uncertain'] else ''})."}
    if sa:
        return {"verdict": "motsäger",
                "text": "Rundata anger " + ", ".join(f"{c['name']} ({c['kind']})" for c in sa) + "."}
    if rec is None:
        return {"verdict": "okänt", "text": "Stenen finns inte i Rundata."}
    return {"verdict": "nytt", "text": "Rundata anger ingen ristare."}


# ---- candidates ----------------------------------------------------------------------------

def build_candidates(ev: dict) -> list[dict]:
    cands: dict[str, dict] = {}

    def add(name, source, description, weight, rank=None):
        c = cands.setdefault(name, {"name": name, "evidence": [], "score": 0.0, "first_in": []})
        c["evidence"].append({"source": source, "description": description, "weight": round(weight, 2)})
        c["score"] += weight
        if rank == 1:
            c["first_in"].append(source)

    for c in ((ev.get("rundata") or {}).get("carvers") or []):
        if c["kind"] == "S":
            add(c["name"], "Rundata", "Inskriften är signerad av ristaren" + (" (osäker läsning)." if c["uncertain"] else "."),
                2 if c["uncertain"] else 4)
        elif c["kind"] == "A":
            add(c["name"], "Rundata", "Attribuerad till ristaren i litteraturen" + (" (osäker)." if c["uncertain"] else "."),
                1 if c["uncertain"] else 2)
        elif c["kind"] in ("P", "L"):
            add(c["name"], "Rundata", "Parsten till eller liknar ristarens signerade inskrifter.", 1)

    o = ev.get("orthography") or {}
    if o.get("usable"):
        for rank, r in enumerate(o["ranking"][:3], start=1):
            w = (2 if rank == 1 else 1) * r["reliability"]
            area = "" if r["in_area"] else ", utanför ristarens kända landskap"
            add(r["carver"], o.get("source", "Ortografi"),
                f"Plats {rank} (likhet {_d(r['similarity'])}"
                + (f", {OrthographyModel.p_text(r.get('significance'))}" if r.get("significance") else "")
                + f"; modellen har rätt i omkring {round(r['precision'] * 100)} % "
                f"när den föreslår ristaren, {r['predicted']} förslag; {o['n_words']} ord{area}).", w, rank)

    g = ev.get("groove") or {}
    if g.get("ranking") and g.get("reliability", 0) > 0:
        acc = (g.get("evaluation") or {}).get("top1_accuracy")
        for rank, r in enumerate(g["ranking"][:3], start=1):
            w = (2 if rank == 1 else 1) * g["reliability"]
            add(r["group"], "Huggteknik",
                f"Plats {rank} mot mätkorpusen (Mahalanobisavstånd {_d(r['distance'])}, {r['n']} stenar; "
                f"korsvaliderad träffsäkerhet {round((acc or 0) * 100)} %).", w, rank)

    out = []
    for c in cands.values():
        sources = {e["source"] for e in c["evidence"]}
        if c["score"] >= 4 or (len(sources) >= 3 and c["score"] >= 3):
            strength = "stark"
        elif c["score"] >= 2.5 or (c["score"] >= 1.5 and len(sources) >= 2):
            strength = "måttlig"
        else:
            strength = "svag"
        out.append({**c, "score": round(c["score"], 2), "strength": strength, "sources": sorted(sources)})
    out.sort(key=lambda c: (-c["score"], -len(c["sources"]), c["name"]))
    return out[:6]


def conflicts(ev: dict, candidates: list[dict]) -> list[str]:
    """Motsägelser mellan källorna, redovisade utan AI."""
    out = []
    rec = ev.get("_rec")
    rd_sa = [c for c in ((ev.get("rundata") or {}).get("carvers") or []) if c["kind"] in ("S", "A") and not c["uncertain"]]
    o = ev.get("orthography") or {}
    g = ev.get("groove") or {}
    o_top = o["ranking"][0]["carver"] if o.get("usable") and o.get("ranking") else None
    o_top3 = [r["carver"] for r in (o.get("ranking") or [])[:3]] if o.get("usable") else []
    g_top = g["ranking"][0]["group"] if g.get("ranking") and g.get("reliability", 0) > 0 else None
    for c in rd_sa:
        kind = "signerad av" if c["kind"] == "S" else "attribuerad till"
        if o_top and c["name"] not in o_top3:
            out.append(f"Rundata: {kind} {c['name']}, men ortografin rankar {o_top} först och {c['name']} inte bland de tre första."
                       + (" Eftersom stenen är signerad talar det snarare mot den ortografiska metoden." if c["kind"] == "S" else ""))
        if g_top and g_top != c["name"] and c["name"] in {r["group"] for r in g["ranking"]}:
            out.append(f"Rundata: {kind} {c['name']}, men huggtekniken liknar {g_top} mer.")
    if o_top and g_top and o_top != g_top:
        out.append(f"Ortografin pekar på {o_top} men huggtekniken på {g_top}.")
    for cand in candidates[:3]:
        geo = cand.get("geography") or {}
        if geo and not geo.get("plausible") and cand["name"] not in [c["name"] for c in rd_sa]:
            out.append(f"{cand['name']}: geografiskt tveksamt – {geo['text']}")
        st = cand.get("styles") or {}
        if st.get("fits") is False:
            out.append(f"{cand['name']}: stenens stilgrupp {rec['style']} förekommer inte på ristarens säkra stenar.")
        cat = cand.get("category") or {}
        if cat.get("fits") is False:
            out.append(f"{cand['name']}: {cat['text'].split('. ')[-1]}")
        lang = cand.get("language") or {}
        if lang.get("fits") is False:
            out.append(f"{cand['name']}: bara {lang['agree']} av {lang['comparable']} språkdrag stämmer med ristarens inskrifter.")
        mat = cand.get("material") or {}
        if mat.get("fits") is False:
            out.append(f"{cand['name']}: stenens bergart ({mat['material']}) förekommer sällan hos ristaren.")
        tests = cand.get("stone_tests") or {}
        if tests.get("n") and tests["compatible"] == 0:
            out.append(f"{cand['name']}: huggtekniken skiljer sig signifikant från alla {tests['n']} uppmätta stenar av ristaren.")
    sc = ev.get("style_check")
    if sc and sc.get("rundata_style") and not sc["agrees"]:
        out.append(f"AI-bedömd stilgrupp {sc['ai_style']} (bild, okalibrerad) skiljer sig från Rundatas {sc['rundata_style']}.")
    return out


def missing_notes(ev: dict, corpus_note: str | None) -> list[str]:
    notes = []
    if not ev.get("rundata"):
        notes.append("Signumet finns inte i Rundata: ingen litteraturuppgift eller geografi"
                     + ("." if ev.get("orthography") else
                        "; ortografin kräver en egen läsning från Språk & Fonetik."))
    o = ev.get("orthography")
    if ev.get("rundata") and not o:
        notes.append("Ortografi: inskriften ingår inte i den ortografiska modellen (för få läsbara ord eller fel period).")
    elif o and o.get("source") and o["usable"]:
        notes.append("Ortografi: Rundata saknar användbar text, så appens egen AI-läsning används (vikten sänkt 30 %).")
    elif o and not o["usable"]:
        notes.append(f"Ortografi: bara {o['n_words']} läsbara ord – för kort text för en pålitlig jämförelse; vägs inte in.")
    rv = ev.get("reading_validation")
    if rv and not rv["reliable"]:
        notes.append(f"Egen läsning: {rv['text']} Den används inte som belägg.")
    g = ev.get("groove") or {}
    if corpus_note:
        notes.append(f"Huggteknik: {corpus_note}")
    elif not ev.get("measurements"):
        notes.append("Huggteknik: projektet har ingen sparad 3D-analys.")
    elif g.get("note"):
        notes.append(f"Huggteknik: {g['note']}")
    elif g.get("ranking") and not g.get("reliability"):
        notes.append("Huggteknik: jämförelsen mot korpusen är inte bättre än slumpen ännu och vägs inte in.")
    return notes


def outcome(rec: dict | None, candidates: list[dict], conflict_list: list[str] | None = None) -> dict:
    """Vad syntesen säger jämfört med litteraturen. Bara källor där kandidaten kommer först räknas som stöd."""
    if not candidates:
        return {"verdict": "inget", "text": "Underlaget räcker inte för att peka ut någon ristare."}
    top = candidates[0]
    lv = top["literature"]
    support = [x.lower() for x in top.get("first_in", []) if x != "Rundata"]
    other_first = {}
    for c in candidates[1:]:
        for src in c.get("first_in", []):
            other_first[src] = c["name"]
    if lv["verdict"] == "stämmer":
        if support:
            text = f"Beläggen stöder litteraturens {top['name']}, med oberoende stöd från {' och '.join(support)}."
        elif other_first:
            text = (f"Litteraturen anger {top['name']}, men de oberoende metoderna pekar på andra ristare ("
                    + ", ".join(f"{src.lower()}: {name}" for src, name in other_first.items()) + ").")
        else:
            text = f"Litteraturen anger {top['name']}; inga oberoende belägg talar för eller emot."
    elif lv["verdict"] == "nytt":
        text = (f"Rundata anger ingen ristare. Beläggen pekar på {top['name']} ({STRENGTH_PLURAL[top['strength']]} belägg) – "
                "en hypotes att pröva, inte en attribuering.")
    elif lv["verdict"] == "motsäger":
        text = (f"Beläggen pekar på {top['name']} medan {lv['text'][0].lower() + lv['text'][1:]} "
                "Värt en omprövning om beläggen är starka.")
    else:
        text = f"Starkast belägg för {top['name']} ({STRENGTH_PLURAL[top['strength']]} belägg)."
    if conflict_list:
        text += f" {len(conflict_list)} motsägelse{'r' if len(conflict_list) > 1 else ''} mellan källorna redovisas."
    return {"verdict": lv["verdict"], "text": text, "support": support}
