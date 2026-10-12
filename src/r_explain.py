"""Statistiken i R förklarad för den som inte kan terminologin: en fråga per analys, svaret i korthet med ett
nyckeltal, hur säkert det är, ett förslag till tolkning och vad resultatet inte säger.

Texterna räknas fram ur korpusanalysernas resultat (src/r_bridge.py), så att de alltid stämmer med den senaste
beräkningen. Tolkningarna är förslag som följer reservationerna i METHODS.md 17 – inte runologiska slutsatser.

Säkerhet:
  säkert   resultatet är prövat (korsvalidering, permutationstest) och stämmer med vad forskningen utgår från
  troligt  resultatet håller statistiskt, men har viktiga reservationer (t.ex. beroende av attribueringarna)
  osäkert  ett mönster att pröva: svag struktur, eller hypoteser som behöver granskas runologiskt
"""
from __future__ import annotations

from src.research_gaps import PROVINCE_NAMES

CONFIDENCE_TEXT = {
    "säkert": "Säkert resultat",
    "troligt": "Troligt, med reservationer",
    "osäkert": "Osäkert – ett mönster att pröva",
}


def _pct(v) -> str:
    return "–" if v is None else f"{round(v * 100)} %"


def _d(v, k: int = 2) -> str:
    return "–" if v is None else f"{v:.{k}f}".replace(".", ",")


def _p(v) -> str:
    return "< 0,001" if v is not None and v < 0.001 else _d(v, 3)


def _sig(q) -> bool:
    """Signifikant efter justering (q kan vara exakt 0, som inte får räknas som saknat)."""
    return q is not None and q < 0.05


def _names(codes) -> str:
    names = [PROVINCE_NAMES.get(c, c) for c in codes]
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " och " + names[-1] if names else ""


def _list(v) -> list:
    """R writes a one-element vector as a plain value."""
    return [] if v is None else [v] if isinstance(v, str) else list(v)


def _section(key, question, why, headline, answer, confidence, interpretation, not_saying, short) -> dict:
    return {"key": key, "question": question, "why": why, "headline": headline, "answer": answer, "short": short,
            "confidence": confidence, "confidence_text": CONFIDENCE_TEXT[confidence],
            "interpretation": [t for t in interpretation if t], "not_saying": [t for t in not_saying if t]}


def geography(g: dict, remains: dict | None = None) -> dict | None:
    carvers = g.get("carvers") or []
    if not carvers:
        return None
    n, k = len(carvers), g.get("n_compact", 0)
    w = (g.get("water") or {}).get("overall") if (g.get("water") or {}).get("available") else None
    v = (g.get("water") or {}).get("viking_shore") or {}
    water = (f" Runstenarna står också närmare vatten än slumpvisa platser på land (median {_d(w['median_stones_km'], 1)} "
             f"mot {_d(w['median_random_km'], 1)} km)." if w and w.get("p", 1) < 0.05 else "")
    shore = bool(water and v.get("p") is not None and v["p"] < 0.05 and v["median_stones_km"] < v["median_random_km"])
    if shore:
        water += (f" Mot en grovt modellerad strandlinje omkring år 1000 blir skillnaden tydligare "
                  f"({_d(v['median_stones_km'], 1)} mot {_d(v['median_random_km'], 1)} km).")
    grave = {x["key"]: x for x in (remains or {}).get("distances") or []}.get("gravfalt") if (remains or {}).get("available") else None
    graves = (f" {_pct(grave['near_stones'])} av stenarna som inte är flyttade står inom "
              f"{round(((remains or {}).get('near_km') or 0.5) * 1000)} m från ett registrerat gravfält, mot "
              f"{_pct(grave['near_random'])} av slumpvisa platser." if grave and grave.get("q_bh", 1) < 0.05 else "")
    return _section(
        "geography", "Arbetade ristarna inom ett eget område?",
        "Om ristarna var bundna till en bygd säger stenens plats något om vem som kan ha ristat den – och om hur "
        "hantverket var organiserat.",
        {"value": f"{k} av {n}", "label": "ristare arbetade inom ett tydligt mindre område än slumpen ger"},
        f"De flesta ristare har sina stenar samlade: {k} av de {n} ristare som har minst {g.get('min_inscriptions', 5)} "
        f"säkra stenar arbetade inom ett mindre område än lika många slumpvis valda stenar i samma landskap.{water}{graves}",
        "säkert" if k / n >= 0.6 else "troligt",
        ["Ristarna var troligen lokala hantverkare som arbetade för beställare i sin egen bygd, snarare än vandrande "
         "specialister.",
         "Platsen är därför ett rimligt – men inte avgörande – argument när en sten ska attribueras.",
         "Närheten till vatten stämmer med att stenar restes vid färdvägar, där många passerade." if water else None,
         "Närheten till gravfälten består över tiden och gäller också kristna stenar: gravfälten kan ha förblivit släktens "
         "minnesplatser genom kristnandet." if graves else None],
        ["Testet är inte helt oberoende: forskarna har själva vägt in platsen när de attribuerat stenar, vilket gör "
         "ristarnas områden mer samlade.",
         ("Vattenkartan är grov; dåtidens strand är en grov modell med höjddata vars fel är av samma storleksordning som "
          "landhöjningen." if shore else "Vattenkartan är grov och visar dagens stränder, inte vikingatidens.") if water else None,
         "Kulturmiljöregistret är olika väl inventerat i olika trakter, och gravfälten är sällan daterade." if graves else None],
        f"Ja – {k} av {n} ristare arbetade inom ett eget, begränsat område.")


def attribution(a: dict) -> dict | None:
    ab = {x["features"]: x for x in a.get("ablation") or []}
    if "Alla" not in ab:
        return None
    acc, top3 = ab["Alla"]["accuracy"], ab["Alla"]["top3"]
    grouped = {k: {x["features"]: x for x in v.get("ablation") or []}.get("Alla", {}).get("accuracy")
               for k, v in (a.get("grouped_cv") or {}).items()}
    rel = {r["threshold"]: r for r in (a.get("calibration") or {}).get("reliability") or []}
    r50 = rel.get(0.5)
    lang, geo = (ab.get("Språk och innehåll") or {}).get("accuracy"), (ab.get("Geografi") or {}).get("accuracy")
    return _section(
        "attribution", "Kan statistiken föreslå vem som ristade en sten?",
        "Många runstenar saknar ristare i Rundata. En modell som har lärt sig de kända ristarnas drag – plats, stil, "
        "stavning, formler och innehåll – kan föreslå kandidater.",
        {"value": _pct(acc), "label": f"rätt ristare som förstaval, mot {_pct(a.get('majority_baseline'))} om man gissar"},
        f"När modellen prövas på stenar med känd ristare som den inte har sett, väljer den rätt ristare i {_pct(acc)} av "
        f"fallen och har rätt ristare bland de tre främsta i {_pct(top3)}."
        + (f" Även på en socken den aldrig sett blir det {_pct(grouped.get('Socken'))}." if grouped.get("Socken") else "")
        + (f" När den anger minst 50 % sannolikhet har förstavalet varit rätt i {_pct(r50['accuracy'])} av fallen."
           if r50 and r50.get("accuracy") else ""),
        "säkert",
        ["Modellen är ett bra hjälpmedel för att sortera fram kandidater, särskilt för stenar nära kända ristares "
         "områden.",
         "Sannolikheterna är försiktiga: när modellen säger 50 % har den oftast rätt oftare än så.",
         f"Stavning, formler och innehåll räcker långt på egen hand ({_pct(lang)} rätt); platsen ensam ger {_pct(geo)}."
         if lang and geo else None],
        [f"Modellen kan bara välja bland de {len(a.get('carvers') or [])} ristare den har tränats på; en okänd ristare "
         "kan den inte föreslå.",
         "Den har lärt sig av forskarnas egna attribueringar och mäter alltså hur väl den håller med dem – inte en "
         "oberoende sanning.",
         "Ett förslag för en enskild sten är en hypotes som behöver runologisk granskning."],
        f"Ja, med förbehåll – rätt ristare som förstaval i {_pct(acc)} av fallen, mot {_pct(a.get('majority_baseline'))} med gissning.")


def anonymous(an: dict) -> dict | None:
    groups = an.get("groups") or []
    v = an.get("validation") or {}
    if not groups or not v.get("purity"):
        return None
    cands = [g for g in groups if g.get("status") == "candidate"]
    known = len(groups) - len(cands)
    provs = []
    for g in cands:
        for p in _list(g.get("provinces")):
            if p not in provs:
                provs.append(p)
    examples = ", ".join(f"{g['name']} ({g['n']} stenar)" for g in cands[:3])
    return _section(
        "anonymous", "Finns det ristare som ännu inte har namn?",
        "Om en grupp stenar utan ristare liknar varandra lika mycket som en ristares stenar, kan det vara en okänd "
        "ristare eller verkstad.",
        {"value": str(len(cands)), "label": "möjliga okända ristare, med arbetsnamn efter socken"},
        f"{len(cands)} grupper av stenar utan ristare liknar varandra i stavning, språk, formler och stil lika mycket som "
        f"en ristares stenar, utan att likna någon känd ristare i närheten" + (f" – t.ex. {examples}" if examples else "")
        + f". Prövad på kända ristare bestod en sådan grupp i genomsnitt till {_pct(v['purity'])} av samma ristare, mot "
        f"{_pct(v.get('purity_geography'))} om man bara tar närliggande stenar.",
        "osäkert",
        [f"Kandidaterna finns i {_names(provs[:4])}, där få stenar är attribuerade – där är chansen störst att hitta "
         "ristare som forskningen inte har namngett." if provs else None,
         f"{known} andra grupper liknar en känd ristare. Att metoden där hittar kända ristare talar för att den fångar "
         "verkliga ristargrupper." if known else None,
         "Nästa steg är att jämföra ornamentik, runformer och huggteknik på stenarna i en grupp."],
        ["Arbetsnamnen är etiketter för grupperna, inte namn på personer.",
         "En grupp kan vara en ristare, en verkstad eller en lokal tradition som flera följde.",
         f"I genomsnitt kan omkring {_pct(1 - v['purity'])} av stenarna i en grupp vara av någon annan.",
         "Grupperna kan redan vara beskrivna i Sveriges runinskrifter eller annan litteratur som appen inte har."],
        f"Kanske – {len(cands)} grupper av stenar utan ristare kan vara okända ristare eller verkstäder.")


def chronology(ch: dict) -> dict | None:
    v = ch.get("validation") or {}
    if not v:
        return None
    region = PROVINCE_NAMES.get(ch.get("region"), ch.get("region"))
    unexplained = [d for d in ch.get("corpus_dimensions") or [] if d.get("unexplained")]
    return _section(
        "chronology", "Kan språk och innehåll datera stenarna?",
        "Runstenar dateras i dag främst efter ornamentiken (Gräslunds stilgrupper). Om språk och innehåll ändras i "
        "samma takt får kronologin stöd från ett oberoende håll.",
        {"value": _d(v.get("rho")), "label": "samband mellan språkets och ornamentikens tidsordning (0 = inget, 1 = samma)"},
        f"I {region} ordnar språkdrag, formler och innehåll stenarna i ungefär samma tidsföljd som stilgrupperna, fast "
        f"ornamentiken inte ingick. Ett årtal för en enskild sten blir däremot osäkert: felet är i genomsnitt "
        f"{v.get('mae_loo_years')} år, mot {v.get('mae_naive_years')} år om man gissar på genomsnittet.",
        "troligt" if v.get("usable") else "osäkert",
        ["Resultatet ger oberoende stöd åt stilkronologin: språk och ornamentik ändrades åt samma håll.",
         "Seriationen kan ge en grov placering – tidig, mittre eller sen – av stenar som saknar ornamentik, men inte "
         "ett årtal.",
         ("I hela landet finns dessutom ett mönster som varken följer tid eller plats; det kan vara ristarens eller "
          "beställarens val och är värt att pröva.") if unexplained else
         ("I hela landet följer formelvalet (t.ex. om stenen har en bön) mer ristaren än tiden – prövat icke-linjärt mot "
          "stilgruppen och mot omblandade ristaretiketter.") if any(list(d.get("explained_by") or []) == ["ristare"]
                                                                   for d in ch.get("corpus_dimensions") or []) else None],
        [f"Analysen gäller {region}, där stilkronologin är utarbetad. I hela landet styrs språket mer av region än av tid.",
         "Ordningen är säkrare än årtalen."],
        "Delvis – språket följer stilkronologins tidsordning, men årtalen för enskilda stenar är osäkra.")


SHAPE_WORD = {"rises": "blir vanligare", "falls": "blir ovanligare", "peak": "är vanligast omkring {y}",
              "trough": "är ovanligast omkring {y}", "flat": "förändras knappt"}


def change(c: dict) -> dict | None:
    feats = {f["key"]: f for f in c.get("features") or []}
    tested = [f for f in feats.values() if (f.get("time") or {}).get("tested")]
    if not tested:
        return None
    sig = [f for f in tested if _sig(f["time"].get("q"))]

    def t(key):
        f = feats.get(key) or {}
        tm = f.get("time") or {}
        return tm if tm.get("tested") and _sig(tm.get("q")) else None

    # The most telling changes first (a written norm, the writing system, Christianity), then the rest by size
    priority = ["stungna", "o_runa", "bon", "signatur", "ai_alla", "cross", "stungen_y", "stungen_e"]
    sig.sort(key=lambda f: (priority.index(f["key"]) if f["key"] in priority else 99,
                            -abs((f["time"].get("last") or 0) - (f["time"].get("first") or 0))))
    parts = []
    for f in sig[:4]:
        tm = f["time"]
        from src.r_findings import _peak
        word = SHAPE_WORD[tm["shape"]].format(y=_peak(tm))
        curve = [r["share"] for r in tm.get("curve") or []]
        if tm["shape"] == "peak" and curve:
            numbers = f"som mest {_pct(max(curve))}, på slutet {_pct(tm['last'])}"
        elif tm["shape"] == "trough" and curve:
            numbers = f"som minst {_pct(min(curve))}, på slutet {_pct(tm['last'])}"
        else:
            numbers = f"{_pct(tm['first'])} → {_pct(tm['last'])}"
        parts.append(f"{f['label'].split(' (')[0].lower()} {word} ({numbers})")
    interp = []
    st = t("stungen_e") or t("stungna")
    if st and st["shape"] == "rises":
        interp.append("Skriften förfinades: stungna runor, som skiljer e från i och y från u, blir vanliga under "
                      "1000-talet.")
        rows = ((feats.get("stungen_e") or {}).get("provinces") or {}).get("rows") or []
        cross = sorted([r for r in rows if r.get("cross_year")], key=lambda r: r["cross_year"])
        if len(cross) >= 2:
            interp.append(f"Stungen i blir vanlig tidigare i {PROVINCE_NAMES.get(cross[0]['province'], cross[0]['province'])} "
                          f"(omkring {cross[0]['cross_year']}) än i {PROVINCE_NAMES.get(cross[-1]['province'], cross[-1]['province'])} "
                          f"(omkring {cross[-1]['cross_year']}). Förändringen kan ha spridits därifrån – eller så hade "
                          "ristarskolorna där andra vanor.")
    o = t("o_runa")
    if o and o["shape"] == "rises":
        interp.append("o-runan tar över o-ljudet, ett tecken på att runornas ljudvärden ändrades under perioden.")
    b = t("bon")
    if b and b["shape"] == "peak":
        from src.r_findings import _peak
        interp.append(f"Kristna böner är vanligast omkring {_peak(b)} och nästan borta på de sena stenarna – kanske "
                      "för att kristendomen då var självklar, eller för att formlerna ändrades.")
    ai = t("ai_alla")
    if ai and ai["shape"] == "falls":
        interp.append("Stavningen med diftong (stain) breder ut sig över tid. Det liknar en skrivnorm som sprids snarare än "
                      "en ljudförändring – ett mönster att pröva mot den språkhistoriska litteraturen.")
    bro = next((a for a in c.get("assoc") or [] if a.get("key") == "bro_sjal"), None)
    if bro and (bro.get("all") or {}).get("q") is not None and bro["all"]["q"] < 0.05:
        interp.append(f"Bro- och vägstenar har oftare själsbön ({_pct(bro['share_x'])} mot {_pct(bro['share_other'])}), vilket "
                      "stämmer med tolkningen av brobyggen som själagåvor.")
    return _section(
        "change", "Hur förändrades språk, skrift och tro under 1000-talet?",
        "Runstenarna är den största källan till svenskt språk och kristnande under vikingatiden. Hur och var förändringar "
        "spreds säger något om kontakter och påverkan.",
        {"value": f"{len(sig)} av {len(tested)}", "label": "drag förändras tydligt över tid, med plats och ristare konstanta"},
        ("Med plats och ristare konstanta: " + "; ".join(parts) + ".") if parts else "Inga drag förändras tydligt över tid.",
        "troligt",
        interp,
        ["Tiden bygger på stilgrupper, som anger ett tidsintervall och främst finns för Uppland och Södermanland.",
         "Ändrad stavning är inte säkert ändrat uttal – den kan spegla skrivtradition och ristarskola."],
        f"Ja – {len(sig)} av {len(tested)} drag förändras, bland dem stungna runor, o-runan och de kristna bönerna."
        if sig else "Inga drag förändras tydligt.")


def language(t: dict, dl: dict) -> dict | None:
    lemmas = t.get("lemmas") or []
    m = dl.get("mantel") or {}
    if not lemmas and not m:
        return None
    top = lemmas[0] if lemmas else None
    forms = "/".join(f["form"] for f in (top or {}).get("forms", [])[:3])
    geo_ok = m.get("p") is not None and m["p"] < 0.05
    return _section(
        "text", "Har ristare och trakter egna sätt att stava?",
        "Stavningen kan avslöja både vem som ristade och vilken dialekt eller skrivtradition som fanns i trakten.",
        {"value": _d(m.get("r")) if m else _d((top or {}).get("cramers_v")),
         "label": "samband mellan stavning och avstånd (0 = inget, 1 = fullt)" if m else "samband mellan stavning och ristare"},
        (f"Ristarna har tydliga stavningsvanor – tydligast för '{top['lemma']}', som stavas t.ex. {forms}. " if top else "")
        + (f"Mellan {dl.get('n_districts')} härader skiljer sig stavningen mer ju längre ifrån varandra de ligger." if geo_ok
           else ""),
        "säkert" if geo_ok and top else "troligt",
        ["Stavningen är ett användbart spår när en sten ska attribueras: ristarna hade egna vanor.",
         "Att närliggande trakter stavar mer lika kan spegla dialekter eller lokala skrivtraditioner." if geo_ok else None],
        ["Eftersom ristare arbetade lokalt kan en stavningsgräns lika gärna gå mellan ristarverkstäder som mellan "
         "dialekter.",
         "Stavningsvanorna är inte oberoende av attribueringarna, som delvis bygger på stavningen."],
        "Ja – ristarna har egna stavningsvanor" + (", och stavningen skiljer sig mer ju längre ifrån varandra trakterna ligger."
                                                   if geo_ok else "."))


def clusters(c: dict) -> dict | None:
    if not c.get("k"):
        return None
    sil = c.get("best_silhouette") or 0
    return _section(
        "clusters", "Faller runstenarna i naturliga grupper?",
        "Om stenarna delar sig i tydliga grupper efter stil, språk och innehåll kan grupperna motsvara tider, trakter "
        "eller ristarskolor.",
        {"value": str(c["k"]), "label": f"grupper, men med {c.get('structure', 'svag')} struktur"},
        f"Stenarna delar sig i {c['k']} grupper, men gränserna är vaga. Grupperna sammanfaller inte med ristarna.",
        "osäkert" if sil < 0.35 else "troligt",
        ["Grupperna följer främst kors, stungna runor och böner – alltså tid och kristnande – snarare än vem som ristade.",
         "Runstenarna är ett sammanhängande material utan skarpa gränser mellan typer."],
        ["Med svag struktur är det osäkert vilken grupp en enskild sten hör till."],
        "Bara svagt – grupperna följer tid och kristnande, inte ristare.")


def network(nw: dict) -> dict | None:
    comms = nw.get("communities") or []
    if not comms:
        return None
    kin = sorted(nw.get("kinship") or [], key=lambda k: -k.get("n", 0))
    christian = [k for k in kin if k.get("q_christian") is not None and k["q_christian"] < 0.05 and k["n"] >= 20]
    return _section(
        "network", "Vilka ord och släktrelationer hör ihop?",
        "Runstensformlerna följer mönster. Vilka ord som står tillsammans visar hur formlerna är uppbyggda, och släktorden "
        "visar vem som reste stenar efter vem.",
        {"value": str(len(comms)), "label": "grupper av ord som ofta står i samma inskrifter"},
        f"De {nw.get('n_words')} vanligaste orden bildar {len(comms)} grupper som motsvarar formler."
        + (f" Vanligaste släktordet är '{kin[0]['relation']}' ({_pct(kin[0].get('share'))} av stenarna)." if kin else ""),
        "troligt",
        [("Släktrelationerna " + ", ".join(f"'{k['relation']}'" for k in christian[:3]) + " är vanligare i kristna inskrifter "
          "än i övriga.") if christian else None,
         "Formelgrupperna kan användas för att se vilka formler som hör till samma tradition eller tid."],
        ["Att ord står tillsammans visar formler, inte vad orden betydde för samtiden."],
        f"Orden bildar {len(comms)} grupper som motsvarar formler, och släktorden varierar med inskriftens innehåll.")


ORDER = ["attribution", "anonymous", "change", "chronology", "geography", "text", "clusters", "network"]


def sections(res: dict) -> list[dict]:
    """En förklaring per analys, i den ordning sidan visar dem; analyser utan resultat utelämnas."""
    built = {
        "geography": geography(res.get("geography") or {}, res.get("remains")),
        "attribution": attribution(res.get("attribution") or {}),
        "anonymous": anonymous(res.get("anonymous") or {}),
        "chronology": chronology(res.get("chronology") or {}),
        "change": change(res.get("change") or {}),
        "text": language(res.get("text") or {}, res.get("dialect") or {}),
        "clusters": clusters(res.get("clusters") or {}),
        "network": network(res.get("network") or {}),
    }
    return [built[k] for k in ORDER if built.get(k)]


def overview(res: dict) -> dict:
    """Helhetsbilden: vad analyserna tillsammans säger, i löpande text, och vad som är rimliga nästa steg."""
    g, a, an = res.get("geography") or {}, res.get("attribution") or {}, res.get("anonymous") or {}
    ch, c, cl = res.get("chronology") or {}, res.get("change") or {}, res.get("clusters") or {}
    dl, t = res.get("dialect") or {}, res.get("text") or {}
    paras, steps = [], []

    ab = {x["features"]: x for x in a.get("ablation") or []}
    carvers = g.get("carvers") or []
    if carvers and ab.get("Alla"):
        paras.append(
            f"**Ristarna och deras hand.** Ristarna var i regel lokala hantverkare med egna vanor: {g.get('n_compact')} av "
            f"{len(carvers)} ristare arbetade inom ett begränsat område, och stavningen skiljer tydligt mellan dem"
            + (" och mellan trakter" if (dl.get("mantel") or {}).get("p", 1) < 0.05 else "")
            + f". Därför kan statistiken känna igen en ristare: modellen väljer rätt i {_pct(ab['Alla']['accuracy'])} av "
            f"fallen när den prövas på stenar med känd ristare, mot {_pct(a.get('majority_baseline'))} om man gissar. "
            "Plats och stavning har dock också legat till grund för forskarnas attribueringar, så modellen mäter delvis "
            "hur väl den håller med forskningen.")
        steps.append("Gå igenom de starka ristarförslagen i Forskningsluckor och pröva dem mot ornamentik och litteratur.")

    cands = [x for x in an.get("groups") or [] if x.get("status") == "candidate"]
    if cands:
        provs = []
        for x in cands:
            for p in _list(x.get("provinces")):
                if p not in provs:
                    provs.append(p)
        v = an.get("validation") or {}
        paras.append(
            f"**Okända ristare.** Där få stenar är attribuerade – i {_names(provs[:4])} – finns {len(cands)} grupper av "
            "stenar som liknar varandra lika mycket som en ristares stenar utan att likna någon känd ristare, t.ex. "
            + ", ".join(x["name"] for x in cands[:3]) + ". De har fått arbetsnamn efter socken. Metoden är prövad på kända "
            f"ristare (i genomsnitt {_pct(v.get('purity'))} av en grupp samma ristare), men varje grupp är en hypotes: det "
            "kan vara en ristare, en verkstad eller en lokal tradition.")
        steps.append("Jämför ornamentik, runformer och gärna huggspår (3D) på stenarna i de okända ristarnas grupper.")

    v = ch.get("validation") or {}
    feats = {f["key"]: f for f in c.get("features") or []}

    def sig(key):
        tm = (feats.get(key) or {}).get("time") or {}
        return tm if tm.get("tested") and _sig(tm.get("q")) else None
    time_bits = []
    if v:
        time_bits.append(f"Språk och innehåll ordnar stenarna i samma tidsföljd som ornamentiken (rangkorrelation "
                         f"{_d(v.get('rho'))}), vilket ger stilkronologin stöd från ett oberoende håll – men årtal för "
                         "enskilda stenar blir osäkra.")
    st, o, b, ai = sig("stungna"), sig("o_runa"), sig("bon"), sig("ai_alla")
    changes = []
    if st and st["shape"] == "rises":
        changes.append(f"stungna runor blir vanligare ({_pct(st['first'])} → {_pct(st['last'])})")
    if o and o["shape"] == "rises":
        changes.append(f"o-runan tar över o-ljudet ({_pct(o['first'])} → {_pct(o['last'])})")
    if b and b["shape"] == "peak":
        from src.r_findings import _peak
        changes.append(f"kristna böner är vanligast omkring {_peak(b)}")
    if changes:
        time_bits.append("Under 1000-talet förändras skrift och tro, med plats och ristare konstanta: "
                         + ", ".join(changes[:-1]) + (" och " if len(changes) > 1 else "") + changes[-1] + ".")
    rows = ((feats.get("stungen_e") or {}).get("provinces") or {}).get("rows") or []
    cross = sorted([r for r in rows if r.get("cross_year")], key=lambda r: r["cross_year"])
    if len(cross) >= 2:
        time_bits.append(f"Stungen i blir vanlig omkring {cross[0]['cross_year']} i "
                         f"{PROVINCE_NAMES.get(cross[0]['province'], cross[0]['province'])} men först omkring "
                         f"{cross[-1]['cross_year']} i {PROVINCE_NAMES.get(cross[-1]['province'], cross[-1]['province'])} – "
                         "kanske en spridning in mot Mälardalen.")
    if ai and ai["shape"] == "falls":
        time_bits.append("Den diftongiska stavningen (stain) breder ut sig, vilket ser ut som en skrivnorm som sprids.")
    if time_bits:
        paras.append("**Tid och förändring.** " + " ".join(time_bits))
        steps.append("Pröva förändringsmönstren – diftongstavningen och de stungna runornas spridning – mot den "
                     "språkhistoriska litteraturen.")

    if cl.get("k"):
        paras.append(f"**Typer av stenar.** Runstenarna faller inte i skarpa typer: de {cl['k']} grupper som finns har vaga "
                     "gränser och följer tid och kristnande (kors, stungna runor, böner) snarare än ristare.")

    rm = res.get("remains") or {}
    grave = {x["key"]: x for x in rm.get("distances") or []}.get("gravfalt") if rm.get("available") else None
    v = (g.get("water") or {}).get("viking_shore") or {}
    if grave and grave.get("q_bh", 1) < 0.05:
        shore = v.get("p") is not None and v["p"] < 0.05 and v["median_stones_km"] < v["median_random_km"]
        paras.append(
            f"**Landskapet.** {_pct(grave['near_stones'])} av runstenarna som inte är flyttade står inom "
            f"{round((rm.get('near_km') or 0.5) * 1000)} m från ett registrerat gravfält, mot {_pct(grave['near_random'])} "
            "av slumpvisa platser i samma trakter"
            + (", och närheten är densamma före och efter 1050 och för kristna stenar." if all(
                ((rm.get("tests") or {}).get(k) or {}).get("q_bh", 0) >= 0.05 for k in ("time_gravfalt", "christian_gravfalt"))
               else ".")
            + (" Stenarna står också nära vatten, tydligare mot en modellerad strand omkring år 1000 än mot dagens."
               if shore else ""))
        steps.append("Pröva gravfältens roll mot undersökta gravfält med sena, kristna gravar.")

    bro = next((x for x in c.get("assoc") or [] if x.get("key") == "bro_sjal"), None)
    new_patterns = []
    if ai and ai["shape"] == "falls":
        new_patterns.append("diftongstavningens spridning")
    if len(cross) >= 2:
        new_patterns.append("de stungna runornas väg in i Mälardalen")
    if bro and _sig((bro.get("all") or {}).get("q")) and (bro.get("halves") or {}).get("replicated"):
        new_patterns.append("själsbönen på brostenar")
    if cands:
        new_patterns.append(f"{len(cands)} möjliga okända ristare")
    paras.append(
        "**Sammantaget** ger statistiken tre slags bidrag: stöd för etablerade tolkningar (lokala ristare, stilkronologin), "
        "verktyg för att föreslå ristare och hitta okända, och nya mönster att pröva"
        + (" – " + ", ".join(new_patterns) if new_patterns else "") + ". Resultaten är förslag för runologisk granskning, "
        "inte färdiga slutsatser; reservationerna står under varje fråga.")
    return {"paragraphs": paras, "next_steps": steps}
