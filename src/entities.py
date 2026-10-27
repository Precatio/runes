"""Enheterna i en runinskrift: personer med roll och släktskap, platser och händelser, ur Rundatas engelska översättning.

Namnen tas ur översättningen, där de står i grundform (Gunnelfr, Ásbjôrn, Goti), men räknas bara när de motsvarar ett
ord som Rundatas fornvästnordiska normalisering märker som namn (citattecken), så att engelska ord med versal inte blir
personer. Roller och släktskap läses ur formeln:

  resare        namn före verbet (raised, placed, had … made, erected, cut)   "Gunnelfr had the stone raised"
                även en medresare: "…, and Heðindís in memory of her husbandman", "(so did) Ásgautr",
                "and Illugi and Signy (also had it cut)", och beställaren: "Inga had the stones cut", "Holmdórr ordered Œpir to carve"
  minnes        namn efter "in memory of"                                     "in memory of Ásbjôrn and … Goti"
                och namnet efter ett släktord ("his father's father Eysteinn"); ett namn som efter en lucka står i
                en annan utsaga ("… making of the landmark Vani") är bara nämnt
  släktskap     ordet efter eller före den minnes namn                         "Goti, her sons" / "his father Spjót"
                ett pluralt ord gäller hela uppräkningen, efter den ("Jafri and Vígr, his brothers", "in memory of
                Ásbjôrn and in memory of Goti, her sons") och före den ("his sons Sveinn and Hrœmingr"); sammansatta
                led ("his father's father", "his wife's brother") blir grandfather, nephew, brother-in-law …, aldrig
                father eller brother, och "mother-in-law" blir aldrig mother
  ristare       namn i en sats om runorna utan minnesformel                     "Œpir cut." / "Þórir the Crane carved."
                och den som får uppdraget: "ordered Œpir to carve" ("cut down" är inget ristande)
  nämnd         övriga namn, bland dem släkt i genitiv och efter "son/father/heir/godson … of"
  fadersnamn    "X, Y's son" och "Y's son X"
  plats         namn efter in/at/of/from/on (och ortnamnen i ABROAD)            "Ragnfastr of Snotastaðir"
  händelse      Ingvarståget, Knuts gäld och resmålen utanför Norden          "with Ingvarr", "in Ingvarr's retinue",
                                                                                "when Knútr attacked England"

Satserna delas vid . ; ! ? men inte vid en lucka (...), så att resare och minnes på en skadad sten stannar i samma sats,
och vid ett "(?)" som står där punkten saknas ("Jôrundr(?) Œpir carved", "Heilfúss(?) He died"). Över en lucka blir ingen
ristare som har ett eget verb före luckan ("Hefnir died at home ... ... cut the runes").
Ett namn som normaliseringen märker räknas även när det är delvis kompletterat ("[Íg]ulfastr, "Arn[k]ell).
Släktskapen ger fakta (den minnes, släktordet, resaren) för resarna i samma sats; inte för en resare med en egen
släktskap ("Hróðelfr, their mother") och aldrig en person till sig själv (sonen som bär faderns namn). "Their father" gäller
också resarna i en tidigare formel för samma person ("A and B raised the stone in memory of Loðinn ... C erected in memory
of Loðinn, their father"). En senare medresare med eget släktord är släkt med den förste resaren ("her son") eller med
den döde ("his son" när resaren är hans hustru).

Reglerna är enkla och redovisade; de missar ovanliga formuleringar och tolkar inte otolkade inskrifter. Används av
src/linking.py (samma personer, platser och händelser på flera stenar).
"""
from __future__ import annotations

import re
import unicodedata

STOP = {"God", "Christ", "Mary", "Lord", "May", "He", "She", "They", "And", "Then", "This", "These", "Here", "In", "The",
        "A", "An", "It", "His", "Her", "Their", "Who", "Interpret", "Holy", "Michael", "Jesus", "Spirit", "Saint", "Sun",
        "Thor", "Þórr", "Óðinn", "Odin", "Heimdallr", "Valhalla", "Midgard"}
# Places outside Scandinavia and regions: events and destinations, not farms
ABROAD = {"England": "England", "London": "England", "Bath": "England", "Ireland": "Irland", "Scotland": "Skottland",
          "Greece": "Grekland", "Greeks": "Grekland", "Serkland": "Serkland", "Garðar": "Garðar", "Holmgarðr": "Garðar",
          "Novgorod": "Garðar", "Estonia": "Estland", "Virland": "Estland", "Semgallia": "Semgallen", "Livonia": "Livland",
          "Finland": "Finland", "Tavastia": "Finland", "Saxony": "Saxland", "Frisia": "Frisland", "Lombardy": "Langobardland",
          "Langbarðaland": "Langobardland", "Italy": "Langobardland", "Jerusalem": "Jerusalem", "Jórdan": "Jerusalem",
          "Gotland": "Gotland", "Jútland": "Jylland", "Jutland": "Jylland", "Denmark": "Danmark", "Hedeby": "Hedeby",
          "Heiðabý": "Hedeby", "Wendland": "Vendland"}
EVENTS = {"Ingvarr": "Ingvarståget", "Knútr": "Knuts gäld"}  # a name that marks an event when it is the leader, not kin
RAISE = r"(?:raised|raise|placed|place|had|has|have|made|make|erected|erect|let|set|laid|lay|cut|carved|built)"
CARVE = r"(?:carved|carve|cut|wrote|coloured|colored|painted|made the runes|struck|hewed|marked)"
NOT_CUT_DOWN = r"(?!cut\s+down\b)"  # "Varinn, who the husbandmen cut down": a killing, not a carving
CAUSE = r"\b(?:had|has|have|let|ordered|bade|asked)\b"  # the subject of "had … cut" is the sponsor, not the carver
# the longer words first, so that "his mother-in-law" is never read as "mother"
REL = "(?:" + "|".join(sorted(
    "father mother son sons daughter daughters brother brothers sister sisters wife husband husbandman housewife kinsman "
    "kinsmen uncle nephew grandfather grandson father-in-law mother-in-law son-in-law daughter-in-law brother-in-law "
    "stepson stepfather stepmother foster-son foster-father foster-mother foster-brother partner comrade master lord "
    "freedman retainer friend heir godson godfather".split(), key=len, reverse=True)) + ")"
FEMALE = {"mother", "daughter", "daughters", "sister", "sisters", "wife", "housewife", "mother-in-law",
          "daughter-in-law", "stepmother", "foster-mother", "grandmother", "niece", "aunt"}
PLURAL = {"sons", "daughters", "brothers", "sisters", "kinsmen"}
# "his father's father", "his brother's son": the relation is the compound, never its first word
COMPOUND = {("father", "father"): "grandfather", ("mother", "father"): "grandfather",
            ("father", "mother"): "grandmother", ("mother", "mother"): "grandmother",
            ("son", "son"): "grandson", ("daughter", "son"): "grandson",
            ("brother", "son"): "nephew", ("sister", "son"): "nephew",
            ("brother", "daughter"): "niece", ("sister", "daughter"): "niece",
            ("father", "brother"): "uncle", ("mother", "brother"): "uncle",
            ("father", "sister"): "aunt", ("mother", "sister"): "aunt",
            ("wife", "brother"): "brother-in-law", ("husband", "brother"): "brother-in-law",
            ("wife", "father"): "father-in-law", ("husband", "father"): "father-in-law",
            ("wife", "mother"): "mother-in-law", ("husband", "mother"): "mother-in-law",
            ("son", "wife"): "daughter-in-law", ("daughter", "husband"): "son-in-law",
            ("sister", "husband"): "brother-in-law", ("daughter", "husbandman"): "son-in-law",
            ("sister", "husbandman"): "brother-in-law"}
NAME = r"[A-ZÁÉÍÓÚÝÞÐÆØÖÄÅÔÂŒǪ][\wôœæøþðáéíóúýǫ-]+"
PREP = re.compile(r"\b(?:in|at|from|on)\s+$", re.I)
# After "of" a name is a place only with a place-name ending (Ragnfastr of Snotastaðir; but "of Holmgeirr" is a person)
PLACE_END = re.compile(r"(?:staðir|stöðum|býr|bý|by|ey|eyju|hamarr|land|lundr|lundir|vík|nes|holmr|holmi|tuna|tún|vin|"
                       r"heimr|hof|berg|ás|dalr|fjôrðr|kíll|á|ár|sta|garðr|torp|þorp|hús|heiðr|sæti)$", re.I)


def fold(s: str) -> str:
    """Bokstäverna utan accenter och med þ/ð/æ/ø/ô utskrivna: för att jämföra namnformer."""
    s = s.lower().replace("þ", "th").replace("ð", "d").replace("æ", "ae").replace("ø", "o").replace("ô", "o") \
        .replace("œ", "oe").replace("ǫ", "o")
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _marked(rec: dict) -> list[str]:
    """De ord som normaliseringen märker som namn ("Gunnelfr), med kompletteringarna inlästa ("[Íg]ulfastr, "Arn[k]ell)
    och varje läsning för sig ("Ál/Áli/"Alli)."""
    ows = re.sub(r"[\[\]]", "", rec.get("normalization_ows") or "")
    return [fold(w) for g in re.findall(r'"([^\s,.;:()!?]+)', ows) for w in re.split(r'[/"]', g) if w]


def _is_marked(word: str, marked: list[str]) -> bool:
    f = fold(word)
    k = min(4, len(f) - 1) if len(f) > 3 else len(f)
    return any(m[:k] == f[:k] for m in marked if len(m) >= 2)


def _compound(a: str, b: str) -> str:
    a, b = a.lower(), (b or "").lower()
    if not b:
        return a
    one = b[:-1] if b in PLURAL else b  # "her sister's sons": nephew for each of them
    return COMPOUND.get((a, one)) or f"{a}'s {b}"


def _rel_side(after: str, before: str) -> tuple[str | None, str | None, str]:
    """(släktordet, "after"/"before", pronomenet his/her/their): efter namnet ("Goti, her sons") eller före det ("his
    father Spjót", "his father's father Eysteinn"); ett sammansatt led ger hela släktskapen (grandfather), inte dess
    första ord."""
    m = re.match(rf",?\s*(?:(his|her|their|and \w+'s)\s+)(?:\w+\s+){{0,2}}?({REL})\b(?:'s\s+({REL})\b)?(?!'s\s+\w)",
                 after, re.I)
    if m:
        return _compound(m.group(2), m.group(3)), "after", m.group(1).lower()
    m = re.search(rf"\b(his|her|their)\s+(?:\w+\s+)?(?:({REL})'s\s+)?({REL})\s+$", before, re.I)
    if m:
        return (_compound(m.group(2), m.group(3)) if m.group(2) else m.group(3).lower()), "before", m.group(1).lower()
    return None, None, ""


def _rel(after: str, before: str) -> str | None:
    """Släktordet efter eller före namnet (se _rel_side)."""
    return _rel_side(after, before)[0]


LIST_WORDS = {"and", "or", "his", "her", "their", "the", "a", "an", "of", "in", "memory", "remembrance", "after", "both",
              "two", "three", "four", "five", "good", "dear", "beloved"}  # words of a list of the commemorated
SENTENCE = r"(?:He|She|They|May|And|Here|This|These|Then|It)\b"  # words that begin a statement, not a name


def _query(m: re.Match) -> str:
    """Ett "(?)" som saknar punkten före en ny sats: "Jôrundr(?) Œpir carved" (två personer, inte namn och binamn),
    "Heilfúss(?) He died". Efter ett släktord eller "of" ("stepfather(?) Víghjalmr", "heir of(?) Gansi"), före ett namn i
    genitiv ("Fullugi(?) Freygeirr's heir"), före ett binamn som "Narfasonr" eller "Kauparfa" och efter ett ord som "And" faller det bara bort."""
    prev, nxt = m.group(1), m.group(2).strip()
    if prev.endswith(".") or not re.match(r"[A-ZÁÉÍÓÚÝÞÐÆØÖÄÅÔÂŒǪ]", nxt):
        return prev
    if re.match(SENTENCE, nxt):
        return prev + "."
    if re.match(NAME, prev) and prev not in STOP and not re.search(r"['’]s$", prev) \
            and not re.match(rf"{NAME}['’]s\b", nxt) and not re.match(r"\S*(?:sonr|arfi|arfa|arve)\b", nxt):
        return prev + "."
    return prev


def _clauses(t: str) -> list[str]:
    """Satserna: delade vid . ; ! ? men inte vid en lucka (... eller …), och före en medresare med egen minnesformel
    ("…, his father, and Heðindís in memory of her husbandman")."""
    t = re.sub(r"\.{2,}|…", "…", t)
    # a lacuna still ends the clause before a word that starts a sentence ("... And Brúsi coloured", "... May God")
    starts = "|".join(sorted(STOP, key=len, reverse=True))
    t = re.sub(rf"…\s+(?=(?:{starts})\b)", "…. ", t)
    out = []
    for c in re.split(r"(?<=[.;!?])\s+", t):
        # "…, his father, and Heðindís in memory of her husbandman": a new raiser with a formula of her own; the
        # co-raisers are consumed with the "and", and an "and" inside a list of names ("Ôzurr and Fullugi in memory
        # of") is no boundary
        # but "Sigfastr and Sigfuss raised this stone and Heðinfríða in memory of Véfastr, their father": a first part
        # without a formula of its own shares "their" father with her
        def cut(m):
            pre = c[:m.start()]
            if re.search(rf"(?:^|[^\w-]){NAME}$", pre) or (
                    not re.search(r"\bin (?:memory|remembrance) of\b|\bafter\b", pre, re.I)
                    and re.search(r"\btheir\b", c[m.end():m.end() + 80], re.I)):
                return m.group(0)
            return "\x00" + m.group(1)
        c = re.sub(rf",?\s+and\s+((?:{NAME}(?:,\s*|\s+and\s+))*{NAME}\s+(?:in (?:memory|remembrance) of|after)\b)",
                   cut, c)
        out += c.split("\x00")
    return out


def extract(rec: dict) -> dict:
    """{persons: [{name, key, role, rel, female}], places: [..], events: [..], facts: [(a, rel, b)]} för en inskrift."""
    t = rec.get("translation_en") or ""
    t = re.sub(r"(?:\.{2,}|…)\s*§[A-Z]+\s*", "…. ", t)  # a side that begins after a lacuna begins a new clause
    t = re.sub(r"§[A-Z]+\s*", " ", t).replace("(and)", "and")
    t = re.sub(r"(\S+)\(\?\)(?=(\s+\S+))", _query, t).replace("(?)", "")
    t = re.sub(r"([\wôœæøþðáéíóúýǫ]+)(?:/[\wôœæøþðáéíóúýǫ-]+)+", r"\1", t)  # Ál/Áli/Alli, father/brother-in-law: the first reading
    t = re.sub(r"\((?:it|the stone|he|she|they|the runes|this|these|stones?|his|her|their)\)", lambda m: m.group(0)[1:-1], t)
    marked = _marked(rec)
    persons, places, events, facts = [], [], set(), []
    seen = {}

    def person(name, role, rel=None, clause=0):
        key = fold(name)
        p = seen.get((key, role))
        if p is None:
            p = {"name": name, "key": key, "role": role, "rel": rel, "female": bool(rel and rel in FEMALE), "clause": clause}
            seen[(key, role)] = p
            persons.append(p)
        elif rel and not p.get("rel"):
            p["rel"], p["female"] = rel, rel in FEMALE
        return p

    for ci, clause in enumerate(_clauses(t)):
        found = [m for m in re.finditer(NAME, clause)
                 if m.group(0) not in STOP and (m.group(0) in ABROAD or _is_marked(m.group(0), marked))]
        # a byname right after a name (Þorbjôrn Skald, Þórir the Crane) belongs to the person, not a person of its own
        names = [(m.start(), m.group(0)) for i, m in enumerate(found)
                 if not (i and m.start() - found[i - 1].end() <= 1 and found[i - 1].group(0) not in ABROAD)]
        if not names:
            continue
        mem = re.search(r"\bin (?:memory|remembrance) of\b|\bafter\b", clause, re.I)
        verb = re.search(rf"\b{NOT_CUT_DOWN}{RAISE}\b", clause, re.I)
        carve = re.search(rf"\b{NOT_CUT_DOWN}{CARVE}\b", clause, re.I)
        cause = re.search(CAUSE, clause, re.I)
        here, seg = [], 0  # the mentions of this clause, with their own relation; seg: a raiser's own formula
        for pos, nm in names:
            before = clause[:pos]
            after = clause[pos + len(nm):]
            if nm in ABROAD:
                events.add(ABROAD[nm])
                continue
            if nm == "Ingvarr" and (re.search(r"\bwith\s+$|east|travel|ship|Serkland", before + after, re.I)
                                    or re.match(r"'s\s+(?:troop|retinue|men|band|host|army|following|company|lið)\b", after, re.I)) \
                    and not (mem and pos > mem.start() and re.match(rf",?\s*(?:his|her|their)\s+{REL}", after, re.I)):
                events.add(EVENTS[nm])
                continue
            if nm in EVENTS and re.search(r"\bwith\s+$", before, re.I):
                events.add(EVENTS[nm])
                continue
            if nm == "Knútr" and (re.search(r"payment|paid", clause, re.I) or re.search(r"\b(?:when|king)\s+$", before, re.I)):
                events.add(EVENTS[nm])  # "when Knútr attacked England", "King Knútr": the leader, not a person on the stone
                continue
            kin_of = re.search(rf"\b(?:{REL}|widow) of\s+$", before, re.I)
            if kin_of:  # "Melbrigði, the son of Aðakán", "the father of Danr", "godson of Ólafr": kin, not a place or a role
                person(nm, "nämnd", clause=ci)
                continue
            of_place = re.search(r"\bof\s+$", before) and PLACE_END.search(nm)
            if (PREP.search(before) or of_place) and not re.match(r"'s\b", after) \
                    and not re.search(r"memory of\s+$|of\s+(?:his|her|their)\s+$", before, re.I):
                places.append({"name": nm, "key": fold(nm)})
                continue
            rel, side, pron = _rel_side(after, before)
            # "Inga had the stones cut", "Stóðkell ordered Óþveginn to cut": the one who has it done raised the stone
            late = False
            sponsor = bool(carve and cause and cause.start() < carve.start() and pos < cause.start())
            # a lacuna between the name and the carve verb cuts them apart when another name or a verb of the name's
            # own stands between: "Þorkell and ... Brandr ... Œpir carved", "Hefnir died at home ... ... cut the runes",
            # "Bjôrn ... the stone raised ... carved these runes"
            cross = False
            if carve and pos < carve.start():
                span = clause[pos + len(nm):carve.start()]
                cross = "…" in span and (any(pos < q < carve.start() for q, _ in names)
                                         or bool(re.search(rf"\b(?:died|perished|fell|drowned|was|were|lived|{RAISE})\b",
                                                           span, re.I)))
            elif carve:
                cross = "…" in clause[carve.end():pos]
            # after the memorial formula: a carver ("... Hákon cut the landmark") or a raiser of her own ("..., and ...
            # Ásgerðr in memory of her husbandman", "... Jôfurr and Foks had the stone raised"), but never the one the
            # formula names ("and Arnlaug in memory of Ónæmr in memory of ...")
            they = r"(?:,?\s+(?:they|he|she))?\s+"
            carves_here = bool(re.match(rf"(?:\s+and\s+{NAME})*{they}{NOT_CUT_DOWN}{CARVE}\b", after))
            # a carve verb after a list ("…, Œpir carved") makes nobody a raiser
            rh = re.match(rf"(?:(?:,\s*|\s+and\s+){NAME})*{they}(in (?:memory|remembrance) of|after|{RAISE})\b", after)
            raises_here = bool(rh) and not re.fullmatch(CARVE, rh.group(1))
            obj = re.search(r"\b(?:in (?:memory|remembrance) of|after)\)?\s+$", before, re.I)
            # a name after the formula where a lacuna and words of another statement stand between ("in memory of …
            # Sig-... ... ... making of the landmark Vani", "They were ... Sveinn"): without a relation of its own it is
            # only named; "in memory of ... ... Vénjótr" and "his father ... Ágoti" stay commemorated
            chain = max([f.end() for f in re.finditer(r"\bin (?:memory|remembrance) of\b|\bafter\b", clause[:pos], re.I)]
                        + [h["end"] for h in here if h["role"] == "minnes"] + [0])
            span = clause[chain:pos]
            gap = "…" in span and bool(set(re.findall(r"[^\W\d_]+(?:-[^\W\d_]+)*", re.sub(r"…\S*|<[^>]*>", " ", span).lower()))
                                     - LIST_WORDS - set(REL[3:-1].split("|")))
            also = r"\s+\(also [^)]*\)"  # "(also raised)", "(also had it cut)", "(also made)"
            if re.match(r"'s\b", after):  # a name in the genitive (Sigríðr's son, Þóra's freedman) is kin, never a raiser
                p = person(nm, "nämnd", clause=ci)
            elif re.search(r"\bbut\s+$", before) and re.match(r"\s+made\b", after):  # en Gautr gerði: but Gautr made
                p = person(nm, "ristare", clause=ci)
            elif re.search(r"\b(?:ordered|bade|asked)\s+$", before, re.I) and \
                    re.match(r"\s+to\s+(?:carve|cut|write|colou?r|paint|make the runes)\b", after, re.I):
                p = person(nm, "ristare", clause=ci)  # "ordered Œpir to carve"
            elif re.search(r"\(so did\)\s+$", before, re.I) or re.match(also, after, re.I) or \
                    (mem and pos > mem.start() and re.match(rf"(?:(?:,\s*|\s+and\s+){NAME})*{also}", after)):
                p = person(nm, "resare", clause=ci)  # "and (so did) Ásgautr", "and Illugi and Signy (also had it cut)"
                late = True  # the relation in the clause ("his son") is the first raiser's, not theirs
            elif mem and pos > mem.start() and carves_here:
                p = person(nm, "ristare", clause=ci)
            elif mem and pos > mem.start() and raises_here and not obj:
                p = person(nm, "resare", clause=ci)
                if here and here[-1]["role"] == "minnes":
                    seg += 1  # her own formula: the relations before her are not hers
            elif mem and pos > mem.start() and gap and not rel:
                p = person(nm, "nämnd", clause=ci)
            elif mem and pos > mem.start():
                p = person(nm, "minnes", rel, ci)
            elif mem and side == "before" and not raises_here and not carves_here:
                p = person(nm, "minnes", rel, ci)  # "... his father's father Eysteinn, and in memory of Guðríkr"
            elif carve and not mem and not sponsor and not cross \
                    and (not verb or carve.start() <= verb.start() or pos < carve.start()):
                p = person(nm, "ristare", clause=ci)
            elif sponsor or (verb and pos < verb.start() and not (cross and verb.start() == carve.start())) \
                    or (mem and pos < mem.start()):  # "Geiri, Guði … in memory of their brothers"
                p = person(nm, "resare", clause=ci)
            elif not mem and verb and pos > verb.end() and side == "after" and \
                    (len({h["p"]["key"] for h in here if h["role"] == "resare"}) >= 2) == (pron == "their") and \
                    any(h["role"] == "resare" for h in here):
                # the formula lost in a gap: "Þyrvé got this stone made ... Krókr, her husband"; the pronoun must fit the
                # raisers ("Þorkell and Sjafi had the stone-slab raised ... Heðinfast, his wife" is the dead man's wife)
                p = person(nm, "minnes", rel, ci)
            else:
                p = person(nm, "nämnd", rel, ci)
            here.append({"p": p, "role": p["role"], "rel": rel, "side": side, "pron": pron, "late": late, "seg": seg,
                         "start": pos, "end": pos + len(nm)})
            pm = re.match(rf",?\s*({NAME})'s\s+({REL})\b", after)
            if pm and _is_marked(pm.group(1), marked):
                r_ = pm.group(2).lower()
                if r_ in ("son", "sons", "daughter", "daughters"):  # "X, Y's son": Y is X's father or mother
                    facts.append((fold(pm.group(1)), "förälder till", p["key"]))
                else:  # "Manni, Myskja's brother": Manni is Myskja's brother
                    facts.append((p["key"], r_, fold(pm.group(1))))
                person(pm.group(1), "nämnd", clause=ci)

        # a plural relation covers the whole list: after it ("Jafri and Vígr, his brothers", "in memory of Ásbjôrn and in
        # memory of Goti, her sons") and, when it stands before the names, the list after it ("his sons Sveinn and
        # Hrœmingr", "his brothers Ásbjôrn and in memory of Guðlafr")
        sep_list = r"\s*,?\s*(?:and\s+)?"
        sep = sep_list + r"(?:\(?(?:in (?:memory|remembrance) of|after)\)?\s+)?"

        def spread(src, dst):
            dst["rel"], dst["pron"] = src["rel"], src["pron"]
            if not dst["p"].get("rel"):
                dst["p"]["rel"], dst["p"]["female"] = src["rel"], src["rel"] in FEMALE

        for i in range(len(here)):
            h = here[i]
            if h["role"] != "minnes" or h["rel"] not in PLURAL:
                continue
            # a new "in memory of" ends the list once the plural covers two names: "his sons Sveinn and Þorsteinn and in
            # memory of Sámr, a good valiant man"
            n, j = 1, i
            while j > 0 and here[j - 1]["role"] == "minnes" and not here[j - 1]["rel"] \
                    and re.fullmatch(sep if n == 1 else sep_list, clause[here[j - 1]["end"]:here[j]["start"]], re.I):
                j -= 1
                n += 1
                spread(h, here[j])
            j = i
            while h["side"] == "before" and j + 1 < len(here) and here[j + 1]["role"] == "minnes" and not here[j + 1]["rel"] \
                    and re.fullmatch(sep if n == 1 else sep_list, clause[here[j]["end"]:here[j + 1]["start"]], re.I):
                j += 1
                n += 1
                spread(h, here[j])

        def shared(m_, r):  # the same person is commemorated in r's own formula: "their father" is r's father too
            return m_["pron"] == "their" and any(h["role"] == "minnes" and h["p"]["key"] == m_["p"]["key"] and h["seg"] == r["seg"]
                                       for h in here)

        for m_ in here:  # the raisers of the same clause: m_ is r's <rel> (Ketill is Gautr's son)
            if m_["role"] != "minnes" or not m_["rel"]:
                continue
            for r in here:
                # not to a raiser with a relation of their own ("Hróðelfr, their mother") or one added afterwards ("(so
                # did) Ásgautr"), and never a person to himself
                if r["role"] == "resare" and (r["seg"] == m_["seg"] or shared(m_, r)) and not r["rel"] and not r["late"] \
                        and r["p"]["key"] != m_["p"]["key"]:
                    f = (m_["p"]["key"], m_["rel"], r["p"]["key"])
                    if f not in facts:
                        facts.append(f)
        # a raiser added afterwards with a relation of her own: "Ingiþóra had this stone raised in memory of her father
        # Sigtryggr, and (so did) Ragnfastr, her son" (her son: Ingiþóra's, since the dead man is a man); "Tonna placed
        # this stone in memory of Bramr, her husbandman, and (so did) Ásgautr, his son" (his son: Bramr's, since the
        # raiser is his wife)
        for r in here:
            if not (r["role"] == "resare" and r["late"] and r["rel"] and r["side"] == "after"):
                continue
            first = {h["p"]["key"] for h in here if h["role"] == "resare" and not h["late"] and h["seg"] == r["seg"]}
            dead = [h for h in here if h["role"] == "minnes" and h["rel"] and h["seg"] == r["seg"]]
            to = None
            if r["pron"] == "her" and len(first) == 1 and dead and all(h["rel"] not in FEMALE for h in dead):
                to = next(iter(first))
            elif r["pron"] == "his" and len(dead) == 1 and dead[0]["rel"] in ("husband", "husbandman"):
                to = dead[0]["p"]["key"]
            if to and to != r["p"]["key"]:
                f = (r["p"]["key"], r["rel"], to)
                if f not in facts:
                    facts.append(f)
    return {"signum": rec["signum"], "persons": persons, "places": places, "events": sorted(events), "facts": facts}
