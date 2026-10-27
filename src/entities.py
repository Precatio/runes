"""Enheterna i en runinskrift: personer med roll och släktskap, platser och händelser, ur Rundatas engelska översättning.

Namnen tas ur översättningen, där de står i grundform (Gunnelfr, Ásbjôrn, Goti), men räknas bara när de motsvarar ett
ord som Rundatas fornvästnordiska normalisering märker som namn (citattecken), så att engelska ord med versal inte blir
personer. Roller och släktskap läses ur formeln:

  resare        namn före verbet (raised, placed, had … made, erected, cut)   "Gunnelfr had the stone raised"
  minnes        namn efter "in memory of"                                     "in memory of Ásbjôrn and … Goti"
  släktskap     ordet efter eller före den minnes namn                         "Goti, her sons" / "his father Spjót"
  ristare       namn i en sats om runorna utan minnesformel                     "Œpir cut." / "Þórir the Crane carved."
  fadersnamn    "X, Y's son" och "Y's son X"
  plats         namn efter in/at/of/from/on (och ortnamnen i ABROAD)            "Ragnfastr of Snotastaðir"
  händelse      Ingvarståget, Knuts gäld och resmålen utanför Norden

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
CARVE = r"(?:carved|cut|wrote|coloured|colored|painted|made the runes|struck|hewed|marked)"
REL = (r"(?:father|mother|son|sons|daughter|daughters|brother|brothers|sister|sisters|wife|husband|husbandman|"
       r"housewife|kinsman|kinsmen|uncle|nephew|grandfather|grandson|father-in-law|mother-in-law|son-in-law|"
       r"daughter-in-law|brother-in-law|stepson|stepfather|stepmother|foster-son|foster-father|foster-mother|"
       r"foster-brother|partner|comrade|master|lord|freedman|retainer|friend|heir|godson|godfather)")
FEMALE = {"mother", "daughter", "daughters", "sister", "sisters", "wife", "housewife", "mother-in-law",
          "daughter-in-law", "stepmother", "foster-mother"}
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
    return [fold(w) for w in re.findall(r'"([^\s,.;:()\[\]!?/]+)', rec.get("normalization_ows") or "")]


def _is_marked(word: str, marked: list[str]) -> bool:
    f = fold(word)
    k = min(4, len(f) - 1) if len(f) > 3 else len(f)
    return any(m[:k] == f[:k] for m in marked if len(m) >= 2)


def after_all(clause: str, pos: int, nm: str) -> str:
    return clause[pos + len(nm):]


def extract(rec: dict) -> dict:
    """{persons: [{name, key, role, rel, female}], places: [..], events: [..], facts: [(a, rel, b)]} för en inskrift."""
    t = rec.get("translation_en") or ""
    t = re.sub(r"§[A-Z]+\s*", " ", t).replace("(and)", "and").replace("(?)", "")
    t = re.sub(r"([\wôœæøþðáéíóúýǫ]+)(?:/[\wôœæøþðáéíóúýǫ]+)+", r"\1", t)  # Ál/Áli/Alli: the first reading
    t = re.sub(r"\((?:it|the stone|he|she|they|the runes|this|these|stones?)\)", lambda m: m.group(0)[1:-1], t)
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

    for ci, clause in enumerate(re.split(r"(?<=[.;!?])\s+", t)):
        found = [m for m in re.finditer(NAME, clause)
                 if m.group(0) not in STOP and (m.group(0) in ABROAD or _is_marked(m.group(0), marked))]
        # a byname right after a name (Þorbjôrn Skald, Þórir the Crane) belongs to the person, not a person of its own
        names = [(m.start(), m.group(0)) for i, m in enumerate(found)
                 if not (i and m.start() - found[i - 1].end() <= 1 and found[i - 1].group(0) not in ABROAD)]
        if not names:
            continue
        mem = re.search(r"\bin (?:memory|remembrance) of\b|\bafter\b", clause, re.I)
        verb = re.search(rf"\b{RAISE}\b", clause, re.I)
        carve = re.search(rf"\b{CARVE}\b", clause, re.I)
        for pos, nm in names:
            before = clause[:pos]
            if nm in ABROAD:
                events.add(ABROAD[nm])
                continue
            if nm == "Ingvarr" and re.search(r"\bwith\s+$|east|travel|ship|Serkland", before + after_all(clause, pos, nm), re.I) \
                    and not (mem and pos > mem.start() and re.match(rf",?\s*(?:his|her|their)\s+{REL}", clause[pos + len(nm):], re.I)):
                events.add(EVENTS[nm])
                continue
            if nm in EVENTS and re.search(r"\bwith\s+$", before, re.I):
                events.add(EVENTS[nm])
                continue
            if nm == "Knútr" and re.search(r"payment|paid", clause, re.I):
                events.add(EVENTS[nm])
                continue
            kin_of = re.search(r"\b(?:son|sons|daughter|daughters|wife|widow|brother|sister) of\s+$", before, re.I)
            if kin_of:  # "Melbrigði, the son of Aðakán": a parent or kin, not a place
                person(nm, "nämnd", clause=ci)
                continue
            of_place = re.search(r"\bof\s+$", before) and PLACE_END.search(nm)
            if (PREP.search(before) or of_place) and not re.match(r"'s\b", clause[pos + len(nm):]) \
                    and not re.search(r"memory of\s+$|of\s+(?:his|her|their)\s+$", before, re.I):
                places.append({"name": nm, "key": fold(nm)})
                continue
            after = clause[pos + len(nm):]
            rel = None
            m = re.match(rf",?\s*(?:(?:his|her|their|and \w+'s)\s+)(?:\w+\s+){{0,2}}?({REL})\b", after, re.I)
            if m:
                rel = m.group(1).lower()
            else:
                m = re.search(rf"\b(?:his|her|their)\s+(?:\w+\s+)?({REL})\s+$", before, re.I)
                if m:
                    rel = m.group(1).lower()
            if re.match(r"'s\b", after):  # a name in the genitive (Sigríðr's son, Þóra's freedman) is kin, never a raiser
                p = person(nm, "nämnd", clause=ci)
            elif re.search(r"\bbut\s+$", before) and re.match(r"\s+made\b", after):  # en Gautr gerði: but Gautr made
                p = person(nm, "ristare", clause=ci)
            elif mem and pos > mem.start():
                p = person(nm, "minnes", rel, ci)
            elif carve and not mem and (not verb or carve.start() <= verb.start() or pos < carve.start()):
                p = person(nm, "ristare", clause=ci)
            elif (verb and pos < verb.start()) or (mem and pos < mem.start()):  # "Geiri, Guði … in memory of their brothers"
                p = person(nm, "resare", clause=ci)
            else:
                p = person(nm, "nämnd", rel, ci)
            pm = re.match(rf",?\s*({NAME})'s\s+({REL})\b", after)
            if pm and _is_marked(pm.group(1), marked):
                r_ = pm.group(2).lower()
                if r_ in ("son", "sons", "daughter", "daughters"):  # "X, Y's son": Y is X's father or mother
                    facts.append((fold(pm.group(1)), "förälder till", p["key"]))
                else:  # "Manni, Myskja's brother": Manni is Myskja's brother
                    facts.append((p["key"], r_, fold(pm.group(1))))
                person(pm.group(1), "nämnd", clause=ci)
    for p in persons:
        if p["role"] == "minnes" and p.get("rel"):
            for r in persons:  # the raisers of the same clause: p is r's <rel> (Ketill is Gautr's son)
                if r["role"] == "resare" and r["clause"] == p["clause"]:
                    facts.append((p["key"], p["rel"], r["key"]))
    return {"signum": rec["signum"], "persons": persons, "places": places, "events": sorted(events), "facts": facts}
