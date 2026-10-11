"""Attribueringsförslag: alla argument för en ristare till en sten, som ett dokument att skicka till dem som
förvaltar runtextdatabasen (se METHODS.md, 14f).

Dokumentet samlar det appen vet om stenen och om den föreslagna ristaren: modellens sannolikhet, ortografins
likhet med p-värde, område, stilgrupp, språkdrag och bergart, andra tänkbara ristare och varför de väger lättare,
avstämningen mot Runor 2020 och Wikidata, en tolkning, metodens kända brister och hur resultaten kan upprepas.
Allt är framräknat; ingen AI-text.
"""
from __future__ import annotations

import datetime
from collections import Counter

from src import limitations
from src.academic import bullets, h, p, table
from src.interpretation import interpret
from src.research_gaps import certain_carvers, province
from src.stone_overview import _checks, stone
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
    styles = Counter(r["style"] for r in stones if r["style"] in BY_CODE and not r["style_uncertain"])
    n = sum(styles.values())
    years = [(BY_CODE[s]["from"], BY_CODE[s]["to"]) for s, k in styles.items() if BY_CODE[s].get("from") and k >= 0.1 * n]
    return {"n": len(stones), "signed": signed, "provinces": Counter(province(r) for r in stones).most_common(4),
            "styles": styles.most_common(5), "span": (min(y[0] for y in years), max(y[1] for y in years)) if years else None}


def build(rec: dict, carver: str, ctx: dict, crosscheck: dict | None, dims: dict | None, author: str,
          institution: str, versions: dict) -> list[dict]:
    """Rapportens block (src/academic.py-formatet)."""
    signum = rec["signum"]
    inscriptions = ctx["inscriptions"]
    profile = stone(rec, ctx, detail=True)
    listed = profile.get("carvers") or []
    reattribution = bool(listed) and carver not in listed
    probs = ctx["oof"].get(signum) or ctx["pred"].get(signum) or {}
    m = ctx["model"]
    rk = m.rank_carvers(signum, 5) if signum in m.index else None
    ortho_row = next((r for r in (rk or {}).get("ranking", []) if r["carver"] == carver), None)
    ortho_pos = [r["carver"] for r in (rk or {}).get("ranking", [])].index(carver) + 1 if ortho_row else None
    checks = _checks(rec, carver, inscriptions, ctx["names"], ctx["home"])
    cs = carver_summary(carver, inscriptions)
    alt = next((a for a in profile.get("alternatives") or [] if a["carver"] == carver), None)
    strength = alt["strength"] if alt else None

    # The reasoning, as in Forskningsluckor (src/interpretation.py)
    sig = (ortho_row or {}).get("significance") or {}
    finding = {"signum": signum, "method": "samlade belägg", "verdict": "motsäger" if reattribution else "nytt",
               "suggested": carver, "existing": ", ".join(listed) or "ingen ristare", "evidence": strength or 0.0,
               "crosscheck": crosscheck or {},
               "stats": {"p_adjusted": sig.get("p_adjusted")} if ortho_pos == 1 else {}}
    reading = interpret(finding, rec, ctx, profile)

    place = ", ".join(x for x in [rec.get("place"), rec.get("parish"), rec.get("district"), rec.get("municipality")] if x)
    kind = "omprövning av attribuering" if reattribution else "attribuering"
    blocks: list[dict] = [{"type": "title", "text": f"Förslag till {kind}: {signum} – {carver}",
                           "author": author, "institution": institution, "date": datetime.date.today().isoformat()}]
    blocks += [p("Till: Samnordisk runtextdatabas, Institutionen för nordiska språk, Uppsala universitet "
                 "[Fyll i mottagare, t.ex. också Runor vid Riksantikvarieämbetet]")]

    ok = [CHECK_LABELS[k].lower() for k, (v, _) in checks.items() if v is True]
    bad = [CHECK_LABELS[k].lower() for k, (v, _) in checks.items() if v is False]
    summary = (f"{signum} ({place or 'okänd plats'}) " + (f"attribueras i Rundata till {', '.join(listed)}. " if listed
               else "saknar ristare i Samnordisk runtextdatabas. ")
               + f"Vi föreslår att stenen {'i stället ' if reattribution else ''}knyts till {carver}. "
               + (f"Den statistiska modellen ger {carver} sannolikheten {_n(probs.get(carver))}. " if carver in probs else "")
               + (f"Stavningen ligger närmast {carver}s inskrifter (plats {ortho_pos} av {len(rk['ranking'])}). " if ortho_pos else "")
               + (f"{', '.join(ok).capitalize()} stämmer med ristarens säkra stenar" if ok else "")
               + (f"; {', '.join(bad)} talar emot" if bad else "") + (". " if ok or bad else "")
               + "Förslaget är en hypotes byggd på statistiska jämförelser och bör prövas runologiskt.")
    blocks += [h(1, "Sammanfattning"), p(summary)]

    # 1. The stone
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

    # 2. The proposed carver
    styles = ", ".join(f"{s} ({k})" for s, k in cs["styles"]) or "–"
    blocks += [h(1, f"2. {carver} i Rundata"),
               p(f"{carver} står som säker ristare (signerad eller attribuerad) på {cs['n']} runstenar, varav "
                 f"{len(cs['signed'])} signerade, i {', '.join(f'{pv} ({k})' for pv, k in cs['provinces'])}. "
                 f"Stilgrupper: {styles}"
                 + (f", vilket enligt Gräslunds kronologi motsvarar ungefär {cs['span'][0]}–{cs['span'][1]}." if cs["span"] else ".")
                 + (f" Signerade stenar: {', '.join(cs['signed'][:12])}{' …' if len(cs['signed']) > 12 else ''}." if cs["signed"] else "")
                 + (f" {CARVER_NOTES[carver]}" if carver in CARVER_NOTES else ""))]

    # 3. The evidence, method by method
    ev_rows = []
    if probs:
        top3 = sorted(probs.items(), key=lambda kv: -kv[1])[:3]
        ev_rows.append(["Statistisk modell (R)", f"{carver}: {_n(probs.get(carver, 0.0))}; främsta: "
                        + ", ".join(f"{c} {_n(v)}" for c, v in top3),
                        "stöder" if top3[0][0] == carver else ("delvis" if probs.get(carver, 0) >= 0.2 else "talar emot")])
    else:
        ev_rows.append(["Statistisk modell (R)", "Ingen bedömning (stenen ligger utanför modellens område eller ristaren ingår inte).", "–"])
    if ortho_row:
        sig = ortho_row.get("significance") or {}
        ev_rows.append(["Ortografi", f"Plats {ortho_pos}, likhet {_n(ortho_row['similarity'])} på {rk['n_words']} ord"
                        + (f"; p {_pv(sig.get('p_value'))}, justerat för valet av den bästa ristaren {_pv(sig.get('p_adjusted'))}" if sig else ""),
                        ("stöder" if (sig.get("p_adjusted") is None or sig["p_adjusted"] < 0.05) else "stöder, men likheten är inte säkerställd")
                        if ortho_pos == 1 else ("delvis" if ortho_pos <= 3 else "talar emot")])
    elif rk:
        ev_rows.append(["Ortografi", f"{carver} finns inte bland de fem närmaste (först: {rk['ranking'][0]['carver']}).", "talar emot"])
    else:
        ev_rows.append(["Ortografi", "För kort eller oläst text.", "–"])
    for k, (v, text) in checks.items():
        ev_rows.append([CHECK_LABELS[k], text, "stöder" if v is True else ("talar emot" if v is False else "–")])
    ev_rows.append(["Huggteknik (3D)", "Inte uppmätt i underlaget för det här förslaget.", "–"])
    blocks += [h(1, "3. Beläggen"), table(["Metod", "Resultat", "Bedömning"], ev_rows,
                                          f"Vad varje metod säger om {carver} som ristare till {signum}.")]

    # 4. Other candidates
    others = [a for a in profile.get("alternatives") or [] if a["carver"] != carver]
    if listed and reattribution:
        blocks += [h(1, "4. Rundatas ristare och andra kandidater"),
                   p(f"Stödet för Rundatas ristare {profile.get('carver')} är {_n(profile.get('support'))} från "
                     f"{profile.get('n_sources')} metoder (samma metoder som ovan).")]
    else:
        blocks.append(h(1, "4. Andra tänkbara ristare"))
    if others:
        blocks.append(table(["Ristare", "Styrka", "Modell", "Ortografi", "Kontroller (område, stil, språk, bergart)"],
                            [[a["carver"], _n(a["strength"]), _n(a["model"]), _n(a["orthography"]),
                              ", ".join(("✓" if v else "✕") if v is not None else "–" for v in a["checks"].values())]
                             for a in others],
                            "Andra ristare som modellen eller ortografin pekar på; styrkan väger samman modell och ortografi "
                            "och räknas ned när kontrollerna inte klaras."))
    else:
        blocks.append(p("Ingen annan ristare får något nämnvärt stöd av modellen eller ortografin."))
    if strength is not None:
        blocks.append(p(f"Den samlade styrkan för {carver} är {_n(strength)} på en skala 0–1 (Stenöversikt, se metod nedan)."))

    # 5. Literature and newer sources
    cc = crosscheck or {}
    lit = [f"Sveriges runinskrifter: {sri_reference(signum)}" if sri_reference(signum) else "Stenens utgåva i Sveriges runinskrifter bör kontrolleras."]
    runor = cc.get("runor") or {}
    if runor.get("text"):
        lit.append(f"Runor 2020 (Riksantikvarieämbetet): {runor['text']}")
    if runor.get("references"):
        lit.append("Litteratur i Runor att gå igenom: " + "; ".join(runor["references"][:8]))
    if (cc.get("wikidata") or {}).get("text"):
        lit.append(f"Wikidata: {cc['wikidata']['text']}")
    if not runor and not cc.get("wikidata"):
        lit.append("Förslaget är inte avstämt mot Runor 2020 och Wikidata.")
    blocks += [h(1, "5. Litteratur och nyare källor"), bullets(lit)]

    # 6. Reading
    blocks += [h(1, "6. Tolkning")] + [p(f"{x['title']}. {x['text']}") for x in reading["paragraphs"][2:]]

    # 7. Limitations
    lims = limitations.select(["attribution", "statistics", "rundata", "software"])
    blocks += [h(1, "7. Kända brister"), bullets([limitations.bullet(x) for x in lims])]

    # 8. Method and reproducibility
    blocks += [h(1, "8. Metod och reproducerbarhet"),
               p(f"Framtaget med Vitki {versions.get('app', '')} ({APP_URL}; öppen källkod, {REPO_URL}). "
                 f"R-korpusens version {versions.get('fingerprint', '–')}, förteckningen över kända brister version "
                 f"{limitations.VERSION}. Metoderna beskrivs i METHODS.md: ortografi (avsnitt 6), språkdrag (8), bergart "
                 "(10), samlade belägg per sten (13c), tolkning (13d) och statistiken i R (17). Ortografin jämför stenen med "
                 "ristarnas profiler utan att stenen själv ingår; modellens sannolikheter är korsvaliderade för stenar med "
                 "ristare och förslag för stenar utan."),
               h(1, "Referenser"),
               bullets(["Axelson, J. 1993. Mellansvenska runristare. Förteckning över signerade och attribuerade inskrifter. (Runrön 5.) Uppsala.",
                        "Gräslund, A.-S. 1998. Ornamentiken som dateringsgrund för Upplands runstenar. I: Innskrifter og datering / Dating inscriptions. Trondheim, s. 73–91.",
                        "Samnordisk runtextdatabas. Institutionen för nordiska språk, Uppsala universitet.",
                        "Runor. Riksantikvarieämbetet, utgåva 2020 av Samnordisk runtextdatabas. https://runor.raa.se"]
                       + ([sri_reference(signum)] if sri_reference(signum) else [])),
               p(f"Kontakt: {author}{', ' + institution if institution else ''} [Fyll i e-post]")]
    return blocks
