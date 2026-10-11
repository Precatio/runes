"""Tolkning av ett fynd i Forskningsluckor (se METHODS.md, 13d).

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
        out.append(f"Modellen ger {f.get('suggested')} sannolikheten {_num(st.get('probability'))}{cv}. "
                   f"Vid den nivån har modellens förstaval varit rätt i omkring {round((st.get('accuracy') or 0) * 100)} % av fallen.")
        if st.get("p_truth") is not None:
            out.append(f"Rundatas ristare får {_num(st['p_truth'])}.")
        out.append("Modellen är tränad på attribueringar som delvis bygger på samma drag (stil, stavning, geografi), "
                   "så den är inte helt oberoende av forskningsläget.")
    elif method == "huggteknik":
        out.append("Huggtekniken jämförs med uppmätta stenar i mätkorpusen; måtten är inte validerade som spår av "
                   "ristarens hand och påverkas av bergart och vittring.")
    elif method.startswith("stilgrupp"):
        out.append("Stilgruppen är en AI-bedömning av en bild och är inte kalibrerad.")
    ev = f.get("evidence") or 0
    out.append(f"Sammantaget bedöms belägget som {'starkt' if ev >= 0.6 else ('måttligt' if ev >= 0.35 else 'svagt')} "
               f"({_num(ev)} på en skala 0–1).")
    return out


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
    paragraphs.append({"title": "Hur starkt belägget är", "text": " ".join(_strength(f))})

    # 3. The other methods on the same carver
    support = against = 0
    lines = []
    if sug and not style_method:
        chk = _checks(rec, sug, ctx["inscriptions"], ctx["names"], ctx["home"])
        ok = [CHECK_NAMES[k] for k, (v, _) in chk.items() if v is True]
        bad = [CHECK_NAMES[k] for k, (v, _) in chk.items() if v is False]
        unknown = [CHECK_NAMES[k] for k, (v, _) in chk.items() if v is None]
        support += len(ok)
        against += len(bad)
        if ok:
            lines.append(f"{_join(ok).capitalize()} stämmer med {sug}.")
        if bad:
            lines.append(f"{_join(bad).capitalize()} talar emot ({'; '.join(chk[k][1] for k, (v, _) in chk.items() if v is False)})")
        if unknown:
            lines.append(f"{_join(unknown).capitalize()} kan inte prövas.")
        probs = ctx["oof"].get(rec["signum"]) or ctx["pred"].get(rec["signum"]) or {}
        if not method.startswith("statistisk modell") and probs:
            p = probs.get(sug, 0.0)
            top = max(probs, key=probs.get)
            if top == sug and p >= 0.3:
                support += 1
                lines.append(f"Den statistiska modellen pekar också på {sug} ({_num(p)}).")
            elif p < 0.1:
                against += 1
                lines.append(f"Den statistiska modellen pekar i stället på {top} ({_num(probs[top])}; {sug} {_num(p)}).")
        ortho = (profile or {}).get("orthography")
        if method != "ortografi" and ortho:
            order = [r["carver"] for r in ortho["ranking"]]
            if order and order[0] == sug:
                support += 1
                lines.append(f"Ortografin pekar också på {sug}.")
            elif sug not in order[:3]:
                against += 1
                lines.append(f"Ortografin pekar i stället på {order[0]}.")
        if verdict == "motsäger" and profile and profile.get("support") is not None:
            lines.append(f"Stödet för Rundatas ristare {profile.get('carver')} är {_num(profile['support'])} från "
                         f"{profile.get('n_sources')} metoder (Stenöversikt).")
    paragraphs.append({"title": f"Andra belägg för {sug}" if sug and not style_method else "Andra belägg",
                       "text": " ".join(lines) if lines else "Inga andra metoder kan uttala sig om förslaget."})

    # 4. Newer sources
    cc = f.get("crosscheck") or {}
    status = cc.get("status")
    cc_text = {
        "finns redan": "Förslaget finns redan i Runor 2020 eller Wikidata – en bekräftelse av metoden snarare än ny kunskap.",
        "nämns": "Ristaren nämns i Runors anmärkningar om stenen; läs dem innan förslaget förs fram som nytt.",
        "annan ristare": "Runor 2020 anger en annan ristare än förslaget.",
        "samma som": "Runor knyter stenen till samma namnlösa ristare som en annan sten.",
        "saknas": "Varken Runor 2020 eller Wikidata har förslaget.",
    }.get(status, "Förslaget är inte avstämt mot nyare källor (knappen ovanför tabellen).")
    paragraphs.append({"title": "Nyare källor", "text": cc_text})

    # 5. Conclusion and what could settle it
    ev = f.get("evidence") or 0
    signed = any(c["kind"] == "S" and not c["uncertain"] for c in rec["carvers"])
    st = f.get("stats") or {}
    # A spelling similarity that may be chance (adjusted p ≥ 0.05) keeps the conclusion from "starkt"
    p_ok = not (method in ("ortografi", "samlade belägg") and st.get("p_adjusted") is not None and st["p_adjusted"] >= 0.05)
    rundata_supported = verdict == "motsäger" and (profile or {}).get("support") is not None and profile["support"] >= 0.6
    if verdict == "motsäger" and status == "annan ristare":
        against += 1  # Runor 2020 sides with another carver than the suggestion
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
    elif ev >= 0.5 and support >= 3 and against == 0 and p_ok:
        level = "starkt"
        text = (f"Ett välgrundat förslag: belägget är starkt och {support} andra belägg stämmer med {sug} utan att något talar emot. "
                + ("Attribueringen i Rundata kan behöva omprövas." if verdict == "motsäger" else "Värt att pröva runologiskt."))
    elif ev >= 0.35 and support >= against:
        level = "måttligt"
        text = (f"Ett rimligt men osäkert förslag: {support} andra belägg stämmer med {sug}"
                + (f" och {against} talar emot" if against else "") + ". "
                + ("Stavningslikheten är inte säkerställd när man räknar med att den bästa av alla ristare valts. " if not p_ok else "")
                + ("Värt en närmare granskning, men inte ett starkt argument mot Rundata." if verdict == "motsäger"
                   else "Det behöver stöd från fler håll innan det förs fram."))
    else:
        level = "svagt"
        text = (f"Ett svagt förslag: belägget är {'svagt' if ev < 0.35 else 'måttligt'} och "
                + (f"{against} andra belägg talar emot." if against > support else "för få andra belägg stöder det.")
                + (" Sannolikt en svaghet i metoden; övriga belägg stöder Rundata." if verdict == "motsäger" else ""))
    steps = []
    if sug and not style_method:
        steps.append(f"en 3D-mätning av huggspåren jämförd med säkra stenar av {sug} (minst 20 runor per sten enligt riktvärdet)")
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
