"""Vad runstenarna berättar om den döde: budskapen i Rundatas engelska översättning, en regel per budskap.

Budskapen räknas per sten (står det på stenen eller inte) och bara på stenar där minst fyra ord av översättningen går
att läsa (översättarens tillägg inom parentes, ordalternativ med snedstreck och namnfragment räknas inte); på övriga
är budskapet okänt (None). Regeln prövar inte att själva minnesformeln är bevarad, så ett fragment med fyra ord får 0
för alla budskap; r/messages.R prövar därför om resultaten håller på stenar med minst tio läsbara ord. Budskapen prövas
i r/messages.R mot landsdel, tid och ristare (METHODS.md avsnitt 1o).

Reglerna är medvetet enkla och öppna: en sten kan bära flera budskap, och 'resa' och 'död borta' gäller resor utanför
Norden (inte inrikes färder; Gotland, Danmark och Hedeby räknas som Norden). En resa kräver ett mål eller en riktning
utanför Norden: 'he travelled' eller 'died on a voyage' utan mål räknas inte. Namnet Ingvarr räknas bara i
tågets egna formler ('with Ingvarr', 'Ingvarr's retinue/troop/men'), inte när en man bara heter Ingvarr. Jerusalem,
Jordan, Italien och Langobardernas land räknas som öst: inskrifterna själva säger att vägen dit gick österut
(Sö 65, Sö Fv1954;22, U 605). Facit: handkodningen av de 55 västerinskrifterna (utdata/brittiska/hemma_kodning.csv)
och ett handkodat urval av österfärder (data/messages_facit_ost.csv); scripts/check_messages.py jämför reglerna med
båda och skriver överensstämmelsen till data/messages_check.json (som sidan Budskap visar).
"""
import re

# Legible enough to say what the stone tells: at least MIN_WORDS words survive in the translation (fragments with a
# whole clause, such as "He died in England", count; "... in the west ..." does not). Translator additions in
# parentheses, "(?)", slash alternatives ("his/her" is one word), "<runes>" and name fragments ("-aldr") do not count.
MIN_WORDS = 4
# The legibility threshold is low: a fragment with four words ("... had the stone cut ...") counts as legible and
# gets 0 for every message. r/messages.R repeats the tests on stones with at least STRICT_WORDS legible words (the
# number is in the column legible_words of rows()), and scripts/check_messages.py prints the travel shares at both.
STRICT_WORDS = 10

# Places and peoples outside Norden, as Rundata's English spells them (Lombardy/Lombards, Tafeistaland, Seimgalir,
# Lífland, Holmgarðr/Holmgarðir, Eifor, Wallachians). Not "Tafeistr" or "Spjallboði": they are personal names. Not
# the Wends either: "Wends killed him" (Sö 351) says who killed him, not where. Finland and Estonia count as abroad
# (outside the Viking-age Scandinavian lands), Gotland, Denmark and Hedeby do not.
_PLACES = (r"england|london|bath|greece|greeks?|greek harbours|serkland|garðar|garðir|gardar|holmgarð\w*|novgorod|"
           r"estonia|virland|seimgal\w*|semgal\w*|lífland|livonia|finland|tafeistaland|tavastia|saxony|frisia|"
           r"lombard\w*|langbar\w*|langobard\w*|italy|jerusalem|jórdan|wendland|wallachians?|eifor")
# The Ingvarr expedition in its own formulas; a man who is only called Ingvarr is not a journey
_INGVARR = r"(?:with|among) ingvarr|ingvarr's(?:\s*\(\?\))?\s+(?:troop|retinue|men|ship|host|following)"
_ABROAD = (rf"{_PLACES}|{_INGVARR}|the west|the east|western route|eastern route|westwards|eastwards|abroad")
# How the commemorated person died. Burial ("lies", "buried") and a bare "died" do not say how or where; "died" and
# "was dead" count only with a place, a circumstance or a manner after them ("died in Greece", "died at home")
_AFTER_DIED = (r"(?:\(\?\))?(?:\s+\w+ly)?\s+(?:in|at|on|from|of|with|among|abroad|out|east|west|south|north|home|"
               r"there|far|by|during|when|while|after|before|under|young)\b")
_HOW = (rf"died{_AFTER_DIED}|(?:was|were) dead{_AFTER_DIED}|was killed|were killed|was slain|were slain|fell|drowned|"
        r"perished|met (?:his|their) end|forfeited (?:his|their) li(?:fe|ves)|lost (?:his|their) li(?:fe|ves)|"
        r"was burned|were burned|was betrayed|were betrayed|ended (?:his|their)|"
        # active voice: "Wends killed him", "Vígmundr slaughtered him", "his murdered son", "betrayed him"
        r"killed (?:him|them|their|his|her)\b|slew|slaughtered|murdered|betrayed (?:him|them)\b")
_BURIAL = r"lies|lie |rests|buried|coffin|laid (?:him|them) in"
# Where the death or the burial happened: also a bare "died" and burial, since the place follows
_DEATH = rf"{_HOW}|died|(?:was|were) dead|{_BURIAL}"
# Journeys with a destination or a direction outside Norden; a bare "travelled", "journey" or "voyage" does not count
# ("travelled from Scania", "died on a voyage", "had travelled valiantly"), "travelled to every land" does
_TRAVEL = (r"(?:to|in) every land|went (?:west|east|abroad)|(?:been|was|were|sat) (?:long )?(?:in|on) the (?:west|east)|"
           r"in the (?:west|east)|abroad|eastwards|westwards|western route|eastern route|(?:took|taken) .{0,30}payments?")
# Between the death and the place: within the clause, across lacuna dots ("perished ... in the east")
_GAP = r"(?:[^.;§]|\.\.\.)"
# Between the place and the death right after it ("in Serkland lies", "England, died in"), not across "but"/"then"
_NEAR = r"(?:(?!\b(?:but|then)\b)[^.;§])"

PATTERNS = {
    # the stone says how or where the commemorated person died
    "dod_uppgift": re.compile(rf"\b(?:{_HOW})", re.I),
    # ... and that it happened outside Scandinavia
    # (the death before the place, or the place right before it; not "travelled to the west, but then died at Hedeby"
    # or "travelled to England; then died grievously at home", but "was with the Greeks; then died with them")
    "dod_borta": re.compile(rf"\b(?:{_DEATH})\b{_GAP}{{0,80}}\b(?:{_ABROAD})\b|\b(?:{_ABROAD})\b{_NEAR}{{0,15}}\b(?:{_DEATH})"
                            rf"|\b(?:{_ABROAD})\b[^.§]{{0,15}}\b(?:died|perished|fell|was killed) (?:with them|there)\b", re.I),
    # a journey or a stay abroad
    "resa": re.compile(rf"\b(?:{_TRAVEL})|\b(?:{_ABROAD})\b", re.I),
    # payment, gold or silver gained
    "gald": re.compile(r"\b(payments?|gold|silver|geld|divided|earned wealth)\b", re.I),
    # inheritance
    "arv": re.compile(r"\b(inherit\w*|heirs?|inheritance)\b", re.I),
    # farm, estate, ownership of land; not "owned (i.e. was married to)", "owned (= had) one daughter", "owned a ship"
    "gard": re.compile(r"\b(owned(?!\s*\((?:i\.?\s?e\.?|=))(?!\s+(?:a|the) (?:cargo-)?ship)|farms?|estates?|homestead|village|"
                       r"lived(?:\(\?\))? (?:at|in|here)|resided|settled)\b", re.I),
    # raised in one's own memory, in one's lifetime ("in memory of myself", "and for himself", "(in memory of) himself")
    "egen": re.compile(r"(?:in memory of|for)\)?\s+(?:myself|himself|herself|themselves)|in (his|her|their) (own )?lifetime|"
                       r"while (he|she|they) (was |were )?(alive|living)", re.I),
    # praise of the dead (sponsors and carvers praised are left out in classify(): "Gunnborga the good coloured")
    # (not of God, the Virgin or the afterlife: "May excellent God help", "God's good maid", "the best home for
    # Christians"; not of the monument or a use: "the good landmark", "made good use of")
    "berom": re.compile(r"(?<!god's )\b(good|valiant|best|foremost|generous|able|ablest|capable|unvillainous|wise|mild|"
                        r"eloquent|bold|brave|dear|beloved|noble|excellent|gentle|amiable|venerable|of strength|"
                        r"(?:free|liberal|generous) with food|most (?:skil?lful|free|generous))\b"
                        r"(?!(?:\(\?\))?\s+(?:god|christ|home|landmark|monument|memorial|use)\b)", re.I),
}
KEYS = tuple(PATTERNS)
LABELS = {"dod_uppgift": ("Säger hur eller var den döde dog", "Says how or where the dead person died"),
          "dod_borta": ("Dog utanför Norden", "Died outside Scandinavia"),
          "resa": ("Resa eller vistelse utanför Norden", "Journey or stay outside Scandinavia"),
          "gald": ("Gäld, guld eller silver", "Payment, gold or silver"),
          "arv": ("Arv", "Inheritance"),
          "gard": ("Gård och ägande", "Farm and ownership"),
          "egen": ("Rest åt sig själv i livstiden", "Raised for oneself in one's lifetime"),
          "berom": ("Beröm av den döde", "Praise of the dead")}

# Local places that read like a direction: Sö 196 "made this Assembly-(place) in the east(?)" (alternative reading
# "avenged the betrayals in the west"); not a journey abroad (the hand coding leaves the stone out as uncertain)
_LOCAL = re.compile(r"\(?assembly-?\(?place\)?\)?\s+in the (?:east|west)|betrayals in the west", re.I)
# Inscriptions where only the first sentences are about the dead: the rest of Rök (Ög 136) is legend (Þjóðríkr the
# bold, who "nine generations ago lost his life with the Hreidgoths")
_ONLY_SENTENCES = {"Ög 136": 2}
# A praised name that is the subject of the raising or the carving: "Gísl and Ingimundr, good valiant men, had the
# landmark made", "Ólôf's able sons, they raised", "Gunnborga the good coloured this stone", "The unvillainous Bjôrn
# raises the stone" (past and present tense)
_SPONSOR_VERB = re.compile(r"[^.;]*?\b(?:had|have|has|let|raised|raise|raises|made|make|makes|erected|erects|erect|placed|"
                           r"places|place|set|sets|coloured|colours|carved|carves|cut|cuts|marked|marks)\b", re.I)
# ... or praised sponsors with no verb after them: "able lads in memory of their father" (U 225)
_SPONSOR_APPOSITION = re.compile(r"\s+(?!(?:and|or|his|her|their)\b)\w+\s+in memory of\b", re.I)
_WORD = re.compile(r"(?<![-\w])[A-Za-zÀ-ÿðþæøåäöôÐÞ]{2,}(?![-\w])")


def _text(rec: dict) -> str:
    """Översättningen utan avsnittsmärken och lokala platser, avgränsad där resten inte handlar om den döde."""
    t = re.sub(r"§[A-Z]+\s*", " ", rec.get("translation_en") or "")
    n = _ONLY_SENTENCES.get(rec.get("signum"))
    if n:
        t = " ".join(re.split(r"(?<=\.)\s+", t.strip())[:n])
    return _LOCAL.sub(" ", t)


def _legible_words(t: str) -> int:
    """Ord som går att läsa: utan översättarens tillägg, '(?)', runföljder och namnfragment; 'a/b' är ett ord."""
    t = re.sub(r"\([^()]*\)|<[^<>]*>", " ", t)
    t = re.sub(r"(\w+)(?:/[\w-]+)+", r"\1", t)
    return len(_WORD.findall(t))


def _praises_dead(t: str) -> bool:
    """Berömmer stenen den döde? Inte när den berömde är den som reste eller ristade stenen."""
    for m in PATTERNS["berom"].finditer(t):
        before = re.split(r"(?<!\.)\.(?!\.)|;", t[:m.start()])[-1]
        if re.search(r"\bin memory of\b", before, re.I):
            return True
        if _SPONSOR_APPOSITION.match(t, m.end()):
            continue
        rest = _SPONSOR_VERB.match(t, m.end())
        if not rest or re.search(r"\b(?:in memory of|who|whom)\b", rest.group(0), re.I):
            return True
    return False


def legible_words(rec: dict) -> int:
    """Antalet läsbara ord i översättningen (det som MIN_WORDS prövas mot)."""
    return _legible_words(_text(rec))


def classify(rec: dict) -> dict:
    """{budskap: 1, 0 eller None} för en inskrift; None när för få ord av översättningen går att läsa."""
    t = _text(rec)
    if _legible_words(t) < MIN_WORDS:
        return {k: None for k in KEYS}
    out = {k: int(bool(p.search(t))) for k, p in PATTERNS.items() if k != "berom"}
    out["berom"] = int(_praises_dead(t))
    if out["dod_borta"]:
        out["dod_uppgift"] = out["resa"] = 1
    return {k: out[k] for k in KEYS}


_WEST = re.compile(r"\b(england|london|bath|the west|western route|westwards|saxony|frisia)\b", re.I)
# Jerusalem, Jordan, Italy and Lombardy: the eastern route, as the inscriptions say ("ploughed his stern to the east,
# and met his end in the land of the Lombards", "on the eastern route abroad in Lombardy", "travel to the east and
# abroad to Jerusalem")
_EAST = re.compile(rf"\b(greece|greeks?|greek harbours|serkland|garðar|garðir|gardar|holmgarð\w*|novgorod|estonia|virland|"
                   rf"seimgal\w*|semgal\w*|lífland|livonia|finland|tafeistaland|tavastia|lombard\w*|langbar\w*|"
                   rf"langobard\w*|italy|jerusalem|jórdan|wendland|wallachians?|eifor|{_INGVARR}|the east|"
                   rf"eastern route|eastwards)\b", re.I)


def direction(rec: dict) -> str:
    """Resans riktning: 'väst', 'öst', 'båda' eller '' (ingen resa eller okänd riktning)."""
    t = _text(rec)
    w, e = bool(_WEST.search(t)), bool(_EAST.search(t))
    return "båda" if w and e else "väst" if w else "öst" if e else ""


# Landsdelar ur landskapens signumprefix (de svenska runstenarna i korpusen)
REGION = {**{p: "Götaland" for p in ("Ög", "Vg", "Sm", "Öl", "Bo", "Hr", "Ds")},
          **{p: "Svealand" for p in ("U", "Sö", "Vs", "Nä", "Gs", "D", "Vr")},
          **{p: "Norrland" for p in ("Hs", "M", "J", "Ån", "Me", "Lp")}, "G": "Gotland"}


def rows(inscriptions: list[dict]) -> list[dict]:
    """En rad per svensk vikingatida runsten: signum, landsdel, resans riktning, antalet läsbara ord och budskapen
    (r/messages.R)."""
    from src import research_gaps as gaps
    out = []
    for r in inscriptions:
        if not gaps.is_runestone(r):
            continue
        c = classify(r)
        out.append({"signum": r["signum"], "region": REGION.get(gaps.province(r), ""), "direction": direction(r),
                    "legible_words": legible_words(r), **{f"msg_{k}": c[k] for k in KEYS}})
    return out
