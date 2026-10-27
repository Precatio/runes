"""Vad runstenarna berättar om den döde: budskapen i Rundatas engelska översättning, en regel per budskap.

Budskapen räknas per sten (står det på stenen eller inte) och bara på stenar där minnesformeln går att läsa; på övriga
är budskapet okänt (None). De prövas i r/messages.R mot landsdel, tid och ristare (METHODS.md avsnitt 1o).

Reglerna är medvetet enkla och öppna: en sten kan bära flera budskap, och 'resa' och 'död borta' gäller resor utanför
Norden (inte inrikes färder). Handkodningen av de 55 västerinskrifterna (utdata/brittiska/hemma_kodning.csv) är
facit för resa och död borta (scripts/check_messages.py).
"""
import re

# Legible enough to say what the stone tells: at least MIN_WORDS words survive in the translation (fragments with a
# whole clause, such as "He died in England", count; "... in the west ..." does not)
MIN_WORDS = 4

_ABROAD = (r"england|london|bath|greece|greeks|serkland|garðar|gardar|holmgarð|novgorod|estonia|virland|semgall|livonia|"
           r"finland|tavastia|saxony|frisia|langobard|italy|jerusalem|jórdan|ingvarr|the west|the east|western route|"
           r"eastern route|westwards|eastwards|abroad|wendland|gotland")
_DEATH = (r"died|was killed|were killed|was slain|were slain|fell|drowned|perished|met (?:his|their) end|"
          r"forfeited (?:his|their) li(?:fe|ves)|lost (?:his|their) li(?:fe|ves)|lies|lie |rests|was burned|were burned|"
          r"was betrayed|were betrayed|ended (?:his|their)|buried|coffin|laid (?:him|them) in")
_TRAVEL = (r"travell?ed|journey|voyage|went (?:west|east|abroad)|sailed|was (?:in|on) the (?:west|east)|"
           r"(?:been|was|were|sat) (?:long )?(?:in|on) the (?:west|east)|in the (?:west|east)|abroad|eastwards|westwards|"
           r"western route|eastern route|traveller to|with ingvarr|steered|(?:took|taken) .{0,30}payments?")

PATTERNS = {
    # the stone says how or where the commemorated person died
    "dod_uppgift": re.compile(rf"\b(?:{_DEATH})", re.I),
    # ... and that it happened outside Scandinavia
    # (the death before the place, or the place right before it; not "travelled to the west, but then died at Hedeby")
    "dod_borta": re.compile(rf"\b(?:{_DEATH})\b[^.;§]{{0,80}}\b(?:{_ABROAD})|\b(?:{_ABROAD})\b[^.;§]{{0,15}}\b(?:{_DEATH})", re.I),
    # a journey or a stay abroad
    "resa": re.compile(rf"\b(?:{_TRAVEL})|\b(?:{_ABROAD})\b", re.I),
    # payment, gold or silver gained
    "gald": re.compile(r"\b(payments?|gold|silver|geld|divided)\b", re.I),
    # inheritance
    "arv": re.compile(r"\b(inherit\w*|heirs?|inheritance)\b", re.I),
    # farm, estate, ownership of land
    "gard": re.compile(r"\b(owned|farms?|estates?|homestead|village|lived (?:at|in)|resided|settled)\b", re.I),
    # raised in one's own memory, in one's lifetime
    "egen": re.compile(r"in memory of (himself|herself|themselves)|in (his|her|their) (own )?lifetime|while (he|she|they) "
                       r"(was |were )?(alive|living)", re.I),
    # praise of the dead
    "berom": re.compile(r"\b(good|valiant|best|foremost|generous|able|capable|unvillainous|wise|mild|eloquent|"
                        r"bold|brave|dear|beloved|noble)\b", re.I),
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


def classify(rec: dict) -> dict:
    """{budskap: 1, 0 eller None} för en inskrift; None när minnesformeln inte går att läsa."""
    t = re.sub(r"§[A-Z]+\s*", " ", rec.get("translation_en") or "")
    if len(re.findall(r"[A-Za-zÀ-ÿðþæøåäöÐÞ]{2,}", t)) < MIN_WORDS:
        return {k: None for k in KEYS}
    out = {k: int(bool(p.search(t))) for k, p in PATTERNS.items()}
    if out["dod_borta"]:
        out["dod_uppgift"] = out["resa"] = 1
    return out


_WEST = re.compile(r"\b(england|london|bath|the west|western route|westwards|saxony|frisia|langobard|italy|jerusalem|jórdan)\b", re.I)
_EAST = re.compile(r"\b(greece|greeks|serkland|garðar|gardar|holmgarð\w*|novgorod|estonia|virland|semgall|livonia|finland|"
                   r"tavastia|ingvarr|the east|eastern route|eastwards|wendland)\b", re.I)


def direction(rec: dict) -> str:
    """Resans riktning: 'väst', 'öst', 'båda' eller '' (ingen resa eller okänd riktning)."""
    t = rec.get("translation_en") or ""
    w, e = bool(_WEST.search(t)), bool(_EAST.search(t))
    return "båda" if w and e else "väst" if w else "öst" if e else ""


# Landsdelar ur landskapens signumprefix (de svenska runstenarna i korpusen)
REGION = {**{p: "Götaland" for p in ("Ög", "Vg", "Sm", "Öl", "Bo", "Hr", "Ds")},
          **{p: "Svealand" for p in ("U", "Sö", "Vs", "Nä", "Gs", "D", "Vr")},
          **{p: "Norrland" for p in ("Hs", "M", "J", "Ån", "Me", "Lp")}, "G": "Gotland"}


def rows(inscriptions: list[dict]) -> list[dict]:
    """En rad per svensk vikingatida runsten: signum, landsdel, budskapen och resans riktning (r/messages.R)."""
    from src import research_gaps as gaps
    out = []
    for r in inscriptions:
        if not gaps.is_runestone(r):
            continue
        c = classify(r)
        out.append({"signum": r["signum"], "region": REGION.get(gaps.province(r), ""), "direction": direction(r),
                    **{f"msg_{k}": c[k] for k in KEYS}})
    return out
