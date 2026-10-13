"""Ämnen för artiklarna: de mönster som R-analyserna har hittat och som håller, och ett utkast kring ett av dem.

Kandidaterna är korpusmönstren (src/r_findings.py) som är *mönster att pröva* eller *bekräftar*, har en hypotes och håller i
båda halvorna av korpusen (nya mönster får vara med också när analysen saknar ett prov i halvor). Utkastet följer bloggens mall (rubrik, ingress, "Kort sagt", vad vi
ser med ett diagram när datan finns, "Så säkra är vi", hypotesen, hur den kan prövas, förbehåll, se själv och källor) och
är tänkt att skrivas om med egna ord: siffrorna och resonemangen kommer från appen, berättelsen från skribenten.
"""
from __future__ import annotations

import re

RANK = {"mönster att pröva": 0, "bekräftar": 1}
# Method checks rather than findings about the runestones; they do not make a post of the month
SKIP = {("Attribuering", "model"), ("Datering", "seriation"), ("Språk", "spelling")}
# The change analysis's features under the pattern map's names (src/pattern_map.py), for the link to the map
def see_maps(p: dict, res: dict, map_keys: frozenset = frozenset()) -> tuple[str | None, str | None]:
    """The map tool's view that belongs with the topic: (pattern on the map, "kluster" | "tid" | None), so that the article
    can show the picture instead of linking to the map."""
    k, key, hc = kind(p, res), p.get("key") or "", _hotspot(res, p.get("key") or "")
    pm = (hc[0]["key"] if hc else MAP_ALIAS.get(key, key)) if (hc or k in ("time", "regional")) else None
    if not pm or pm not in map_keys:
        return None, None
    return pm, "kluster" if hc else "tid" if k == "time" else None


MAP_ALIAS = {"cross": "kors", "ai_alla": "monoftong", "ai_sten": "monoftong"}
STYLE_YEARS = {"RAK": 1000, "Fp": 1030, "Pr1": 1030, "Pr2": 1035, "Pr3": 1065, "Pr4": 1085, "Pr5": 1115}

WORDS = {
    "sv": {
        "short": "Kort sagt", "see": "Vad vi ser", "sure": "Så säkra är vi", "hyp": "Vår hypotes", "test": "Så kan den prövas",
        "caveats": "Förbehåll", "yourself": "Se själv", "sources": "Källor och data",
        "hyp_bullet": "Vår hypotes", "test_bullet": "Den kan prövas", "both": "Mönstret syns i två oberoende halvor av "
        "materialet, inte bara i några enskilda socknar.", "not_both": "Mönstret syns inte i båda halvorna av materialet, "
        "så det kan bero på några enskilda socknar.",
        "many": "**Många test på en gång.** Den som prövar många mönster hittar till slut något av en ren slump, så vi "
                "prövade det här tillsammans med appens andra mönster och tog hänsyn till det. {plain} ({sig}).",
        "halves": "**Två oberoende halvor.** Vi delade stenarna i två grupper, socken för socken, så att båda grupperna fick "
                  "stenar från samma trakter och ungefär samma tid, och gjorde om hela analysen i varje grupp för sig. "
                  "Mönstret syns i båda. Hade det bara funnits i den ena hade det kunnat bero på några enskilda socknar "
                  "eller ristare.",
        "draws": "**Osäkra årtal.** Stilgruppernas dateringar är ungefärliga; vi räknade om med årtal lottade inom varje "
                 "stilgrupps intervall, och {ok} av {n} omräkningar gav samma resultat.",
        "model": "**Samma ristare, samma trakt.** Modellen jämför stenar av samma ristare och i samma område, så att mönstret "
                 "inte bara är en enskild ristares vana eller en skillnad mellan landskap.",
        "cluster": "**Inte slumpen.** Vi lät datorn fördela mönstret slumpvis över stenarna {nsim} gånger och jämförde: ett "
                   "lika tydligt kluster uppstod nästan aldrig (Kulldorffs scanstatistik).",
        "moran": "**Mönstret samlas.** Stenar med mönstret står oftare nära varandra än slumpen ger. Måttet för det, Morans I, "
                 "är {i}, där 0 betyder ingen samling alls.",
        "rewrite": "*Utkast: siffrorna och resonemangen kommer från Vitkis analyser. Skriv om texten med egna ord, börja "
                   "gärna med en inskrift som krok och lägg till vad som är nytt jämfört med tidigare forskning.*",
        "rundata": "Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk, Uppsala universitet. Open "
                   "Database License.",
        "around": "omkring", "stones": "stenar", "in": "Inom klustret", "out": "Övriga stenar",
        "chart_time": "Andel runstenar med mönstret ({label}), efter stilgrupp",
        "chart_prov": "Andel runstenar med mönstret ({label}) omkring 1050, efter landskap",
        "chart_cluster": "Andel runstenar med mönstret ({label}) inom klustret och i resten av landet",
        "source_line": "Källa: Vitkis korpusanalys av Samnordisk runtextdatabas.",
    },
    "en": {
        "short": "In short", "see": "What we see", "sure": "How sure we are", "hyp": "Our hypothesis",
        "test": "How it can be tested", "caveats": "Caveats", "yourself": "See for yourself", "sources": "Sources and data",
        "hyp_bullet": "Our hypothesis", "test_bullet": "It can be tested", "both": "The pattern holds in both halves of the "
        "corpus, split parish by parish.", "not_both": "The pattern has not been tested in both halves, or holds in only one.",
        "many": "**Many tests at once.** Whoever tests many patterns will in the end find something by pure chance, so we "
                "tested this one together with the app's other patterns and took that into account. {plain} ({sig}).",
        "halves": "**Two independent halves.** We split the stones into two groups, parish by parish, so that both groups "
                  "got stones from the same districts and about the same time, and redid the whole analysis in each group "
                  "on its own. The pattern appears in both. Had it been found in only one, it could have been down to a "
                  "few particular parishes or carvers.",
        "draws": "**Uncertain years.** The style groups' dates are approximate; we recalculated with years drawn at random "
                 "within each group's interval, and {ok} of {n} recalculations gave the same result.",
        "model": "**Same carver, same area.** The model compares stones by the same carver and in the same area, so the "
                 "pattern is not just one carver's habit or a difference between provinces.",
        "cluster": "**Not chance.** We let the computer spread the pattern at random over the stones {nsim} times and "
                   "compared: a cluster this clear almost never arose (Kulldorff's scan statistic).",
        "moran": "**The pattern gathers.** Stones with the pattern stand near each other more often than chance would give. "
                 "The measure for that, Moran's I, is {i}, where 0 means no gathering at all.",
        "rewrite": "*Draft: the numbers and the reasoning come from Vitki's analyses. Rewrite the text in your own words, "
                   "perhaps opening with an inscription as a hook, and add what is new compared with earlier research.*",
        "rundata": "Scandinavian Runic-text Data Base (Rundata), Department of Scandinavian Languages, Uppsala "
                   "University. Open Database License.",
        "around": "around", "stones": "stones", "in": "Within the cluster", "out": "Other stones",
        "chart_time": "Share of runestones with the pattern ({label}), by style group",
        "chart_prov": "Share of runestones with the pattern ({label}) around 1050, by province",
        "chart_cluster": "Share of runestones with the pattern ({label}) within the cluster and in the rest of the country",
        "source_line": "Source: Vitki's corpus analysis of the Scandinavian Runic-text Data Base.",
    },
}
REFS = {
    "time": "Gräslund, A.-S. 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. In: M. Stoklund et al. "
            "(eds), *Runes and their Secrets: Studies in Runology*. Copenhagen: Museum Tusculanum Press, pp. 117–139.",
    "holm": "Holm, S. 1979. A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics* 6, "
            "pp. 65–70.",
    "bh": "Benjamini, Y. & Hochberg, Y. 1995. Controlling the false discovery rate. *Journal of the Royal Statistical "
          "Society B* 57, pp. 289–300.",
    "kulldorff": "Kulldorff, M. 1997. A spatial scan statistic. *Communications in Statistics – Theory and Methods* 26, "
                 "pp. 1481–1496.",
}


def topic_key(p: dict) -> str:
    return f"{p.get('topic')}|{p.get('key')}"


def first_sentence(text: str) -> str:
    s = re.split(r"(?<=[a-zåäö0-9)])\.\s", text or "", maxsplit=1)[0]
    s = re.split(r"\s\(|:\s", s, maxsplit=1)[0]
    return s.rstrip(".") if len(s) <= 110 else s[:107].rsplit(" ", 1)[0] + " …"


def main_clause(text: str) -> str:
    """The first sentence's main clause, without parentheses and what follows a colon: a whole sentence for the lead."""
    s = re.split(r"(?<=[a-zåäö0-9)])\.\s", (text or "").strip(), maxsplit=1)[0]
    s = re.sub(r"\s*\([^()]*\)", "", s)
    head, _, tail = s.partition(": ")
    # "Prepositionen at: landskapen skiljer sig" – keep what follows the colon when the head is no sentence of its own
    if len(head.split()) < 5 and tail:
        head = f"{head}: {re.split(r',\s|;\s', tail, maxsplit=1)[0]}"
    return head.strip().rstrip(".")


def sharpened(hypothesis: str) -> str:
    """The hypothesis's first sentence as a statement for the quote: whole, and without "Vi föreslår att"."""
    s = re.split(r"(?<=[a-zåäö0-9)])\.\s", (hypothesis or "").strip(), maxsplit=1)[0].rstrip(".")
    s = re.sub(r"^(Vi föreslår att|We suggest that|We propose that)\s+", "", s)
    return s[:1].upper() + s[1:] if s else s


def _dot(t: str) -> str:
    t = t.strip()
    return t if t.endswith((".", "!", "?", "…")) else t + "."


def _feature(res: dict, key: str) -> dict | None:
    return next((f for f in (res.get("change") or {}).get("features") or [] if f.get("key") == key), None)


def _hotspot(res: dict, key: str) -> tuple[dict, dict] | None:
    """The hotspot pattern and cluster behind a key such as hotspot_r_for_R_U 768."""
    m = re.match(r"^hotspot_(.+)_([^_]+ \d+[A-Z]?)$", key or "")
    if not m:
        return None
    p = next((x for x in (res.get("hotspots") or {}).get("patterns") or [] if x.get("key") == m.group(1)), None)
    c = next((c for c in (p or {}).get("clusters") or [] if c.get("center") == m.group(2)), None)
    return (p, c) if p and c else None


def has_chart(p: dict, res: dict) -> bool:
    return bool(chart(p, res, "sv"))


def chart(p: dict, res: dict, lang: str = "sv", label: str | None = None, provinces: dict | None = None) -> str:
    """A :::chart block (components/BlogBody.tsx) for the pattern, or "" when there are no numbers to draw."""
    w, topic, key = WORDS[lang], p.get("topic"), p.get("key") or ""
    pct = (lambda v: f"{round(v * 100)}")
    num = (lambda n: f"{n} {w['stones']}")
    if topic == "Förändring" and (f := _feature(res, key)) and (rows := (f.get("time") or {}).get("by_style")):
        peak = max(rows, key=lambda r: r["share"])["style"]
        lines = [f"{'+' if r['style'] == peak else ''}{r['style']}, {w['around']} {STYLE_YEARS.get(r['style'], r.get('year'))} | "
                 f"{pct(r['share'])} | {num(r['n'])}" for r in rows if r.get("n")]
        return "\n".join([f":::chart {w['chart_time'].format(label=label or f.get('label', key))}", *lines, w["source_line"], ":::"])
    if topic == "Regional skillnad" and (f := _feature(res, key)):
        rows = [r for r in ((f.get("provinces") or {}).get("rows") or []) if (r.get("n_mid") or 0) >= 10 and r.get("share1050") is not None]
        if len(rows) >= 2:
            rows.sort(key=lambda r: -r["share1050"])
            names = provinces or {}
            lines = [f"{'+' if i == 0 else ''}{names.get(r['province'], r['province'])} | {pct(r['share1050'])} | {num(r['n_mid'])}"
                     for i, r in enumerate(rows)]
            return "\n".join([f":::chart {w['chart_prov'].format(label=label or f.get('label', key))}", *lines, w["source_line"], ":::"])
    if (hc := _hotspot(res, key)):
        _, c = hc
        return "\n".join([f":::chart {w['chart_cluster'].format(label=label or key)}",
                          f"+{w['in']} ({c['center']}, {c['radius_km']} km) | {pct(c['rate_in'])} | {num(c['n'])}",
                          f"{w['out']} | {pct(c['rate_out'])}", w["source_line"], ":::"])
    return ""


def candidates(patterns: list[dict], res: dict, used: set[str] = frozenset()) -> list[dict]:
    """Ämnena att välja bland: nya mönster som håller i båda halvorna först, sedan bekräftade, högst ett par per område."""
    out, per_topic = [], {}
    # Confirmed patterns must hold in both halves; new ones too, unless the analysis has no test in halves (None)
    pool = [p for p in patterns if p.get("status") in RANK and p.get("hypothesis") and (p.get("topic"), p.get("key")) not in SKIP
            and (p.get("replicated") is True or (p["status"] == "mönster att pröva" and p.get("replicated") is None))]
    # A feature that is part of a broader one (stungen e within stungna runor) gives way to it
    from src.language_profile import REDUNDANT
    keys = {p.get("key") for p in pool}
    covered = {k for parent, kids in REDUNDANT.items() if parent in keys for k in kids}
    pool = [p for p in pool if p.get("key") not in covered]
    pool.sort(key=lambda p: (topic_key(p) in used, RANK[p["status"]], not p.get("replicated"), not has_chart(p, res)))
    for p in pool:
        t = p.get("topic") or ""
        if per_topic.get(t, 0) >= 4:
            continue
        per_topic[t] = per_topic.get(t, 0) + 1
        out.append({"key": topic_key(p), "topic": t, "status": p["status"], "replicated": bool(p.get("replicated")),
                    "title": first_sentence(p["text"]), "text": p["text"], "hypothesis": first_sentence(p["hypothesis"]),
                    "significance": (p.get("significance") or {}).get("label"), "chart": has_chart(p, res),
                    "used": topic_key(p) in used})
    return out[:14]


# ---- the draft, in the form of the published post "Bönen tystnade – men korset stod kvar" --------------------------
# A quote from a stone with the pattern as the hook, the stone's photo, "Kort sagt", the pattern with numbers and a
# chart, a figure from the R analyses (the map tool's maps where they exist), "Så säkra är vi", the hypothesis with what
# is new, a first test computed from the data with a sharpened hypothesis, how it can be tested further, caveats, see for
# yourself and sources. Only what needs knowledge of earlier research is left for the writer, marked in italics.

REFS.update({
    "getis": "Getis, A. & Ord, J. K. 1992. The analysis of spatial association by use of distance statistics. "
             "*Geographical Analysis* 24, pp. 189–206.",
})

T = {
    "sv": {
        "note": "*Utkast efter mallen från ”Bönen tystnade – men korset stod kvar”: siffrorna, diagrammen och kartan kommer "
                "från Vitkis analyser. Skriv om med egna ord, gör rubriken till en berättelse och fyll i det som är markerat.*",
        "quote_lead": "Så står det – i Rundatas normalisering – på runstenen {signum} vid {place} i {province}",
        "dated": ", ristad någon gång mellan {a} och {b} att döma av ornamentiken",
        "carver": " och tillskriven ristaren {carver}",
        "follow": "Men när vi lät statistiken följa {label} genom hela materialet såg vi {teaser}.",
        "teaser": {"peak": "att det kom och gick", "rises": "att det bredde ut sig", "falls": "att det försvann",
                   "regional": "att landskapen skiljer sig", "cluster": "att det samlas på en plats",
                   "generic": "ett mönster som håller"},
        "title": {"peak": "{Label} kommer och går", "rises": "{Label} breder ut sig", "falls": "{Label} försvinner",
                  "regional": "{Label} – en skillnad mellan landskapen", "cluster": "{Label} – ett kluster i {region}",
                  "water": "Runstenarna vid vikingatidens stränder", "anonymous": "Okända ristare träder fram",
                  "remains": "Runstenarna vid de dödas platser"},
        "short": "Kort sagt", "sure": "Så säkra är vi", "hyp": "Vår hypotes", "first": "En första prövning",
        "further": "Så kan hypotesen prövas vidare", "caveats": "Förbehåll", "yourself": "Se själv", "sources": "Källor och data",
        "sure_intro": "Ett mönster i ett stort material kan uppstå av en slump, eller av att materialet är skevt. Därför har "
                      "vi prövat det på flera sätt:",
        "kb_robust": {"time": "Förändringen syns också när vi jämför stenar av samma ristare och i samma trakt.",
                      "regional": "Skillnaden finns kvar vid samma tid och med samma ristare.",
                      "cluster": "Klustret klarar en prövning mot slumpen och syns i två oberoende halvor av materialet.",
                      "generic": "Mönstret klarar justeringen för många test."},
        "kb_hyp": "Vår hypotes: {hyp} Den kan prövas.",
        "h1": {"time": "{Label} genom tiden", "regional": "{Label} landskap för landskap", "cluster": "Ett kluster i {region}",
               "remains": "Nära de dödas platser", "water": "Vid vikingatidens stränder", "anonymous": "Grupper utan namn",
               "generic": "Vad vi ser"},
        "h2": {"cluster": "Kartan: var mönstret samlas", "time": "Kartan: var draget är vanligast",
               "regional": "Kartan: var draget är vanligast", "remains": "Runstenarna och fornlämningarna",
               "water": "Kartan: stenarna och vattnet", "anonymous": "Kartan: grupperna", "generic": "Figuren"},
        "data": {"time": "Vi gick igenom de {n} runstenar i Sverige där {label} kan avgöras i Samnordisk runtextdatabas. "
                         "{n_dated} av dem kan dateras ungefär genom sin ornamentik: runstenskonsten bytte stil under "
                         "1000-talet, och stilarna har ordnats i en följd från RAK omkring år 1000 till Pr5 i början av 1100-talet.",
                 "regional": "Vi gick igenom de {n} runstenar i Sverige där {label} kan avgöras och jämförde landskapen vid "
                             "samma tid, omkring 1050, och med ristaren konstant.",
                 "cluster": "Vi lät R söka efter platser där {label} är ovanligt vanligt bland de {n} stenar där mönstret kan "
                            "avgöras: alla cirklar som rymmer högst en tiondel av stenarna prövades mot slumpen (Kulldorffs "
                            "scanstatistik), och varje sten fick ett mått på om grannarna har mönstret oftare än landet i "
                            "stort (Getis-Ord Gi*).",
                 "generic": ""},
        "model_peak": "Vår modell, som tar hänsyn till vem som ristade stenen och var den står, lägger toppen omkring {y} "
                      "(troligen mellan {lo} och {hi}) och visar en förändring från omkring {a} till {b} procent.",
        "model_trend": "Med vem som ristade stenen och var den står konstant går andelen från omkring {a} procent omkring {y1} "
                       "till {b} procent omkring {y2}.",
        "cluster_numbers": "Inom {r} km från {center} har {rin} procent av de {n} stenarna mönstret, mot {rout} procent i "
                           "resten av landet – {rr} gånger så vanligt.",
        "fig_text": {"cluster": "Kartan visar andelen stenar med mönstret per område, de stenar som ligger i heta och kalla "
                                "områden och klustret som ring. Den är samma bild som i kartverktyget under ”Kluster”.",
                     "time": "Kartan visar var draget är vanligast enligt den rumsliga modellen, med ristaren som slumpeffekt.",
                     "regional": "Kartan visar var draget är vanligast enligt den rumsliga modellen, med ristaren som slumpeffekt.",
                     "generic": ""},
        "hyp_known": "*Skriv här vad forskningen redan vet eller har föreslagit om {label}.* Det vi tillför är mätningen: "
                     "{add}. Det kräver en förklaring.",
        "add": {"time": "att förändringen går att följa i hela materialet med ristare och trakt konstanta",
                "regional": "att skillnaden mellan landskapen håller vid samma tid och med samma ristare",
                "cluster": "att mönstret samlas på en plats som går att avgränsa statistiskt och som håller i båda halvorna",
                "generic": "att mönstret håller när det prövas statistiskt i hela materialet"},
        "first_todo": "*Gör en första prövning av hypotesen och redovisa resultatet ärligt, även om det talar emot den. "
                      "Förslag: {test}*",
        "limit": {"time": "Prövningen har en gräns: stilgrupperna delar in tiden i steg om ungefär tjugofem år, så en "
                          "skillnad på något decennium syns inte.",
                  "cluster": "Prövningen har en gräns: många stenar saknar en säker ristare i Rundata.",
                  "regional": "Prövningen har en gräns: i landskap med få ristare kan en enda ristares vana väga tungt.",
                  "generic": ""},
        "further_items": {
            "time": ["**Finare datering.** Om ristarnas verksamhet dateras finare, genom samarbeten och kedjor av lärare och "
                     "elever, går det att se om förändringen sker samtidigt överallt eller sprider sig.",
                     "**Andra landskap.** Följ draget där stilgrupperna är osäkrare och stenarna färre, och jämför med Uppland."],
            "regional": ["**Ristarna.** Hur mycket av skillnaden bärs av ett fåtal produktiva ristare? Pröva utan dem.",
                         "**Tiden.** Följ skillnaden över tid: krymper den eller växer den mot slutet av runstenstiden?"],
            "cluster": ["**Grannstenarna.** Jämför klustrets stenar med stenarna strax utanför: slutar mönstret vid en "
                        "bygdegräns, ett härad eller en vattenled?",
                        "**Ristarna.** Pröva igen när fler stenar får säkra attribueringar: följer mönstret en verkstad?"],
            "generic": ["**Fler data.** Pröva mönstret när fler stenar har säkra uppgifter.",
                        "**Andra källor.** Ställ mönstret mot arkeologin och ortnamnen i samma trakter."]},
        "direct": "**Det direkta provet.** {test}",
        "general_caveats": {"time": "Dateringen bygger på ornamentiken och är ungefärlig, och stilgrupperna är utarbetade för "
                                    "stenarna i Uppland och Södermanland.",
                            "cluster": "Flyttade stenar räknas inte, men alla flyttningar finns inte noterade i Rundata.",
                            "regional": "Landskap med färre än tio daterade stenar från mittperioden redovisas inte.",
                            "generic": ""},
        "general_caveat2": "Ett samband är inte en orsak; hypotesen förklarar mönstret, men andra förklaringar är möjliga.",
        "photos": "Foton: Wikimedia Commons, med fotograf och licens i bildtexterna. Figurer: Vitkis korpusanalys i R.",
        "rundata": WORDS["sv"]["rundata"],
        "stones": "stenar",
    },
}
T["en"] = {
    "note": "*Draft in the form of “The prayer fell silent – but the cross remained”: the numbers, charts and map come from "
            "Vitki's analyses. Rewrite in your own words, turn the title into a story and fill in what is marked.*",
    "quote_lead": "So it reads – in Rundata's normalisation – on the runestone {signum} at {place} in {province}",
    "dated": ", carved some time between {a} and {b} to judge by its ornament",
    "carver": " and attributed to the carver {carver}",
    "follow": "But when we let the statistics follow {label} through the whole material we saw {teaser}.",
    "teaser": {"peak": "that it came and went", "rises": "that it spread", "falls": "that it disappeared",
               "regional": "that the provinces differ", "cluster": "that it gathers in one place", "generic": "a pattern that holds"},
    "title": {"peak": "{Label} comes and goes", "rises": "{Label} spreads", "falls": "{Label} disappears",
              "regional": "{Label} – a difference between the provinces", "cluster": "{Label} – a cluster in {region}",
              "water": "The runestones by the Viking Age shores", "anonymous": "Unknown carvers step forward",
              "remains": "The runestones by the places of the dead"},
    "short": "In short", "sure": "How sure we are", "hyp": "Our hypothesis", "first": "A first test",
    "further": "How the hypothesis can be tested further", "caveats": "Caveats", "yourself": "See for yourself",
    "sources": "Sources and data",
    "sure_intro": "A pattern in a large material can arise by chance, or because the material is skewed. So we have tested "
                  "it in several ways:",
    "kb_robust": {"time": "The change shows also when we compare stones by the same carver and in the same area.",
                  "regional": "The difference remains at the same time and with the same carver.",
                  "cluster": "The cluster survives a test against chance and shows in two independent halves of the material.",
                  "generic": "The pattern survives the adjustment for many tests."},
    "kb_hyp": "Our hypothesis: {hyp} It can be tested.",
    "h1": {"time": "{Label} through time", "regional": "{Label} province by province", "cluster": "A cluster in {region}",
           "remains": "Near the places of the dead", "water": "By the Viking Age shores", "anonymous": "Groups without a name",
           "generic": "What we see"},
    "h2": {"cluster": "The map: where the pattern gathers", "time": "The map: where the feature is most common",
           "regional": "The map: where the feature is most common", "remains": "The runestones and the ancient monuments",
           "water": "The map: the stones and the water", "anonymous": "The map: the groups", "generic": "The figure"},
    "data": {"time": "We went through the {n} runestones in Sweden where {label} can be determined in the Scandinavian "
                     "Runic-text Data Base. {n_dated} of them can be roughly dated by their ornament: runestone art changed "
                     "style during the eleventh century, and the styles have been put in order from RAK around the year 1000 "
                     "to Pr5 in the early 1100s.",
             "regional": "We went through the {n} runestones in Sweden where {label} can be determined and compared the "
                         "provinces at the same time, around 1050, and with the carver held constant.",
             "cluster": "We let R search for places where {label} is unusually common among the {n} stones where the pattern "
                        "can be determined: every circle holding at most a tenth of the stones was tested against chance "
                        "(Kulldorff's scan statistic), and every stone got a measure of whether its neighbours have the "
                        "pattern more often than the country as a whole (Getis-Ord Gi*).",
             "generic": ""},
    "model_peak": "Our model, which takes into account who carved the stone and where it stands, puts the peak around {y} "
                  "(probably between {lo} and {hi}) and shows a change from about {a} to {b} per cent.",
    "model_trend": "With who carved the stone and where it stands held constant, the share goes from about {a} per cent around "
                   "{y1} to {b} per cent around {y2}.",
    "cluster_numbers": "Within {r} km of {center}, {rin} per cent of the {n} stones have the pattern, against {rout} per cent in "
                       "the rest of the country – {rr} times as common.",
    "fig_text": {"cluster": "The map shows the share of stones with the pattern per area, the stones in hot and cold areas and "
                            "the cluster as a ring. It is the same picture as in the map tool under “Clusters”.",
                 "time": "The map shows where the feature is most common according to the spatial model, with the carver as "
                         "a random effect.",
                 "regional": "The map shows where the feature is most common according to the spatial model, with the carver "
                             "as a random effect.",
                 "generic": ""},
    "hyp_known": "*Write here what research already knows or has suggested about {label}.* What we add is the measurement: "
                 "{add}. That calls for an explanation.",
    "add": {"time": "the change can be followed through the whole material with carver and area held constant",
            "regional": "the difference between the provinces holds at the same time and with the same carver",
            "cluster": "the pattern gathers in a place that can be delimited statistically and holds in both halves",
            "generic": "the pattern holds when tested statistically on the whole material"},
    "first_todo": "*Make a first test of the hypothesis and report the result honestly, even if it speaks against it. "
                  "Suggestion: {test}*",
    "limit": {"time": "The test has a limit: the style groups divide time into steps of about twenty-five years, so a "
                      "difference of a decade or so does not show.",
              "cluster": "The test has a limit: many stones lack a certain carver in Rundata.",
              "regional": "The test has a limit: in provinces with few carvers a single carver's habit can weigh heavily.",
              "generic": ""},
    "further_items": {
        "time": ["**Finer dating.** If the carvers' careers are dated more finely, through collaborations and chains of "
                 "masters and pupils, it can be seen whether the change happens at the same time everywhere or spreads.",
                 "**Other provinces.** Follow the feature where the style groups are less certain and the stones fewer, and "
                 "compare with Uppland."],
        "regional": ["**The carvers.** How much of the difference rests on a few productive carvers? Test without them.",
                     "**Time.** Follow the difference over time: does it shrink or grow towards the end of the runestone period?"],
        "cluster": ["**The neighbouring stones.** Compare the cluster's stones with those just outside: does the pattern stop at "
                    "a district boundary, a hundred or a waterway?",
                    "**The carvers.** Test again when more stones get certain attributions: does the pattern follow a workshop?"],
        "generic": ["**More data.** Test the pattern when more stones have certain records.",
                    "**Other sources.** Set the pattern against the archaeology and the place names in the same districts."]},
    "direct": "**The direct test.** {test}",
    "general_caveats": {"time": "The dating rests on the ornament and is approximate, and the style groups were worked out "
                                "for the stones of Uppland and Södermanland.",
                        "cluster": "Moved stones are left out, but not every move is recorded in Rundata.",
                        "regional": "Provinces with fewer than ten dated stones from the middle period are not reported.",
                        "generic": ""},
    "general_caveat2": "An association is not a cause; the hypothesis explains the pattern, but other explanations are possible.",
    "photos": "Photos: Wikimedia Commons, with photographer and licence in the captions. Figures: Vitki's corpus analysis in R.",
    "rundata": WORDS["en"]["rundata"],
    "stones": "stones",
}


def plain_significance(sig: dict | None, lang: str) -> str:
    """What the adjusted p- or q-value means, in plain words and correctly: for Benjamini–Hochberg the expected share of
    chance findings among patterns this strong; otherwise how seldom a pattern this clear would arise by chance."""
    v = (sig or {}).get("value")
    if v is None:
        return ""
    sv = lang == "sv"
    if "Benjamini" in ((sig or {}).get("test") or ""):
        if v < 0.001:
            return ("Bland alla mönster som är minst så här tydliga väntas färre än ett av tusen vara slumpfynd." if sv else
                    "Among all patterns at least this strong, fewer than one in a thousand are expected to be chance findings.")
        pct = f"{v * 100:.1f}".rstrip("0").rstrip(".")
        pct = pct.replace(".", ",") if sv else pct
        return (f"Bland alla mönster som är minst så här tydliga väntas högst omkring {pct} procent vara slumpfynd." if sv else
                f"Among all patterns at least this strong, at most about {pct} per cent are expected to be chance findings.")
    if v < 0.001:
        return ("Ett så tydligt mönster skulle uppstå av en ren slump i mindre än ett fall av tusen." if sv else
                "A pattern this clear would arise by pure chance in fewer than one case in a thousand.")
    n = 1 / v
    n = int(round(n, -1)) if n >= 20 else int(round(n))
    return (f"Ett så tydligt mönster skulle uppstå av en ren slump i ungefär ett fall av {n}." if sv else
            f"A pattern this clear would arise by pure chance in about one case in {n}.")


# Statistical restatements in an analysis's note; "Så säkra är vi" explains them in plain words, so the caveats leave
# them out and keep what limits the conclusion
STATS_ONLY = re.compile(r"Morans I|Moran's I|Benjamini|Holm|simuleringar|simulations|Klarar justeringen|survives the adjustment|"
                        r"\(q [<0-9]|\bq [<0-9]|\bp [<0-9]", re.I)


def kind(p: dict, res: dict) -> str:
    topic, key = p.get("topic"), p.get("key") or ""
    if topic == "Förändring" and _feature(res, key):
        return "time"
    if topic == "Regional skillnad" and _feature(res, key):
        return "regional"
    if _hotspot(res, key):
        return "cluster"
    for prefix, k in (("anonymous", "anonymous"), ("remains_", "remains"), ("water", "water")):
        if key.startswith(prefix):
            return k
    return "generic"


def figure_for(p: dict, res: dict) -> str | None:
    """The R figure that belongs with the topic: the map tool's map of the pattern when there is one."""
    k, key = kind(p, res), p.get("key") or ""
    figs = {n for mod in res.values() if isinstance(mod, dict) for n in ((mod.get("figures") or {}).values()
                                                                        if isinstance(mod.get("figures"), dict) else [])}
    want = {"cluster": f"hotspot_{(_hotspot(res, key) or ({},))[0].get('key')}.png", "time": "forandring_karta.png",
            "regional": "forandring_karta.png", "remains": "lamningar_narhet.png", "water": "geografi_vatten.png",
            "anonymous": "okanda_ristare.png"}.get(k)
    if k == "time" and f"hotspot_{MAP_ALIAS.get(key, key)}.png" in figs:
        want = f"hotspot_{MAP_ALIAS.get(key, key)}.png"
    if key.startswith("scan_"):
        want = "landskap_genomsokning.png"
    return want if want in figs else None


def _num(v: float, lang: str, digits: int = 0) -> str:
    s = f"{v:.{digits}f}"
    return s.replace(".", ",") if lang == "sv" else s


def first_test(p: dict, res: dict, lang: str, mix: dict | None = None, provinces: dict | None = None,
               hyp_text: str | None = None) -> tuple[str, str] | None:
    """A first test computed from the data: (text, sharpened hypothesis), or None when the writer has to make it."""
    k, key, sv = kind(p, res), p.get("key") or "", lang == "sv"
    names = provinces or {}
    hyp = sharpened(hyp_text if hyp_text is not None else p.get("hypothesis") or "")
    if k == "cluster" and mix and mix.get("n"):
        share = mix["top_n"] / mix["with_carver"] if mix.get("with_carver") else 0
        if sv:
            text = (f"Om klustret är en enda ristares vana borde stenarna med mönstret följa den ristaren. Av de {mix['n']} "
                    f"stenarna med mönstret inne i klustret har {mix['with_carver']} en säker ristare i Rundata, fördelade på "
                    f"{mix['carvers']} ristare" + (f"; den vanligaste, {mix['top']}, står för {mix['top_n']}." if mix.get("top") else "."))
            if mix["carvers"] >= 3 and share < 0.35:
                verdict = ("Mönstret delas alltså av flera ristare – det talar för en lokal sed i bygden snarare än en "
                           "enskild ristares vana.")
                sharp = "Mönstret är en sed i bygden, som flera ristare följde."
            elif mix["carvers"] >= 3 and share < 0.65:
                verdict = ("En ristare står för en stor del, men flera andra följer samma mönster – det talar för en "
                           "verkstad eller en krets kring en ristare, vars vana spreds i bygden.")
                sharp = "Mönstret började hos en ristare och spreds till andra i samma bygd."
            else:
                verdict = "En ristare dominerar – det talar för en ristares eller verkstads vana snarare än en bygds sed."
                sharp = "Mönstret är en verkstads eller en ristares kännetecken."
        else:
            text = (f"If the cluster is one carver's habit, the stones with the pattern should follow that carver. Of the "
                    f"{mix['n']} stones with the pattern inside the cluster, {mix['with_carver']} have a certain carver in "
                    f"Rundata, spread over {mix['carvers']} carvers" + (f"; the most common, {mix['top']}, accounts for "
                                                                        f"{mix['top_n']}." if mix.get("top") else "."))
            if mix["carvers"] >= 3 and share < 0.35:
                verdict = ("The pattern is thus shared by several carvers – which points to a local custom in the district "
                           "rather than one carver's habit.")
                sharp = "The pattern is a custom of the district, followed by several carvers."
            elif mix["carvers"] >= 3 and share < 0.65:
                verdict = ("One carver accounts for a large part, but several others follow the same pattern – which points to "
                           "a workshop or a circle around one carver, whose habit spread in the district.")
                sharp = "The pattern began with one carver and spread to others in the same district."
            else:
                verdict = "One carver dominates – which points to a carver's or workshop's habit rather than a district's custom."
                sharp = "The pattern is the mark of a workshop or a carver."
        return text + " " + verdict, sharp
    if k in ("time", "regional"):
        f = _feature(res, key) or {}
        rows = [r for r in ((f.get("provinces") or {}).get("rows") or []) if (r.get("n_mid") or 0) >= 10]
        if k == "time" and len([r for r in rows if r.get("cross_year")]) >= 2:
            rs = [r for r in rows if r.get("cross_year")][:4]
            parts = [f"{names.get(r['province'], r['province'])} omkring {r['cross_year']} ({r['cross_lo']}–{r['cross_hi']})" if sv else
                     f"{names.get(r['province'], r['province'])} around {r['cross_year']} ({r['cross_lo']}–{r['cross_hi']})" for r in rs]
            overlap = max(r["cross_lo"] for r in rs) <= min(r["cross_hi"] for r in rs)
            if sv:
                text = ("Om förändringen spreds från ett centrum borde den slå igenom vid olika tider i olika landskap. "
                        f"Draget passerar hälften av stenarna i {', '.join(parts)}. "
                        + ("Intervallen överlappar: förändringen kan ha skett ungefär samtidigt." if overlap else
                           "Intervallen överlappar inte: förändringen slog igenom vid olika tider i olika landskap."))
            else:
                text = ("If the change spread from a centre, it should take hold at different times in different provinces. "
                        f"The feature passes half of the stones in {', '.join(parts)}. "
                        + ("The intervals overlap: the change may have happened at about the same time." if overlap else
                           "The intervals do not overlap: the change took hold at different times in different provinces."))
            return text, hyp
        if len(rows) >= 2:
            rows = sorted(rows, key=lambda r: -(r.get("share1050") or 0))
            hi_, lo_ = rows[0], rows[-1]
            if sv:
                text = (f"Om skillnaden bara är några få ristares vana borde den försvinna när ristaren hålls konstant. Den gör "
                        f"det inte: omkring 1050 och för en typisk ristare är andelen {round(hi_['share1050'] * 100)} procent i "
                        f"{names.get(hi_['province'], hi_['province'])} ({hi_.get('n_carvers', '–')} ristare) och "
                        f"{round(lo_['share1050'] * 100)} procent i {names.get(lo_['province'], lo_['province'])} "
                        f"({lo_.get('n_carvers', '–')} ristare).")
            else:
                text = (f"If the difference were only a few carvers' habit, it should disappear when the carver is held "
                        f"constant. It does not: around 1050 and for a typical carver the share is {round(hi_['share1050'] * 100)} "
                        f"per cent in {names.get(hi_['province'], hi_['province'])} ({hi_.get('n_carvers', '–')} carvers) and "
                        f"{round(lo_['share1050'] * 100)} per cent in {names.get(lo_['province'], lo_['province'])} "
                        f"({lo_.get('n_carvers', '–')} carvers).")
            return text, hyp
    if k == "remains":
        tests = (res.get("remains") or {}).get("tests") or {}
        tg, cg = tests.get("time_gravfalt") or {}, tests.get("christian_gravfalt") or {}
        per = tg.get("periods") or {}
        if per.get("early") is not None and per.get("late") is not None:
            if sv:
                text = (f"Om gravfälten var släktens minnesplatser borde närheten bestå också när stenarna blir kristna. Före "
                        f"omkring 1050 står {round(per['early'] * 100)} procent av stenarna inom 500 meter från ett gravfält, efter "
                        f"{round(per['late'] * 100)} procent" + (f", och stenar med kristna markörer står där lika ofta som andra "
                                                                f"(oddskvot {_num(cg['or'], lang, 2)})." if cg.get("or") else "."))
            else:
                text = (f"If the grave fields were the family's places of memory, the nearness should remain when the stones "
                        f"become Christian. Before about 1050, {round(per['early'] * 100)} per cent of the stones stand within "
                        f"500 metres of a grave field, after {round(per['late'] * 100)} per cent" + (
                            f", and stones with Christian markers stand there as often as others (odds ratio "
                            f"{_num(cg['or'], lang, 2)})." if cg.get("or") else "."))
            return text, hyp
    return None


def draft(p: dict, res: dict, lang: str, tr=lambda t: t, label: str | None = None, provinces: dict | None = None,
          map_keys: frozenset = frozenset(), example: dict | None = None, figure: str | None = None,
          mix: dict | None = None, see: list[str] | None = None) -> dict:
    """Title, summary and body around one pattern, in one language, in the form of the published post."""
    t, w = T[lang], WORDS[lang]
    sv = lang == "sv"
    text, hyp, test, note = (tr(p.get(x) or "") for x in ("text", "hypothesis", "test", "note"))
    k, key, topic = kind(p, res), p.get("key") or "", p.get("topic")
    lab = (label or first_sentence(text)).strip()
    lab_lc = lab[0].lower() + lab[1:] if lab[:1].isupper() and not lab[1:2].isupper() else lab
    # "r för ʀ" and "o-runan" keep their small letter: a rune's name is not capitalised
    Lab = lab if re.match(r"^[a-zåäöʀ](\s|-)", lab) else lab[0].upper() + lab[1:]
    f = _feature(res, key) if k in ("time", "regional") else None
    tm = (f or {}).get("time") or {}
    hc = _hotspot(res, key)
    names = provinces or {}
    region = names.get(max((hc[1].get("provinces") or {"": 0}).items(), key=lambda x: x[1])[0], "") if hc else ""
    shape = tm.get("shape") if k == "time" else k
    teaser = t["teaser"].get(shape) or t["teaser"].get(k) or t["teaser"]["generic"]
    lead_clause = _dot(main_clause(text))
    tpl = t["title"].get(shape) or t["title"].get(k)
    short_label = re.sub(r"\s*\([^()]*\)", "", Lab).strip()
    title = tpl.format(Label=short_label, region=region) if tpl and (k != "cluster" or region) else first_sentence(text)
    hyp_s = sharpened(hyp) if hyp else ""
    summary = lead_clause + (" " + (("Vår hypotes: " if sv else "Our hypothesis: ") + hyp_s[0].lower() + hyp_s[1:] + ".")
                             if hyp_s else "")
    parts = [t["note"]]

    # The hook: a stone with the pattern, its text and its photo
    if example:
        quote = example["normalization"] if sv else example["translation_en"]
        lead = t["quote_lead"].format(signum=example["signum"], place=example["place"], province=example["province"])
        if example.get("years"):
            lead += t["dated"].format(a=example["years"][0], b=example["years"][1])
        if example.get("carver"):
            lead += t["carver"].format(carver=example["carver"])
        parts += [f"*{quote}*", f"{lead}. {lead_clause} {t['follow'].format(label=lab_lc, teaser=teaser)}",
                  example["picture"] if sv else example["picture_en"]]
    else:
        parts.append(f"{lead_clause} {t['follow'].format(label=lab_lc, teaser=teaser)}")

    # Kort sagt
    third = ""
    if k == "time" and tm.get("first") is not None and tm.get("last") is not None:
        third = (f"Från omkring {round(tm['first'] * 100)} till {round(tm['last'] * 100)} procent av stenarna mellan "
                 f"{tm.get('year_first')} och {tm.get('year_last')}." if sv else
                 f"From about {round(tm['first'] * 100)} to {round(tm['last'] * 100)} per cent of the stones between "
                 f"{tm.get('year_first')} and {tm.get('year_last')}.")
    elif hc:
        c = hc[1]
        third = (f"Inom klustret har {round(c['rate_in'] * 100)} procent av stenarna mönstret, mot {round(c['rate_out'] * 100)} "
                 f"procent i resten av landet." if sv else
                 f"Within the cluster {round(c['rate_in'] * 100)} per cent of the stones have the pattern, against "
                 f"{round(c['rate_out'] * 100)} per cent in the rest of the country.")
    bullets = [lead_clause, t["kb_robust"].get(k, t["kb_robust"]["generic"])] + ([third] if third else [])
    if hyp_s:
        # After the colon the sentence continues in lower case, as in the published post ("Vår hypotes: bönen tystnade …")
        h = _dot(hyp_s[0].lower() + hyp_s[1:] if hyp_s[1:2].islower() else hyp_s)
        bullets.append(t["kb_hyp"].format(hyp=h))
    parts.append(f":::box {t['short']}\n" + "\n".join(f"- {b}" for b in bullets) + "\n:::")

    # The pattern in numbers, with the chart
    parts.append(f"## {t['h1'].get(k, t['h1']['generic']).format(Label=Lab, region=region or ('landet' if sv else 'the country'))}")
    n = (f or {}).get("n") or (hc[0].get("n") if hc else None)
    data = t["data"].get(k, "")
    if data and n:
        parts.append(data.format(n=n, n_dated=tm.get("n", "–"), label=lab_lc))
    c = chart(p, res, lang, label, provinces)
    if c:
        parts.append(c)
    if k == "time" and tm.get("shape") == "peak" and tm.get("peak_year"):
        parts.append(t["model_peak"].format(y=tm["peak_year"], lo=tm.get("peak_lo"), hi=tm.get("peak_hi"),
                                            a=round((tm.get("peak_share") or 0) * 100), b=round((tm.get("trough_share") or 0) * 100)))
    elif k == "time" and tm.get("first") is not None:
        parts.append(t["model_trend"].format(a=round(tm["first"] * 100), b=round(tm["last"] * 100),
                                             y1=tm.get("year_first"), y2=tm.get("year_last")))
    elif hc:
        cc = hc[1]
        parts.append(t["cluster_numbers"].format(r=_num(cc["radius_km"], lang), center=cc["center"], rin=round(cc["rate_in"] * 100),
                                                 n=cc["n"], rout=round(cc["rate_out"] * 100), rr=_num(cc.get("rr") or 0, lang, 1)))
    else:
        parts.append(text)

    # The figure from the R analyses
    if figure:
        parts += [f"## {t['h2'].get(k, t['h2']['generic'])}", figure]
        if t["fig_text"].get(k):
            parts.append(t["fig_text"][k])

    # Så säkra är vi
    sig = (p.get("significance") or {}).get("label") or ""
    sure = [w["many"].format(sig=sig, plain=plain_significance(p.get("significance"), lang).rstrip(".")) if sig else None]
    if f:
        sure.append(w["model"])
        draws = tm.get("draws") or {}
        if draws.get("n"):
            sure.append(w["draws"].format(ok=round(draws.get("share_sig", 0) * draws["n"]), n=draws["n"]))
    if hc:
        sure.append(w["cluster"].format(nsim=(res.get("hotspots") or {}).get("nsim", 999)))
        mi = (hc[0].get("moran") or {}).get("i")
        if mi is not None:
            sure.append(w["moran"].format(i=_num(mi, lang, 2)))
    if p.get("replicated"):
        sure.append(w["halves"])
    parts.append(f":::box {t['sure']}\n{t['sure_intro']}\n\n" + "\n".join(f"- {s}" for s in sure if s) + "\n:::")

    # Vår hypotes
    if hyp:
        parts += [f"## {t['hyp']}", t["hyp_known"].format(label=lab_lc, add=t["add"].get(k, t["add"]["generic"])), hyp]

    # En första prövning, with a sharpened hypothesis
    ft = first_test(p, res, lang, mix, provinces, hyp_text=hyp)
    parts.append(f"## {t['first']}")
    if ft:
        parts += [ft[0], f"> {_dot(ft[1])}"]
        if t["limit"].get(k):
            parts.append(t["limit"][k])
    else:
        parts.append(t["first_todo"].format(test=test or "…"))

    # Så kan hypotesen prövas vidare
    items = ([t["direct"].format(test=test)] if test else []) + t["further_items"].get(k, t["further_items"]["generic"])
    parts += [f"## {t['further']}", "\n".join(f"{i}. {x}" for i, x in enumerate(items, 1))]

    # Förbehåll
    cav = [x.strip() for x in re.split(r"(?<=[.!?])\s+(?=[A-ZÅÄÖ])", note) if x.strip() and not STATS_ONLY.search(x)][:4]
    for extra in (t["general_caveats"].get(k), t["general_caveat2"]):
        if extra:
            cav.append(extra)
    parts += [f"## {t['caveats']}", "\n".join(f"- {_dot(x)}" for x in cav)]

    # Se själv: kartverktygets bild och modellens kurvor i stället för länkar in i appen, som inte finns på den publika
    # webbplatsen (src/blog_maps.py), och var analysen kan göras om
    from src import blog_maps
    parts += [f"## {t['yourself']}", *(see or []), blog_maps.github_note(lang)]

    # Källor och data
    refs = [t["rundata"]]
    if f:
        refs += [REFS["time"], REFS["holm"]]
    if hc:
        refs += [REFS["kulldorff"], REFS["getis"], REFS["bh"]]
    if not f and not hc:
        refs.append(REFS["bh"])
    refs.append(t["photos"])
    parts += [f"## {t['sources']}", "\n".join(f"- {r}" for r in refs)]
    return {"title": title, "summary": summary, "body": "\n\n".join(parts)}
