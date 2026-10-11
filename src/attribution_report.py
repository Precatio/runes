"""Beslutsunderlag om en attribuering: alla argument för och emot en ristare till en sten, som ett dokument att
skicka till dem som förvaltar runtextdatabasen (se METHODS.md, 14f).

Dokumentet ska kunna läsas av en runolog som inte känner appen och ligga till grund för ett beslut. Det börjar med
en ärlig slutsats och rekommendation (förslag, granskning eller inget skäl att ompröva; en signerad sten får aldrig
ett förslag om en annan ristare), förklarar varje metod på vanligt språk – vad den jämför, vilka data den bygger på,
vad talen betyder och hur ofta den har rätt – och ställer den föreslagna ristaren mot Rundatas. Allt är framräknat;
ingen AI-text.
"""
from __future__ import annotations

import datetime
from collections import Counter

from src import limitations
from src.academic import bullets, h, p, table
from src.interpretation import _join, interpret
from src.research_gaps import certain_carvers, is_runestone, province
from src.stone_overview import _checks, stone
from src.synthesis import carver_styles, language_check
from src.stone_report import PERIODS, inscription, sri_reference
from src.styles import BY_CODE
from src.about import APP_URL, REPO_URL

CHECK_LABELS = {"område": "Område", "stil": "Stilgrupp", "språkdrag": "Språkdrag", "bergart": "Bergart"}

# Rundata's carver names that are groups or debated identities rather than one person
CARVER_NOTES = {
    "Traen": "\u201dTraen\u201d är enligt Gustavson & Snædal Brink (1981) och Bianchi (2010) en felläsning, och stenarna "
             "bildar en grupp snarare än en ristares verk; förslaget gäller alltså att stenen hör till den gruppen.",
}


def _n(v, d=2) -> str:
    return "–" if v is None else f"{v:.{d}f}".replace(".", ",")


def _pv(v) -> str:
    return "–" if v is None else ("< 0,001" if v < 0.001 else _n(v, 3))


def carver_summary(name: str, inscriptions: list[dict]) -> dict:
    stones = [r for r in inscriptions if name in certain_carvers(r)]
    signed = [r["signum"] for r in stones if any(c["name"] == name and c["kind"] == "S" and not c["uncertain"] for c in r["carvers"])]
    # The same style count and core as the style check (synthesis.carver_styles), so that section 2 and 4.4 agree
    cst = carver_styles(None, name, inscriptions)
    core_years = [(BY_CODE[s]["from"], BY_CODE[s]["to"]) for s in cst["core"] if s in BY_CODE and BY_CODE[s].get("from")]
    return {"n": len(stones), "signed": signed, "provinces": Counter(province(r) for r in stones).most_common(4),
            "styles": Counter(cst["styles"]).most_common(5),
            "core": sorted(cst["core"], key=lambda c: BY_CODE.get(c, {}).get("from") or 0),
            "span": (min(y[0] for y in core_years), max(y[1] for y in core_years)) if core_years else None}


# ---- the model's probabilities, made interpretable ---------------------------------------------------------------

def _calibration(ctx: dict) -> tuple[list[tuple[float, bool]], list[float]]:
    """Ur korsvalideringen (stenar med en säker ristare, som modellen inte såg): (sannolikhet, rätt ristare?) för varje
    ristare och sten, och den högsta sannolikhet som en felaktig ristare fick per sten."""
    by_signum = {r["signum"]: r for r in ctx["inscriptions"]}
    pairs, wrong = [], []
    for sg, probs in (ctx.get("oof") or {}).items():
        r = by_signum.get(sg)
        truth = certain_carvers(r) if r else []
        if len(truth) != 1 or truth[0] not in probs:
            continue
        pairs += [(v, c == truth[0]) for c, v in probs.items()]
        wrong.append(max((v for c, v in probs.items() if c != truth[0]), default=0.0))
    return pairs, wrong


def _hit_rate(pairs, prob: float, width: float = 0.05) -> tuple[int, int]:
    sel = [ok for v, ok in pairs if abs(v - prob) <= width]
    return sum(sel), len(sel)


def _pct(x: float | None) -> str:
    return "–" if x is None else f"{round(100 * x)} %"


def _references(rec: dict, carver: str, inscriptions: list[dict]) -> list[dict]:
    """Ristarens stenar (utan frågetecken i Rundata) efter avstånd: signum, km, signerad, ensam ristare, försvunnen."""
    from src.synthesis import _km
    if rec.get("lat") is None:
        return []
    out = []
    for r in inscriptions:
        if r["signum"] != rec["signum"] and carver in certain_carvers(r) and r.get("lat") is not None:
            others = sorted({c["name"] for c in r["carvers"] if c["name"] != carver})
            out.append({"signum": r["signum"], "km": _km((rec["lat"], rec["lon"]), (r["lat"], r["lon"])),
                        "signed": any(c["name"] == carver and c["kind"] == "S" and not c["uncertain"] for c in r["carvers"]),
                        "others": others, "lost": bool((r.get("flags") or {}).get("lost"))})
    return sorted(out, key=lambda x: x["km"])


def _nearest(rec: dict, carver: str, inscriptions: list[dict], k: int = 5) -> tuple[list[dict], list[dict]]:
    """Jämförelsestenar: de närmaste stenarna där ristaren är ensam ristare och som finns kvar, och de närmare stenar
    som lämnats bort (flera ristare eller försvunna), så att läsaren ser varför."""
    refs = _references(rec, carver, inscriptions)
    usable = [x for x in refs if not x["others"] and not x["lost"]]
    chosen = usable[:k]
    if chosen and not any(x["signed"] for x in chosen):  # at least one signed stone, the firmest comparison
        chosen += [x for x in usable[k:] if x["signed"]][:1]
    limit = chosen[-1]["km"] if chosen else float("inf")
    skipped = [x for x in refs if (x["others"] or x["lost"]) and x["km"] <= limit][:4]
    return chosen, skipped


def _ref_text(x: dict) -> str:
    return f"{x['signum']} ({round(x['km'])} km{', signerad' if x['signed'] else ''})"


def _skip_text(x: dict) -> str:
    why = ([f"tillsammans med {' och '.join(x['others'])}"] if x["others"] else []) + (["försvunnen"] if x["lost"] else [])
    return f"{x['signum']} ({round(x['km'])} km; {', '.join(why)})"


def _verdict(reading: dict, signed_by_other: bool, reattribution: bool, carver: str = "ristaren") -> tuple[str, str, str]:
    """(dokumenttyp, slutsats, rekommendation) efter tolkningens nivå."""
    level = reading["level"]
    if signed_by_other:
        return ("Underlag för granskning av attribuering",
                "Stenen är signerad. En signatur är det starkaste belägg som finns för vem som ristade en sten, och "
                "statistiska jämförelser kan inte väga upp den.",
                "Vi rekommenderar ingen ändring av attribueringen. Att metoderna pekar på en annan ristare visar en "
                "svaghet i metoderna eller ett möjligt samarbete, inte att signaturen är fel.")
    if level == "starkt":
        return ("Förslag till omprövning av attribuering" if reattribution else "Attribueringsförslag",
                f"Underlaget är starkt: både den statistiska modellen och ortografin pekar på {carver}, stavningslikheten är "
                "statistiskt signifikant och inget av de andra beläggen talar emot. Något belägg utanför modellen och "
                "ortografin (huggteknik, runformer, ornamentik) finns ännu inte.",
                (f"Vi föreslår att attribueringen omprövas till {carver}" if reattribution else
                 f"Vi föreslår att stenen attribueras till {carver}")
                + ", efter en runologisk granskning av ornamentik och runformer (avsnitt 7).")
    if level == "måttligt":
        return ("Underlag för granskning av attribuering",
                "Underlaget är måttligt: det finns belägg för ristaren, men inte tillräckligt många oberoende belägg för "
                "ett förslag.",
                ("Vi föreslår ingen ändring i dag" if reattribution else "Vi föreslår ingen attribuering i dag")
                + ", men att stenen granskas runologiskt med de kontroller som anges i avsnitt 7. Förslaget är en prövbar "
                "hypotes.")
    if level == "redan känt":
        return ("Underlag för granskning av attribuering",
                "Förslaget finns redan i nyare källor (Runor 2020 eller Wikidata).",
                "Ingen ny åtgärd behövs utöver att de nyare källorna och databasen stäms av mot varandra.")
    return ("Prövning av attribuering",
            "Underlaget är svagt: beläggen räcker inte för att knyta stenen till ristaren.",
            "Vi rekommenderar ingen ändring av attribueringen." if reattribution else
            "Vi rekommenderar ingen attribuering på detta underlag.")


GLOSSARY = [
    "Sannolikhet (statistiska modellen): modellens skattning av hur troligt det är att stenen är huggen av en viss "
    "ristare, under förutsättning att den är huggen av någon av modellens ristare. Sannolikheterna summerar till 1.",
    "Korsvalidering: modellen prövas på stenar som den inte har sett, en i taget eller i grupper, så att träffsäkerheten "
    "inte blir för optimistisk.",
    "Kalibrering: hur ofta en viss sannolikhet stämmer. En väl kalibrerad modell har rätt i ungefär 60 % av fallen när "
    "den anger 0,6.",
    "Likhet (ortografi): hur lik stenens stavning, skiljetecken och bindrunor är en ristares övriga inskrifter, 0–1.",
    "p-värde: hur ofta en minst lika stor likhet skulle uppstå om stenen inte hade något särskilt samband med ristaren. "
    "Justerat p tar hänsyn till att den mest lika av många ristare valts ut (max-statistik); under 0,05 kallas "
    "statistiskt signifikant. Ett lågt p-värde är inte sannolikheten att ristaren är rätt.",
    "Ristare utan frågetecken: en ristare som Rundata anger som signerad eller attribuerad utan frågetecken. Det är "
    "databasens bedömning, i Mälardalen ofta Axelsons (1993), inte ett facit; bara signaturer är direkta belägg.",
    "Typikalitet: hur stor del av ristarens egna inskrifter som liknar ristarens profil mindre än stenen gör. Låg "
    "typikalitet betyder att stenen är ovanlig för ristaren.",
    "Sannolikhetskvot (språkdrag): hur mycket vanligare stenens form är hos ristaren än på andra stenar i landskapet. "
    "Över 1 talar för ristaren, under 1 emot.",
    "Stilgrupp: Gräslunds (1998) indelning av runstenarnas ornamentik (RAK, Fp, Pr1–Pr5) med ungefärliga dateringar.",
]


def _favours_current(rec: dict, carver: str, current: str, probs: dict, inscriptions: list[dict], names,
                     checks: dict) -> list[str]:
    """Belägg för att Rundatas ristare passar stenen bättre än den prövade: modellen föredrar Rundatas ristare,
    språkdragen stöder den signifikant men inte den prövade, den har stenar mycket närmare, eller stenens stilgrupp
    hör till dess kärna men inte till den prövades. Ett drag som redan talar emot den prövade räknas inte igen."""
    out = []
    p_car, p_cur = probs.get(carver), probs.get(current)
    if p_cur is not None and p_cur > (p_car or 0) and max(probs, key=probs.get) == current:
        out.append(f"modellen föredrar {current} ({_n(p_cur)} mot {_n(p_car or 0)})")
    if checks["språkdrag"][0] is not False:
        l_cur = language_check(rec, current, inscriptions, names) or {}
        l_car = language_check(rec, carver, inscriptions, names, selected=True) or {}
        if l_cur.get("significant") and not l_car.get("significant"):
            out.append(f"språkdragen passar {current} signifikant bättre än landskapets övriga stenar (p {_pv(l_cur.get('p_region'))}), "
                       f"men inte {carver}" + (f" (p {_pv(l_car.get('p_region'))})" if l_car.get("p_region") is not None else ""))
    refs_car, refs_cur = _references(rec, carver, inscriptions), _references(rec, current, inscriptions)
    if checks["område"][0] is not False and refs_car and refs_cur:
        d_car, d_cur = refs_car[0]["km"], refs_cur[0]["km"]  # as in section 4.3: every stone of the carver counts
        if d_car >= 10 and d_car >= 3 * max(d_cur, 1):
            out.append(f"närmaste sten av {current} står {round(d_cur)} km bort, av {carver} {round(d_car)} km")
    st = rec.get("style")
    if st and not rec.get("style_uncertain") and checks["stil"][0] is not False:
        s_car, s_cur = carver_styles(rec, carver, inscriptions), carver_styles(rec, current, inscriptions)
        if st in s_cur["core"] and st not in s_car["core"]:
            n_car = sum(s_car["styles"].values())
            out.append(f"stilgruppen {st} hör till kärnan hos {current} ({s_cur['styles'].get(st, 0)} av "
                       f"{sum(s_cur['styles'].values())} stenar) men är ovanlig hos {carver} ({s_car['styles'].get(st, 0)} av {n_car})")
    return out


def build(rec: dict, carver: str, ctx: dict, crosscheck: dict | None, dims: dict | None, author: str,
          institution: str, versions: dict, att: dict | None = None, email: str = "") -> list[dict]:
    """Rapportens block (src/academic.py-formatet). att: R-modulens attribution.json (modellens uppgifter); email:
    författarens kontaktadress (ur inställningarna, aldrig inskriven i koden)."""
    signum = rec["signum"]
    inscriptions = ctx["inscriptions"]
    att = att or {}
    profile = stone(rec, ctx, detail=True)
    listed = profile.get("carvers") or []
    reattribution = bool(listed) and carver not in listed
    current = listed[0] if reattribution else None
    signed_by_other = reattribution and any(c["kind"] == "S" and not c["uncertain"] and c["name"] != carver
                                            for c in rec["carvers"])
    probs = ctx["oof"].get(signum) or ctx["pred"].get(signum) or {}
    cross_validated = signum in ctx["oof"]
    m = ctx["model"]
    rk = m.rank_carvers(signum, 27) if signum in m.index else None
    ranking = (rk or {}).get("ranking") or []
    pos = {r["carver"]: i + 1 for i, r in enumerate(ranking)}
    ortho_row = next((r for r in ranking if r["carver"] == carver), None)
    alt = next((a for a in profile.get("alternatives") or [] if a["carver"] == carver), None)
    strength = alt["strength"] if alt else None
    # The proposed carver is found by spelling-based methods, so its language traits cannot count for it
    checks = _checks(rec, carver, inscriptions, ctx["names"], ctx["home"], selected=True)
    checks_cur = _checks(rec, current, inscriptions, ctx["names"], ctx["home"]) if current else None
    cs = carver_summary(carver, inscriptions)
    cs_cur = carver_summary(current, inscriptions) if current else None

    sig = (ortho_row or {}).get("significance") or {}
    # How far the orthography's first choice leads the second: a lead of 0.02 does not single a carver out
    margin = (ranking[0]["similarity"] - ranking[1]["similarity"]) if len(ranking) > 1 else None
    ortho_tied = pos.get(carver) == 1 and margin is not None and margin < 0.05 and (sig.get("p_adjusted") or 1) >= 0.05
    top_model = max(probs, key=probs.get) if probs else None
    stats = {"p_adjusted": sig.get("p_adjusted")} if pos.get(carver) == 1 else {}
    if probs:
        stats.update(model_top=top_model, model_p=probs.get(carver, 0.0))
    if pos.get(carver) == 1 and margin is not None:
        stats["ortho_margin"] = round(margin, 3)
    finding = {"signum": signum, "method": "samlade belägg", "verdict": "motsäger" if reattribution else "nytt",
               "suggested": carver, "existing": ", ".join(listed) or "ingen ristare", "evidence": strength or 0.0,
               "crosscheck": crosscheck or {}, "stats": stats}
    reading = interpret(finding, rec, ctx, profile)
    doc_type, conclusion, recommendation = _verdict(reading, signed_by_other, reattribution, carver)

    place = ", ".join(x for x in [rec.get("place"), rec.get("parish"), rec.get("district"), rec.get("municipality")] if x)
    kind_cur = ""
    if current:
        c0 = next((c for c in rec["carvers"] if c["name"] == current), None)
        kind_cur = {"S": "signerad", "A": "attribuerad"}.get((c0 or {}).get("kind"), "")
    pairs, wrong = _calibration(ctx)
    k_models = len(att.get("carvers") or probs) or 18
    near, skipped = _nearest(rec, carver, inscriptions)
    near_cur, skipped_cur = _nearest(rec, current, inscriptions) if current else ([], [])
    for_current = (_favours_current(rec, carver, current, probs, inscriptions, ctx["names"], checks)
                   if current and not signed_by_other else [])
    weak = reading["level"] not in ("starkt", "måttligt") or signed_by_other
    # A weak test that comes out in favour of Rundata's carver is a test of the attribution, and is titled so
    title = (f"Prövning av {signum}: Rundatas attribuering till {current} stöds"
             if current and weak and not signed_by_other and len(for_current) >= 2 else
             f"{doc_type}: {signum} – {carver}")

    blocks: list[dict] = [{"type": "title", "text": title,
                           "author": author, "institution": institution, "date": datetime.date.today().isoformat()}]
    if weak:
        blocks += [p("Internt arbetsunderlag. Ett svagt underlag bör inte skickas till runtextdatabasen som förslag om "
                     "ändring; dokumentet visar att en alternativ ristare har prövats och varför den inte håller.")]
    else:
        blocks += [p("Till: Samnordisk runtextdatabas, Institutionen för nordiska språk, Uppsala universitet "
                     "[Fyll i mottagare, t.ex. också Runor vid Riksantikvarieämbetet]")]

    # ---- summary and recommendation
    p_car, p_cur = probs.get(carver), (probs.get(current) if current else None)
    key_rows = []
    if probs:
        key_rows.append(["Statistisk modell", f"{carver}: {_n(p_car)}" + (f"; {current}: {_n(p_cur)}" if current else "")
                         + f"; högst: {top_model} {_n(probs[top_model])}",
                         "talar för" if top_model == carver and (p_car or 0) >= 0.5 else
                         ("svagt för" if top_model == carver else
                          f"talar emot (föredrar Rundatas {current})" if top_model == current else f"pekar på {top_model}")])
    if ranking:
        key_rows.append(["Ortografi", f"{carver}: plats {pos.get(carver, '–')} av {len(ranking)}"
                         + (f"; {current}: plats {pos.get(current, '–')}" if current else "")
                         + f"; närmast: {ranking[0]['carver']}",
                         "talar för" if pos.get(carver) == 1 and (sig.get("p_adjusted") or 1) < 0.05 else
                         (f"neutral (nästan lika för {ranking[1]['carver']}: {_n(ranking[0]['similarity'])} mot "
                          f"{_n(ranking[1]['similarity'])}, inte signifikant)" if ortho_tied else
                          "svagt för (likheten inte signifikant)" if pos.get(carver) == 1 else f"pekar på {ranking[0]['carver']}")])
    # Place and style are inputs to the model: when the model contributes they agree but are not independent support
    inside_model = {"område", "stil"} if probs else set()
    for k, (v, _) in checks.items():
        key_rows.append([CHECK_LABELS[k], ("stämmer" if v is True else "talar emot" if v is False else "avgör inte")
                         + (f" (för {current}: " + ("stämmer" if checks_cur[k][0] is True else "talar emot" if checks_cur[k][0] is False
                                                   else "avgör inte") + ")" if checks_cur else ""),
                         ("stämmer, men ingår i modellen" if k in inside_model else "talar för") if v is True
                         else "talar emot" if v is False else "neutral"])
    key_rows.append(["Huggteknik (3D)", "inte uppmätt", "–"])
    if signed_by_other:
        key_rows.insert(0, ["Signatur", f"stenen är signerad av {current}", "avgörande emot förslaget"])
    who_cur = " och ".join(listed) if len(listed) > 1 else current
    # Where the hypothesis came from: the Stone overview proposes a carver when the model or the orthography points to it
    origin = []
    if pos.get(carver) == 1:
        origin.append(f"ortografin rankar {carver} först (likhet {_n(ranking[0]['similarity'])}"
                      + (f", {_n(margin)} före {ranking[1]['carver']}" if margin is not None else "") + ")")
    if p_car is not None and top_model == carver:
        origin.append(f"modellen ger {carver} högst sannolikhet ({_n(p_car)})")
    elif p_car is not None and p_car >= 0.1:
        origin.append(f"modellen ger {carver} {_n(p_car)}")
    origin_txt = (f"Hypotesen kommer från Stenöversikten i Vitki, där {carver} visas som alternativ ristare eftersom "
                  f"{_join(origin)}. " if origin and alt else
                  f"{carver} har valts som hypotes av författaren; ingen av appens metoder lyfter fram ristaren. " if not alt else "")
    summary = (f"{signum} ({place or 'okänd plats'}) " +
               (f"är {kind_cur} {'av' if kind_cur == 'signerad' else 'till'} {who_cur} i Samnordisk runtextdatabas (Rundata). "
                if current else "saknar ristare i Samnordisk runtextdatabas (Rundata). ") + origin_txt +
               f"Det här dokumentet prövar om stenen kan knytas till {carver} och redovisar varje belägg för och emot. "
               f"Slutsats: {conclusion} Bedömning enligt appens regler: {reading['level']}"
               + (" (metoderna avviker från en signerad sten)" if reading["level"] == "metodfel" else "")
               + f"; {reading['support']} oberoende belägg för och {reading['against']} emot utöver modellen och ortografin.")
    if for_current:
        summary += (f" Jämfört med Rundatas ristare talar {len(for_current)} belägg för {current}: {'; '.join(for_current)}. "
                    "De är inte oberoende av varandra – modellen använder själv läge, stilgrupp och språkdrag – men de "
                    "pekar åt samma håll.")
    # The model alone can be strong while the combined assessment, which asks for independent support, is not
    share_wrong_car = (sum(w >= p_car for w in wrong) / len(wrong)) if (wrong and p_car is not None) else None
    if (top_model == carver and (p_car or 0) >= 0.5 and share_wrong_car is not None and share_wrong_car < 0.05
            and reading["level"] in ("måttligt", "svagt") and not signed_by_other and not for_current):
        summary += (f" Statistiska modellen ensam ger ett starkt belägg (en felaktig ristare når sällan {_n(p_car)}), och "
                    "Forskningsluckor bedömer därför modellens förslag som starkt. Ett beslut om attribuering kräver också "
                    "oberoende stöd – en statistiskt signifikant stavningslikhet, huggteknik eller en runologisk granskning – "
                    "och det saknas här, så den samlade bedömningen blir lägre.")
    blocks += [h(1, "Sammanfattning och rekommendation"), p(summary), p(f"Rekommendation: {recommendation}"),
               table(["Belägg", "Resultat", "För förslaget"], key_rows,
                     "Beläggen i korthet; varje rad förklaras i avsnitt 4. Beläggen är inte oberoende av varandra: modellen "
                     "använder själv läge, stilgrupp och språkdrag, och ortografin och språkdragen bygger båda på stavningen. "
                     "Bara bergart, nyare källor och huggteknik ligger helt utanför modellen och ortografin.")]

    # ---- 1. the stone
    dm = dims or {}
    size = ", ".join(f"{_n(dm[k])} m {w}" for k, w in (("height_m", "hög"), ("width_m", "bred")) if dm.get(k))
    rows = [["Signum", signum], ["Plats", place or "–"], ["Placering", rec.get("placement") or "–"],
            ["Ristare i Rundata", rec.get("carver_raw") or "ingen angiven"],
            ["Stilgrupp", (rec.get("style") or "–") + (" (osäker)" if rec.get("style_uncertain") else "")],
            ["Datering", PERIODS.get(rec.get("dating") or "", rec.get("dating")) or "–"],
            ["Material", rec.get("material") or "–"]]
    if size:
        rows.append(["Mått (Kulturmiljöregistret)", size + (f", runhöjd {_n(dm.get('rune_height_cm'), 1)} cm" if dm.get("rune_height_cm") else "")])
    blocks += [h(1, "1. Stenen"), table(["", ""], rows, f"Uppgifter om {signum} (Samnordisk runtextdatabas).")]
    if rec.get("transliteration"):
        blocks.append(inscription(rec.get("transliteration", ""), (rec.get("normalization") or "").replace('"', ""),
                                  (rec.get("normalization_ows") or "").replace('"', ""), rec.get("translation_en", ""),
                                  "Samnordisk runtextdatabas"))

    # ---- 2. the carvers
    def carver_text(name: str, summ: dict) -> str:
        styles = ", ".join(f"{s} ({k})" for s, k in summ["styles"]) or "–"
        return (f"{name} står som ristare utan frågetecken i Rundata (signerad eller attribuerad) på {summ['n']} "
                f"inskrifter, varav {len(summ['signed'])} signerade, i {', '.join(f'{pv} ({k})' for pv, k in summ['provinces'])}. "
                f"Stilgrupper: {styles}."
                + (f" Kärnan (stilgrupper på minst en tiondel av stenarna: {', '.join(summ['core'])}) motsvarar enligt "
                   f"Gräslunds kronologi ungefär {summ['span'][0]}–{summ['span'][1]}." if summ["span"] else "")
                + (f" {CARVER_NOTES[name]}" if name in CARVER_NOTES else ""))
    blocks += [h(1, "2. Ristarna"), h(2, f"Den prövade ristaren: {carver}"), p(carver_text(carver, cs))]
    if current:
        blocks += [h(2, f"Rundatas ristare: {current}"), p(carver_text(current, cs_cur)),
                   p("I Mälarlandskapen bygger många attribueringar i Rundata på Axelson (1993), som vägde samman stil, "
                     "stavning och geografi. Signaturer är däremot direkta belägg.")]

    # ---- 3. the material
    n_runestones = sum(1 for r in inscriptions if is_runestone(r))
    ev = ctx.get("evaluation") or {}
    blocks += [h(1, "3. Material: vad stenen jämförs med"),
               bullets(["Samnordisk runtextdatabas (Rundata; RUNDATA.xls från 2018): "
                        + f"{len(inscriptions):,} inskrifter".replace(",", " ") + ", varav "
                        + f"{n_runestones:,}".replace(",", " ") + " svenska vikingatida runstenar.",
                        f"Statistiska modellen: {att.get('n_train', '–')} runstenar av de {k_models} ristare som har minst "
                        f"{att.get('min_inscriptions', 8)} stenar utan frågetecken i Rundata ({', '.join(att.get('carvers') or [])}).",
                        f"Ortografin: {ev.get('n_inscriptions', '–')} vikingatida inskrifter av {ev.get('n_carvers', '–')} "
                        f"ristare med minst {ev.get('min_inscriptions_per_carver', '–')} inskrifter utan frågetecken; stenen själv ingår "
                        "aldrig i ristarens profil.",
                        f"Språkdragen: ristarens inskrifter jämförda med de övriga runstenarna i landskapet ({province(rec)}).",
                        "Stilgrupper och dateringar: Gräslund (1998), som de anges i Rundata.",
                        "Bergart: Rundatas materialuppgifter för ristarens stenar och för landskapets runstenar.",
                        "Nyare källor: Runor 2020 (Riksantikvarieämbetet) och Wikidata, för att se om förslaget redan finns."])]

    # ---- 4. method by method
    blocks.append(h(1, "4. Metoderna och vad de visar"))
    # 4.1 model
    blocks.append(h(2, "4.1 Statistisk modell (slumpskog i R)"))
    blocks.append(p(f"Modellen är en slumpskog (random forest) med {att.get('trees', 500)} beslutsträd. Den har lärt sig vad som "
                    f"skiljer de {k_models} ristarnas stenar åt: läge (koordinater och landskap), stilgrupp, kors och "
                    "kortkvistrunor, språkdrag, formler, de vanligaste runbigrammen (stavningsmönster) och inskriftens innehåll. "
                    "Ornamentikens detaljer, runformer och huggteknik ingår inte."))
    if probs:
        blocks.append(p(("Stenen har en ristare i Rundata, så sannolikheterna är korsvaliderade: de kommer från en modell som "
                         "inte hade sett stenen. " if cross_validated else
                         "Stenen saknar ristare utan frågetecken i Rundata, så sannolikheterna kommer från modellen tränad på alla stenar "
                         "med känd ristare. ")
                        + f"Sannolikheten är modellens skattning av hur troligt det är att stenen är huggen av en viss ristare, "
                        f"under förutsättning att den är huggen av någon av de {k_models} ristarna. Sannolikheterna summerar till 1; "
                        f"utan någon information skulle varje ristare få omkring {_n(1 / k_models)}."))
        top5 = sorted(probs.items(), key=lambda kv: -kv[1])[:5]
        blocks.append(table(["Ristare", "Sannolikhet", ""],
                            [[c, _n(v), "prövad" if c == carver else ("Rundata" if c == current else "")] for c, v in top5]
                            + ([[carver, _n(p_car), "prövad"]] if carver not in dict(top5) and p_car is not None else []),
                            f"Modellens fem högsta sannolikheter för {signum}."))
        if p_car is not None and pairs:
            hit, n_hit = _hit_rate(pairs, p_car)
            share_wrong = sum(w >= p_car for w in wrong) / len(wrong) if wrong else None
            overall = next((x for x in att.get("ablation") or [] if x.get("features") == "Alla"), {})
            grouped = ((att.get("grouped_cv") or {}).get("Socken") or {})
            g_all = next((x for x in grouped.get("ablation") or [] if x.get("features") == "Alla"), {})
            blocks.append(p(("Stenen saknar ristare, så sannolikheten är inte korsvaliderad för just den; hur ofta en sådan "
                             "sannolikhet stämmer skattas från korsvalideringen på stenar med känd ristare. " if not cross_validated else "")
                            + f"Hur ska sannolikheten {_n(p_car)} för {carver} läsas? I korsvalideringen på {len(wrong)} stenar med "
                            f"känd ristare var en ristare som fick en sannolikhet mellan {_n(max(0, p_car - 0.05))} och "
                            f"{_n(p_car + 0.05)} den rätta i {hit} av {n_hit} fall ({_pct(hit / n_hit if n_hit else None)}). "
                            f"En felaktig ristare fick minst {_n(p_car)} på {_pct(share_wrong)} av stenarna. "
                            + (f"Modellens förstaval är rätt på {_pct(overall.get('accuracy'))} av stenarna med känd ristare"
                               + (f" ({_pct(g_all.get('accuracy'))} när hela socknar hölls utanför)" if g_all.get("accuracy") is not None else "")
                               + f", mot {_pct(att.get('majority_baseline'))} om man alltid gissar på den mest produktiva ristaren. "
                               if overall else "")
                            + ("Sannolikheten är alltså så hög att en felaktig ristare sällan når den."
                               if share_wrong is not None and share_wrong < 0.05 else
                               "En så låg sannolikhet får felaktiga ristare ofta, så den är inget belägg för förslaget."
                               if share_wrong is not None and share_wrong >= 0.2 else
                               "Sannolikheten är ett måttligt belägg.")))
        if current and p_cur is not None:
            blocks.append(p(f"Rundatas ristare {current} får {_n(p_cur)}"
                            + (f", alltså mer än {carver}. Modellen stöder Rundatas attribuering snarare än förslaget." if p_cur > (p_car or 0)
                               else f", alltså mindre än {carver}.")))
    else:
        blocks.append(p("Modellen har ingen bedömning av stenen: den ligger utanför modellens område (mer än 25 km från en "
                        "träningssten) eller saknar uppgifterna modellen behöver."))
    # 4.2 orthography
    blocks.append(h(2, "4.2 Ortografi (stavning, skiljetecken, bindrunor)"))
    blocks.append(p("Ortografin jämför hur orden i stenens inskrift är stavade, vilka skiljetecken och bindrunor som används, med "
                    "varje ristares övriga inskrifter. Egennamn räknas inte, så att en signatur inte avslöjar svaret, och stenen "
                    "ingår aldrig i ristarens egen profil. Likheten (0–1) prövas mot hur lika andra ristares inskrifter är "
                    "profilen; p-värdet justeras för att den mest lika av alla ristare valts ut (max-statistik)."))
    if ranking:
        show = ranking[:5] + [r for r in ranking[5:] if r["carver"] in (carver, current)]
        blocks.append(table(["Plats", "Ristare", "Likhet", "p", "Justerat p", "Typikalitet", "Inskrifter"],
                            [[str(pos[r["carver"]]), r["carver"] + (" (prövad)" if r["carver"] == carver else " (Rundata)" if r["carver"] == current else ""),
                              _n(r["similarity"]), _pv((r.get("significance") or {}).get("p_value")),
                              _pv((r.get("significance") or {}).get("p_adjusted")),
                              _pct((r.get("significance") or {}).get("own_percentile")), str(r.get("n_inscriptions", "–"))]
                             for r in show],
                            f"Stavningens likhet med ristarnas inskrifter ({rk['n_words']} läsbara ord i {signum}). Typikalitet: "
                            "hur stor del av ristarens egna inskrifter som liknar profilen mindre än stenen gör."))
        prec = ((ev.get("per_carver") or {}).get(carver) or {}).get("precision")
        blocks.append(p((f"Kort text: med {rk['n_words']} ord är jämförelsen osäker. " if rk["n_words"] < 12 else "")
                        + (f"När ortografin föreslår {carver} har den rätt i {_pct(prec)} av de korsvaliderade fallen. "
                           if prec is not None else "")
                        + (f"Stavningen ligger närmast {ranking[0]['carver']}"
                           + (", Rundatas ristare." if ranking[0]["carver"] == current else
                              ", den prövade ristaren." if ranking[0]["carver"] == carver else ".")
                           + (" Likheten är statistiskt signifikant." if ((ranking[0].get("significance") or {}).get("p_adjusted") or 1) < 0.05
                              else " Likheten är inte statistiskt signifikant.")
                           + (f" Förstavalet leder bara med {_n(margin)} i likhet, så ortografin skiljer inte {ranking[0]['carver']} "
                              f"från {ranking[1]['carver']}; den räknas som neutral." if ortho_tied else ""))))
    else:
        blocks.append(p("Inskriften är för kort eller för skadad för en jämförelse av stavningen."))
    # 4.3–4.6 area, style, language, rock
    titles = {"område": "4.3 Område", "stil": "4.4 Stilgrupp", "språkdrag": "4.5 Språkdrag (ljud och språkbruk)",
              "bergart": "4.6 Bergart"}
    explain = {"område": "Arbetade ristaren i trakten? Stenen jämförs med ristarens stenar (utan frågetecken i Rundata): samma "
                         "landskap och högst 60 km till närmaste sten räknas som rimligt.",
               "stil": "Passar stenens stilgrupp ristarens? En stilgrupp på minst en tiondel av ristarens stenar räknas till "
                       "ristarens kärna och stämmer. En ovanlig stilgrupp inom kärnans tidsram avgör inte; ligger den utanför "
                       "tidsramen talar den emot, och mer än 25 år från kärnan enligt Gräslunds kronologi starkt emot.",
               "språkdrag": "Tjugo drag i ljud, stavning, språkbruk och skrift jämförs med ristarens inskrifter och med andra "
                            "stenar i landskapet: ett drag talar för ristaren när stenens form är tydligt vanligare hos ristaren "
                            "än annars i trakten (kvot minst 1,5), emot när den är tydligt ovanligare (kvot högst 0,67). Andelar "
                            "som bygger på färre än tio av ristarens inskrifter är osäkra och markeras. Eftersom den prövade ristaren har föreslagits av metoder som själva bygger på stavningen, "
                            "kan språkdragen tala emot men inte räknas som oberoende stöd för den.",
               "bergart": "Rundatas material för stenen jämförs med ristarens stenar; en bergart som är lika vanlig i hela "
                          "landskapet skiljer inte ristare åt."}
    for k in ("område", "stil", "språkdrag", "bergart"):
        blocks += [h(2, titles[k]), p(explain[k]), p(f"{carver}: {checks[k][1]}")]
        if checks_cur:
            blocks.append(p(f"{current}: {checks_cur[k][1]}"))
        if k == "språkdrag":
            lang = language_check(rec, carver, inscriptions, ctx["names"], selected=True)
            rows_l = [r for r in (lang or {}).get("rows") or [] if not r.get("repeats")]
            if rows_l:
                blocks.append(table(["Drag", "Stenen", f"Hos {carver}", f"I {province(rec)}", "Kvot", ""],
                                    [[r["label"], r["stone"], f"{_pct(r['share'])} av {r['n']}" + (" (få)" if r["n"] < 10 else ""),
                                      _pct(r.get("region_share")), _n(r.get("lr")),
                                      "" if r.get("lr") is None else "för" if r["lr"] >= 1.5 else "emot" if r["lr"] <= 1 / 1.5 else "neutral"]
                                     for r in rows_l],
                                    f"Stenens språkdrag mot {carver}s inskrifter och landskapets övriga runstenar. Kvot över 1 "
                                    "talar för ristaren, under 1 emot."))
    # 4.7 technique, 4.8 newer sources
    blocks += [h(2, "4.7 Huggteknik (3D)"),
               p("Huggspåren är inte uppmätta i underlaget för det här dokumentet. Huggteknik är det belägg som ligger längst "
                 "från stavning och plats och därför skulle tillföra mest: en 3D-skanning av stenen, med minst 20 mätta runor, "
                 f"jämförd med flera säkra stenar av {carver}" + (f" och av {current}" if current else "") + ".")]
    cc = crosscheck or {}
    lit = [f"Sveriges runinskrifter: {sri_reference(signum)}" if sri_reference(signum) else "Stenens utgåva i Sveriges runinskrifter bör kontrolleras."]
    runor = cc.get("runor") or {}
    from src.crosscheck import agrees_with_rundata
    if runor.get("text"):
        lit.append(f"Runor 2020 (Riksantikvarieämbetet): {runor['text']}"
                   + (" Runor är en senare utgåva av samma databas, så det är inget oberoende belägg."
                      if current and agrees_with_rundata(cc, rec) else ""))
    if runor.get("references"):
        lit.append("Litteratur i Runor att gå igenom: " + "; ".join(runor["references"][:8]))
    if (cc.get("wikidata") or {}).get("text"):
        lit.append(f"Wikidata: {cc['wikidata']['text']}")
    if not runor and not cc.get("wikidata"):
        lit.append("Förslaget är inte avstämt mot Runor 2020 och Wikidata.")
    blocks += [h(2, "4.8 Litteratur och nyare källor"), bullets(lit)]

    # ---- 5. other candidates
    others = [a for a in profile.get("alternatives") or [] if a["carver"] != carver]
    blocks.append(h(1, "5. Andra tänkbara ristare"))
    if others:
        blocks.append(table(["Ristare", "Samlad styrka", "Modell", "Ortografi", "Område, stil, språk, bergart"],
                            [[a["carver"], _n(a["strength"]), _n(a["model"]), _n(a["orthography"]),
                              ", ".join(("✓" if v else "✕") if v is not None else "–" for v in a["checks"].values())]
                             for a in others],
                            "Andra ristare som modellen eller ortografin pekar på. Den samlade styrkan (0–1) väger samman modell "
                            "och ortografi efter deras träffsäkerhet och räknas ned när kontrollerna inte klaras."))
    else:
        blocks.append(p("Ingen annan ristare får något nämnvärt stöd av modellen eller ortografin."))
    if current:
        blocks.append(p(f"Stödet för Rundatas ristare {current} är {_n(profile.get('support'))} på en skala 0–1, från "
                        f"{profile.get('n_sources')} metoder (ett viktat medelvärde av hur väl metoderna stämmer med ristaren)."
                        + (f" Den samlade styrkan för {carver}, {_n(strength)}, är ett annat mått – modell och ortografi "
                           "sammanvägda och nedräknade när kontrollerna inte klaras – och ska inte jämföras rakt av med stödet."
                           if strength is not None else "")))
    elif strength is not None:
        blocks.append(p(f"Den samlade styrkan för {carver} är {_n(strength)}."))

    # ---- 6. assessment
    # The other evidence is set out method by method in section 4; here only the weighing
    blocks += [h(1, "6. Samlad bedömning")] + [p(f"{x['title']}. {x['text']}") for x in reading["paragraphs"][1:-1]
                                              if not x["title"].startswith("Andra belägg")]
    blocks.append(p(f"Vägt samman: utöver modellen och ortografin, som är grunden för den samlade styrkan, talar "
                    f"{reading['support']} oberoende belägg för {carver} och {reading['against']} emot. Område och stilgrupp "
                    "räknas inte som oberoende stöd när modellen bidrar, eftersom den själv använder dem, och språkdragen "
                    "inte, eftersom de bygger på samma stavning som ortografin; de kan däremot tala emot."))
    if for_current:
        blocks.append(p(f"Jämförelsen med Rundatas ristare. Det som skiljer de två ristarna åt talar för {current}: "
                        f"{'; '.join(for_current)}. Beläggen hänger ihop (modellen använder läge, stilgrupp och språkdrag), så de "
                        f"ska inte räknas som {len(for_current)} oberoende skäl, men inget av dem talar för {carver}."))
    blocks.append(p(f"Slutsats. {conclusion} {recommendation}"))

    # ---- 7. what would decide it
    last = reading["paragraphs"][-1]["text"] if reading["paragraphs"] else ""
    marker = "Det som skulle kunna avgöra frågan:"
    tail = last.split(marker, 1)[1].strip().rstrip(".") if marker in last else ""
    steps = [tail[:1].upper() + tail[1:] + "."] if tail else []
    if signed_by_other:
        steps = [f"Inget mer behövs för attribueringen: signaturen avgör. Vill man förstå varför metoderna pekar på {carver} "
                 "kan stenen jämföras med de närmaste stenarna av båda ristarna nedan – ett samarbete eller en verkstad kan ge "
                 "liknande drag."]
    if near or near_cur:
        steps.append("Jämför ornamentik och runformer med de närmaste stenarna där ristaren är ensam ristare och som finns "
                     "kvar: " + "; ".join(f"{name}: " + ", ".join(_ref_text(x) for x in lst)
                                         for name, lst in ((carver, near), (current, near_cur)) if name and lst) + "."
                     + (" Närmare stenar som lämnats bort, eftersom flera ristare nämns eller stenen är försvunnen: "
                        + "; ".join(_skip_text(x) for x in skipped + skipped_cur) + "." if skipped or skipped_cur else ""))
    blocks += [h(1, "7. Vad som skulle kunna avgöra frågan"), bullets(steps)]

    # ---- 8. source criticism
    # Only the limitations that bear on this document: no grooves are measured and the stone's size is not used
    blocks += [h(1, "8. Källkritik och begränsningar"),
               bullets([CIRCULARITY_NOTE,
                        f"Modellen kan bara välja bland sina {k_models} ristare. Är stenen huggen av någon annan pekar den ändå "
                        "ut den mest lika av dem.",
                        "Ornamentikens detaljer, runformer och huggteknik ingår inte i metoderna; de är just de belägg en "
                        "runolog väger tyngst."]
                       + [limitations.bullet(x) for x in limitations.select(["attribution", "statistics", "rundata"])
                          if x["key"] in DOC_LIMITATIONS])]

    # ---- 9. glossary, method, references
    blocks += [h(1, "9. Ordlista"), bullets(GLOSSARY),
               h(1, "10. Metod och reproducerbarhet"),
               p(f"Framtaget med Vitki {versions.get('app', '')} ({APP_URL}; öppen källkod, {REPO_URL}). "
                 f"R-korpusens version {versions.get('fingerprint', '–')}, förteckningen över kända brister version "
                 f"{limitations.VERSION}. Metoderna beskrivs i METHODS.md: ortografi (avsnitt 6), språkdrag (8), bergart "
                 "(10), samlade belägg per sten (13c), tolkning (13d), attribueringsförslag (14f) och statistiken i R (17). "
                 "Samma data och samma version ger samma resultat."),
               h(1, "Referenser"),
               bullets(["Axelson, J. 1993. Mellansvenska runristare. Förteckning över signerade och attribuerade inskrifter. (Runrön 5.) Uppsala.",
                        "Breiman, L. 2001. Random forests. Machine Learning 45, s. 5–32.",
                        "Gräslund, A.-S. 1998. Ornamentiken som dateringsgrund för Upplands runstenar. I: Innskrifter og datering / Dating inscriptions. Trondheim, s. 73–91.",
                        "Samnordisk runtextdatabas. Institutionen för nordiska språk, Uppsala universitet.",
                        "Runor. Riksantikvarieämbetet, utgåva 2020 av Samnordisk runtextdatabas. https://runor.raa.se"]
                       + ([sri_reference(signum)] if sri_reference(signum) else []))]

    # ---- appendix: the stones compared
    def stone_list(name: str) -> str:
        sts = [r for r in inscriptions if name in certain_carvers(r) and r["signum"] != signum]
        return ", ".join(r["signum"] + ("*" if any(c["name"] == name and c["kind"] == "S" and not c["uncertain"] for c in r["carvers"]) else "")
                         for r in sts)
    blocks += [h(1, "Bilaga: ristarnas stenar i jämförelsen (utan frågetecken i Rundata)"),
               p(f"{carver} ({cs['n']} inskrifter; * = signerad): {stone_list(carver)}.")]
    if current:
        blocks.append(p(f"{current} ({cs_cur['n']} inskrifter; * = signerad): {stone_list(current)}."))
    who = ", ".join(x for x in (author, institution) if x) or "[Fyll i namn]"
    blocks.append(p(f"Kontakt: {who}, {email.strip() or '[Fyll i e-post]'}"))
    return blocks


DOC_LIMITATIONS = {"cv_leakage", "exploratory", "rundata"}

CIRCULARITY_NOTE = ("Modellen och ortografin är tränade på Rundatas attribueringar, i Mälardalen främst Axelsons (1993), som "
                    "själv vägde in stil, stavning och geografi. När metoderna stämmer med Rundata är det därför inte helt "
                    "oberoende bekräftelse, och när de avviker kan det bero på att attribueringen gjordes på grunder som "
                    "metoderna inte ser, som ornamentik och runformer.")
