"""Tolkning av ett fynd i Forskningsluckor (se METHODS.md, 14d).

Ett fynd från en metod (ortografi, statistisk modell, huggteknik, AI-stilgrupp) vägs samman med det som de
andra metoderna säger om samma sten och samma ristare – område, stilgrupp, språkdrag, bergart, modellens
sannolikhet och ortografins rangordning – och med avstämningen mot nyare källor. Resultatet är ett resonemang i
fem steg och en slutsats på en av sex nivåer. Reglerna är fasta och redovisas här, så att tolkningen kan
granskas; den är en hjälp att läsa fynden, inte en runologisk bedömning.

Slutsatsens nivåer:
  redan känt    förslaget finns redan i Runor 2020 eller Wikidata
  metodfel      fyndet motsäger en signerad sten (talar mot metoden, inte mot ristaren)
  bekräftelse   fyndet stämmer med Rundata
  starkt        beläggen ≥ 0,5, minst tre andra belägg för ristaren och inget emot, och – för ortografin – en
                likhet som inte kan vara slump (justerat p < 0,05)
  måttligt      beläggen ≥ 0,35 och minst lika många andra belägg för som emot
  svagt         i övriga fall, och när ett fynd som motsäger Rundata står mot ett stöd ≥ 0,6 för Rundatas ristare
                från de andra metoderna
"""
from __future__ import annotations

from src.research_gaps import certain_carvers, province
from src.synthesis import carver_styles
from src.stone_overview import _checks

CHECK_NAMES = {"område": "området", "stil": "stilgruppen", "språkdrag": "språkdragen", "bergart": "bergarten"}


def _num(v, digits=2) -> str:
    return "–" if v is None else f"{v:.{digits}f}".replace(".", ",")


def _p(v) -> str:
    return "–" if v is None else ("< 0,001" if v < 0.001 else _num(v, 3))


def _join(items: list[str]) -> str:
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " och " + items[-1]


def _strength(f: dict) -> list[str]:
    """Meningar om hur starkt fyndet är, beroende på metod."""
    st = f.get("stats") or {}
    method = f.get("method", "")
    out = []
    if method == "ortografi" and st:
        out.append(f"Stavningen liknar {f.get('suggested')}s inskrifter med likheten {_num(st.get('similarity'))}, "
                   f"{_num(st.get('margin'))} mer än för {st.get('second')}, på {st.get('n_words')} läsbara ord.")
        if st.get("p_adjusted") is not None:
            pa = st["p_adjusted"]
            if pa < 0.01:
                out.append(f"Likheten är mycket osannolik som slump även när man räknar med att den bästa av alla ristare "
                           f"valts (p {_p(st.get('p'))}, justerat {_p(pa)}).")
            elif pa < 0.05:
                out.append(f"Likheten är osannolik som slump (p {_p(st.get('p'))}, justerat för valet av den bästa ristaren {_p(pa)}).")
            else:
                out.append(f"Likheten kan vara slump när man räknar med att den bästa av alla ristare valts "
                           f"(p {_p(st.get('p'))}, justerat {_p(pa)}).")
        out.append(f"När metoden föreslår {f.get('suggested')} har den rätt i omkring {round((st.get('precision') or 0) * 100)} % "
                   "av de korsvaliderade fallen.")
        if (st.get("n_words") or 0) < 12:
            out.append("Texten är kort, vilket gör stavningen till ett svagt underlag.")
        if (st.get("margin") or 0) < 0.03:
            out.append("Marginalen till nästa ristare är liten.")
        if st.get("in_area") is False:
            out.append("Stenen ligger utanför ristarens kända landskap.")
    elif method.startswith("statistisk modell") and st:
        cv = " (korsvaliderat: modellen hade inte sett stenen)" if st.get("cross_validated") else ""
        if st.get("bin_n"):
            acc_text = (f"Vid den nivån har modellens förstaval varit rätt i {st['bin_correct']} av {st['bin_n']} prövade "
                        f"stenar med känd ristare (95 % konfidensintervall {round(st['acc_lo'] * 100)}–{round(st['acc_hi'] * 100)} %).")
        else:
            acc_text = f"Vid den nivån har modellens förstaval varit rätt i omkring {round((st.get('accuracy') or 0) * 100)} % av fallen."
        out.append(f"Modellen ger {f.get('suggested')} sannolikheten {_num(st.get('probability'))}{cv}. {acc_text} "
                   "Sannolikheten gäller under förutsättning att ristaren är en av modellens ristare.")
        if st.get("q_value") is not None:
            share = round(st["p_value"] * 100, 1)
            out.append((f"En felaktig ristare fick minst lika hög sannolikhet på {_num(share, 1)} % av de prövade stenarna med "
                        f"känd ristare (q {_p(st['q_value'])} justerat för alla modellens förslag) – förslaget är "
                        + ("statistiskt signifikant." if st["q_value"] < 0.05 else "inte statistiskt signifikant.")))
        if st.get("p_truth") is not None:
            out.append(f"Rundatas ristare får {_num(st['p_truth'])}.")
        out.append("Modellen är tränad på attribueringar som delvis bygger på samma drag (stil, stavning, geografi), "
                   "så den är inte helt oberoende av forskningsläget.")
    elif method.startswith("okänd ristare") and st:
        out.append(f"Stenen ingår i en grupp av {st.get('n')} stenar utan ristare som liknar varandra i stavning, språkdrag, "
                   f"formler och stil (arbetsnamn {st.get('group')}, typsten {st.get('type_stone')}). När metoden prövades på "
                   f"stenar med känd ristare bestod en grupp i genomsnitt till {round((st.get('purity') or 0) * 100)} % av "
                   "samma ristare.")
        out.append("Gruppen kan vara en ristare, en verkstad eller en lokal tradition. Arbetsnamnet är en etikett för "
                   "gruppen, inte ett påstående om en person.")
    elif method == "huggteknik":
        out.append("Huggtekniken jämförs med uppmätta stenar i mätkorpusen; måtten är inte validerade som spår av "
                   "ristarens hand och påverkas av bergart och vittring.")
    elif method.startswith("stilgrupp"):
        out.append("Stilgruppen är en AI-bedömning av en bild och är inte kalibrerad.")
    ev = f.get("evidence") or 0
    grade = "stark" if ev >= 0.6 else ("måttlig" if ev >= 0.35 else "svag")
    if method == "samlade belägg":  # the decision document: the strength combines the model and the orthography
        # The number alone can look strong while its parts are not: say why it should not be read as strong
        sug = f.get("suggested")
        caveats = []
        if st.get("model_top") is not None and (st["model_top"] != sug or (st.get("model_p") or 0) < 0.5):
            caveats.append(f"modellen ger {sug} {_num(st.get('model_p') or 0)}"
                           + (f" och föredrar {st['model_top']}" if st["model_top"] != sug else ""))
        if st.get("p_adjusted") is None or st["p_adjusted"] >= 0.05:
            caveats.append("stavningslikheten är inte statistiskt signifikant"
                           + (f" (justerat p {_p(st['p_adjusted'])})" if st.get("p_adjusted") is not None else ""))
        if st.get("ortho_margin") is not None and st["ortho_margin"] < 0.05:
            caveats.append(f"ortografins förstaval leder bara med {_num(st['ortho_margin'])} i likhet")
        if grade != "svag" and caveats:
            out.append(f"Den samlade styrkan från modellen och ortografin är {_num(ev)} på en skala 0–1, men talet ska "
                       f"inte läsas som {grade}t stöd: {_join(caveats)}. Slutsatsen nedan väger också in de andra beläggen.")
        else:
            out.append(f"Den samlade styrkan från modellen och ortografin är {grade} ({_num(ev)} på en skala 0–1); "
                       "slutsatsen nedan väger också in de andra beläggen.")
    else:
        out.append(f"Metodens eget belägg är {grade}t ({_num(ev)} på en skala 0–1); slutsatsen nedan väger också in de "
                   "andra beläggen.")
    return out


def _typicality(rec: dict, carver: str, ctx: dict) -> float | None:
    """Hur typisk stenens stavning är för ristaren: andelen av ristarens egna stenar (lämna-en-ute) som liknar
    ristarens profil mindre än stenen gör. Ett lågt värde betyder att stenen bara är 'minst olik' ristaren."""
    m = ctx.get("model")
    if m is None or rec["signum"] not in m.index:
        return None
    rk = m.rank_carvers(rec["signum"], 60)
    if not rk or rk["n_words"] < 5:
        return None
    hit = next((r for r in rk["ranking"] if r["carver"] == carver), None)
    sig = (hit or {}).get("significance") or {}
    return sig.get("own_percentile")


def _model_agrees(rec: dict, sug: str, ctx: dict) -> bool:
    """Modellen har den föreslagna ristaren som förstaval med minst 0,5 (då har förstavalet varit rätt i omkring 95 %)."""
    probs = ctx["oof"].get(rec["signum"]) or ctx["pred"].get(rec["signum"]) or {}
    return bool(probs) and max(probs, key=probs.get) == sug and probs[sug] >= 0.5


def interpret(f: dict, rec: dict, ctx: dict, profile: dict | None) -> dict:
    """f: fyndet; rec: Rundatas post; ctx: stone_overview.context; profile: stone_overview.stone(..., detail=True)."""
    sug = f.get("suggested")
    verdict = f.get("verdict")
    method = f.get("method", "")
    style_method = method.startswith("stilgrupp")
    existing = f.get("existing") or "ingen ristare"
    paragraphs = []

    # 1. What the finding says
    if style_method:
        say = f"AI-bedömningen av bilden ger stilgruppen {sug}; Rundata anger {existing}."
    elif verdict == "nytt":
        say = f"Metoden ({method}) föreslår {sug} för en sten som saknar ristare i Rundata."
    elif verdict == "motsäger":
        say = f"Metoden ({method}) pekar på {sug}, medan Rundata anger {existing}."
    else:
        say = f"Metoden ({method}) pekar på samma ristare som Rundata: {sug}."
    paragraphs.append({"title": "Vad fyndet säger", "text": say})

    # 2. How strong it is
    strength = _strength(f)
    if sug and not style_method and (method == "ortografi" or method.startswith("statistisk modell")):
        prov = province(rec)
        attributed = [r for r in ctx["inscriptions"] if province(r) == prov and certain_carvers(r)]
        share = sum(1 for r in attributed if sug in certain_carvers(r)) / len(attributed) if attributed else 0
        if share >= 0.1:
            strength.insert(-1, f"{sug} står för {round(share * 100)} % av de attribuerade stenarna i landskapet. Produktiva "
                                "ristare drar till sig förslag, och träffsäkerheten för deras förslag mäter metoden i "
                                "allmänhet snarare än den här stenen.")
    paragraphs.append({"title": "Hur starkt belägget är", "text": " ".join(strength)})

    # 3. The other methods on the same carver
    support = against = 0
    lines = []
    style_conflict = None
    anonymous_carver = False
    model_method = False
    if sug and not style_method:
        # A carver picked by a spelling-based method gets no independent support from the language traits; the model
        # also uses place and style, so they cannot support its suggestion either (they can still speak against it)
        by_spelling = method in ("ortografi", "samlade belägg") or method.startswith(("statistisk modell", "okänd ristare"))
        model_method = method.startswith("statistisk modell")
        # The combined evidence (the decision document, src/attribution_report.py) is already built from the model and
        # the orthography: they are not counted again, and when the model contributes, place and style are inside it
        combined = method == "samlade belägg"
        probs_c = (ctx["oof"].get(rec["signum"]) or ctx["pred"].get(rec["signum"]) or {}) if combined else {}
        dependent = ({"område", "stil", "språkdrag"} if model_method or (combined and probs_c)
                     else ({"språkdrag"} if by_spelling else set()))
        chk = _checks(rec, sug, ctx["inscriptions"], ctx["names"], ctx["home"], selected=by_spelling)
        sc = carver_styles(rec, sug, ctx["inscriptions"])
        if sc.get("strong"):
            style_conflict = sc
        ok = [CHECK_NAMES[k] for k, (v, _) in chk.items() if v is True and k not in dependent]
        within = [CHECK_NAMES[k] for k, (v, _) in chk.items() if v is True and k in dependent]
        bad = [CHECK_NAMES[k] for k, (v, _) in chk.items() if v is False]
        # None means either no data or a result that does not decide either way; the latter is shown with its text
        cannot = ("För få", "Bergarten kan inte", "Ristarens stenar saknar")
        unknown = [CHECK_NAMES[k] for k, (v, t) in chk.items() if v is None and (not t or t.startswith(cannot))]
        undecided = [(CHECK_NAMES[k], t) for k, (v, t) in chk.items() if v is None and t and not t.startswith(cannot)]
        support += len(ok)
        against += len(bad)
        if ok:
            lines.append(f"{_join(ok).capitalize()} stämmer med {sug}.")
        if within:
            lines.append(f"{_join(within).capitalize()} stämmer också, men ingår redan i metoden och räknas inte som "
                         "oberoende stöd.")
        if bad:
            lines.append(f"{_join(bad).capitalize()} talar emot ({'; '.join(chk[k][1] for k, (v, _) in chk.items() if v is False)})")
        for name, t in undecided:
            lines.append(f"{name.capitalize()} avgör inte frågan: {t[:1].lower() + t[1:]}")
        if unknown:
            lines.append(f"{_join(unknown).capitalize()} kan inte prövas.")
        probs = ctx["oof"].get(rec["signum"]) or ctx["pred"].get(rec["signum"]) or {}
        if not method.startswith("statistisk modell") and probs:
            p = probs.get(sug, 0.0)
            top = max(probs, key=probs.get)
            if top == sug and p >= 0.3:
                support += 0 if combined else 1
                lines.append(f"Den statistiska modellen pekar också på {sug} ({_num(p)}).")
            elif p < 0.1:
                against += 0 if combined else 1
                lines.append(f"Den statistiska modellen pekar i stället på {top} ({_num(probs[top])}; {sug} {_num(p)}).")
        ortho = (profile or {}).get("orthography")
        if method != "ortografi" and ortho:
            order = [r["carver"] for r in ortho["ranking"]]
            if order and order[0] == sug:
                support += 0 if combined else 1
                lines.append(f"Ortografin pekar också på {sug}.")
            elif sug not in order[:3]:
                against += 0 if combined else 1
                lines.append(f"Ortografin pekar i stället på {order[0]}.")
        if combined:
            lines.append("Modellen och ortografin är grunden för den samlade styrkan och räknas inte en gång till"
                         + ("; område och stilgrupp ingår i modellen och räknas inte som oberoende stöd." if probs else "."))
        linked = rec.get("same_carver_as") or []
        if linked and not [c for c in rec["carvers"] if c["kind"] in ("S", "A")]:
            anonymous_carver = True
            lines.append(f"Rundata anger att samma namnlösa ristare har gjort {_join(linked)}. Modellerna kan bara välja "
                         f"bland kända ristare; om den namnlösa ristaren inte är en av dem måste de ändå välja någon, och "
                         f"{sug} kan då vara den minst dåliga kandidaten snarare än rätt.")
            for other in linked:
                op = ctx["oof"].get(other) or ctx["pred"].get(other) or {}
                if op:
                    otop = max(op, key=op.get)
                    if otop == sug:
                        lines.append(f"Modellen föreslår {sug} även för {other} ({_num(op[otop])}), vilket stämmer med att "
                                     "stenarna har samma ristare.")
                    else:
                        against += 1
                        lines.append(f"För {other}, som enligt Rundata har samma ristare, föreslår modellen i stället "
                                     f"{otop} ({_num(op[otop])}; {sug} {_num(op.get(sug, 0))}) – en varningssignal.")
                else:
                    lines.append(f"{other} kan inte prövas av modellen (för lite läsbar text eller för långt från "
                                 "modellens stenar).")
        typ = _typicality(rec, sug, ctx)
        if typ is not None and typ < 0.1:
            against += 1
            lines.append(f"Stavningen liknar {sug} mindre än {round((1 - typ) * 100)} % av {sug}s egna stenar gör – stenen "
                         "är atypisk för ristaren, och förslaget kan vara det minst dåliga valet snarare än en verklig likhet.")
        elif typ is not None:
            lines.append(f"Stavningen liknar {sug} lika mycket som {round(typ * 100)} % av {sug}s egna stenar gör eller mer – "
                         "stenen är inte atypisk för ristaren.")
        if verdict == "motsäger" and profile and profile.get("support") is not None:
            lines.append(f"Stödet för Rundatas ristare {profile.get('carver')} är {_num(profile['support'])} från "
                         f"{profile.get('n_sources')} metoder (Stenöversikt).")
    paragraphs.append({"title": f"Andra belägg för {sug}" if sug and not style_method else "Andra belägg",
                       "text": " ".join(lines) if lines else "Inga andra metoder kan uttala sig om förslaget."})

    # 4. Newer sources
    cc = f.get("crosscheck") or {}
    status = cc.get("status")
    from src.crosscheck import agrees_with_rundata
    same_source = verdict == "motsäger" and status == "annan ristare" and agrees_with_rundata(cc, rec)
    cc_text = {
        "finns redan": "Förslaget finns redan i Runor 2020 eller Wikidata – en bekräftelse av metoden snarare än ny kunskap.",
        "nämns": "Ristaren nämns i Runors anmärkningar om stenen; läs dem innan förslaget förs fram som nytt.",
        "annan ristare": "Runor 2020 anger en annan ristare än förslaget.",
        "samma som": "Runor knyter stenen till samma namnlösa ristare som en annan sten.",
        "saknas": "Varken Runor 2020 eller Wikidata har förslaget.",
    }.get(status, "Förslaget är inte avstämt mot nyare källor (knappen ovanför tabellen).")
    if same_source:
        cc_text = (f"Runor 2020 anger samma ristare som Rundata ({existing}). Runor är en senare utgåva av samma databas, "
                   "så det är inget oberoende belägg: det visar bara att attribueringen inte har ändrats sedan 2014.")
    paragraphs.append({"title": "Nyare källor", "text": cc_text})

    # 5. Conclusion and what could settle it
    ev = f.get("evidence") or 0
    signed = any(c["kind"] == "S" and not c["uncertain"] for c in rec["carvers"])
    st = f.get("stats") or {}
    # A spelling similarity that may be chance (adjusted p ≥ 0.05) keeps the conclusion from "starkt"
    p_ok = not (method in ("ortografi", "samlade belägg") and st.get("p_adjusted") is not None and st["p_adjusted"] >= 0.05)
    # The same for the model: a suggestion that wrong carvers often reach is not "starkt"
    model_sig_ok = not (method.startswith("statistisk modell") and st.get("q_value") is not None and st["q_value"] >= 0.05)
    rundata_supported = verdict == "motsäger" and (profile or {}).get("support") is not None and profile["support"] >= 0.6
    if verdict == "motsäger" and status == "annan ristare" and not same_source:
        against += 1  # Runor 2020 sides with another carver than both the suggestion and Rundata
    if status == "finns redan":
        level, text = "redan känt", f"Förslaget är redan känt i den nyare forskningen. Att metoden kommer fram till samma sak talar för metoden."
    elif verdict == "motsäger" and signed:
        level, text = "metodfel", "Stenen är signerad. Avvikelsen visar en svaghet i metoden, inte att ristaren är fel."
    elif verdict == "stämmer":
        level = "bekräftelse"
        text = (f"En bekräftelse av Rundatas ristare{' från en oberoende metod' if method == 'huggteknik' else ''}"
                + (". Ortografin är inte helt oberoende, eftersom attribueringar kan bygga på stavningen." if method == "ortografi" else "."))
    elif rundata_supported:
        level = "svagt"
        text = (f"Övriga belägg stöder Rundatas ristare {profile.get('carver')} (stöd {_num(profile['support'])}). "
                "Avvikelsen är sannolikt en svaghet i metoden – eller ett tecken på samarbete eller en verkstad – "
                "snarare än ett argument mot attribueringen.")
    elif style_conflict:
        level = "svagt"
        text = (f"Stilgruppen talar starkt emot: stenen har {rec.get('style')}, men {sug}s stenar har främst "
                f"{', '.join(style_conflict['core'])}, omkring {style_conflict['gap_years']} år senare enligt Gräslunds "
                "kronologi. Om stilbestämningen stämmer är förslaget kronologiskt problematiskt, oavsett hur lik stavningen "
                "är. Kontrollera beskrivningen av ornamentiken (Sveriges runinskrifter) innan förslaget drivs vidare.")
    elif anonymous_carver and ev >= 0.35 and against == 0:
        level = "måttligt"
        text = (f"En prövbar hypotes: modellen rangordnar {sug} högst, men Rundata räknar med en namnlös ristare bakom "
                f"stenen och {_join(rec.get('same_carver_as') or [])}, och modellen kan inte föreslå en namnlös ristare. "
                f"Frågan är alltså om den namnlösa ristaren är {sug} – det behöver prövas med ornamentik, runformer och "
                "huggteknik på alla stenarna, inte bara med modellen.")
    elif model_method and ev >= 0.5 and against == 0 and (st.get("acc_lo") or 0) >= 0.8 and model_sig_ok:
        level = "starkt"
        text = (f"Ett välgrundat förslag: vid den här sannolikheten har modellen haft rätt i {st.get('bin_correct')} av "
                f"{st.get('bin_n')} prövade fall, och inget av de andra beläggen talar emot. Plats, stil och språkdrag ingår "
                "redan i modellen och räknas inte som oberoende stöd; ett oberoende belägg, t.ex. huggteknik, skulle stärka "
                "förslaget. " + ("Attribueringen i Rundata kan behöva omprövas." if verdict == "motsäger" else "Värt att pröva runologiskt."))
    elif (method == "samlade belägg" and against == 0 and p_ok and st.get("p_adjusted") is not None
          and _model_agrees(rec, sug, ctx)):
        level = "starkt"
        text = (f"Ett välgrundat förslag: både den statistiska modellen och ortografin pekar på {sug}, stavningslikheten är "
                "statistiskt signifikant och inget av de andra beläggen talar emot. Metoderna delar stavningen och modellen "
                "använder också plats och stil, så ett belägg som ligger utanför dem – huggteknik, runformer eller "
                "ornamentik – skulle stärka förslaget. "
                + ("Attribueringen i Rundata kan behöva omprövas." if verdict == "motsäger" else "Värt att pröva runologiskt."))
    # Two independent pieces of evidence: with the language traits dependent on the spelling and a common rock neutral,
    # area and style are often all that can support a suggestion; a spelling similarity must then also be significant
    elif ev >= 0.5 and support >= 2 and against == 0 and p_ok and not model_method:
        level = "starkt"
        text = (f"Ett välgrundat förslag: belägget är starkt och {support} andra belägg stämmer med {sug} utan att något talar emot. "
                + ("Attribueringen i Rundata kan behöva omprövas." if verdict == "motsäger" else "Värt att pröva runologiskt."))
    elif ev >= 0.35 and support >= against:
        level = "måttligt"
        text = (f"Ett rimligt men osäkert förslag: {support} andra belägg stämmer med {sug}"
                + (f" och {against} talar emot" if against else "") + ". "
                + ("Stavningslikheten är inte signifikant när man räknar med att den bästa av alla ristare valts. " if not p_ok else "")
                + ("Värt en närmare granskning, men inte ett starkt argument mot Rundata." if verdict == "motsäger"
                   else "Det behöver stöd från fler håll innan det förs fram."))
    else:
        level = "svagt"
        text = (f"Ett svagt förslag: belägget är {'svagt' if ev < 0.35 else 'måttligt'} och "
                + (f"{against} andra belägg talar emot." if against > support else "för få andra belägg stöder det.")
                + (" Sannolikt en svaghet i metoden; övriga belägg stöder Rundata." if verdict == "motsäger" else ""))
    if not p_ok and level != "redan känt":
        # A negative result is also knowledge: it can test older attributions made on the same grounds
        text += (" Det hållbara resultatet är att stavningen ensam inte räcker för att attribuera stenen – likheten "
                 "uppstår lätt när man letar bland många ristare.")
    steps = []
    if sug and not style_method:
        stones = " och ".join([rec["signum"]] + list(rec.get("same_carver_as") or []))
        steps.append(f"en 3D-mätning av huggspåren på {stones}, jämförd med flera säkra stenar av {sug} (minst 20 runor "
                     "per sten enligt riktvärdet; ingen huggteknik är mätt för stenen ännu)")
        steps.append(f"en jämförelse av runformer och ornamentik med {sug}s signerade stenar")
    refs = (cc.get("runor") or {}).get("references") or []
    if refs:
        steps.append("en genomgång av litteraturen i Runor (" + "; ".join(refs[:3]) + ")")
    if method == "ortografi" and ((f.get("stats") or {}).get("n_words") or 0) < 12:
        steps.append("en nyläsning som kan ge fler säkra ord")
    if not rec.get("style") or rec.get("style_uncertain"):
        steps.append("en bedömning av ornamentiken (stilgruppen saknas eller är osäker)")
    if steps:
        text += " Det som skulle kunna avgöra frågan: " + _join(steps) + "."
    paragraphs.append({"title": "Tolkning", "text": text})
    return {"paragraphs": paragraphs, "level": level, "support": support, "against": against}
