"""Människorna på runstenarna: vem reste stenen, efter vem, i vilken relation och av vilket kön, en rad per sten, för
r/people.R. Personerna och relationerna kommer ur länkmodellens extraktion (src/entities.py); könet bestäms här.

Könet för en person bestäms i den här ordningen:
1. Relationen: den som är ”his mother”, ”her daughter” … är kvinna, ”son”, ”father”, ”brother” … man.
2. En ensam resare i sin formel: ”in memory of X, her son” ger kvinna, ”his son” man; den som reser efter sin make
   (husband, husbandman) är kvinna, efter sin hustru (wife) man.
3. Namnet, med ett lexikon som byggs ur steg 1–2 på alla runstenar (ett namn är kvinnligt om det oftare är det).
4. Namnets ändelse: kvinnonamn slutar på -laug, -hildr, -fríðr, -gerðr, -dís … eller -a; mansnamn på -r, -i, -n, -l.
Annars okänt. Samma ordning som i artikeln om kvinnorna (utdata/blogg/build/kvinnor.py), här på entitetsmodellens
personer i stället för på texten före verbet. Kontrolleras mot en handkodning (data/people_check.json).

Relationen anges från resarens håll (”his father” = den döde är resarens far) och grupperas: barn, förälder, syskon,
make/maka, annan släkt, utan släkt (partner, lord …) och ingen angiven. Beröm läses på stenen (drengr, þegn, god/bäst),
och tillhör den döde."""
from __future__ import annotations

import re
from collections import Counter

from src import entities

CHILD = {"son", "sons", "daughter", "daughters", "stepson", "foster-son", "godson"}
PARENT = {"father", "mother", "stepfather", "stepmother", "foster-father", "foster-mother"}
SIBLING = {"brother", "brothers", "sister", "sisters", "foster-brother"}
SPOUSE = {"husband", "husbandman", "wife", "housewife"}
KIN = {"kinsman", "kinsmen", "uncle", "nephew", "grandfather", "grandson", "grandmother", "father-in-law",
       "mother-in-law", "son-in-law", "daughter-in-law", "brother-in-law", "niece", "aunt"}
NONKIN = {"partner", "comrade", "master", "lord", "freedman", "retainer", "friend", "godfather"}  # not "heir": it does not say who the dead was
GROUPS = (("barn", CHILD), ("foralder", PARENT), ("syskon", SIBLING), ("make", SPOUSE), ("slakt", KIN), ("ej_slakt", NONKIN))
MALE_REL = (CHILD | PARENT | SIBLING | SPOUSE | KIN | NONKIN) - entities.FEMALE

FEM_END = re.compile(r"(laug|hildr|borg|bjôrg|björg|fríðr|friðr|ríðr|gerðr|gærðr|dís|rún|ný|heiðr|vé|ví|þrúðr|gunnr|unnr|"
                     r"veig|elfr|vôr)$|a$", re.I)
MAL_END = re.compile(r"(r|i|n|l)$", re.I)

DRENGR = re.compile(r"\bdrengr|\bvaliant man|\bvaliant men|\bdreng\b", re.I)
THEGN = re.compile(r"\bþegn|\bthegn", re.I)
GOOD = re.compile(r"\b(?:good|best)\b(?! (?:god|god's))", re.I)
# "his father", "her ... father", "his/her son", "their good father": a possessive with the raiser's relation anywhere in
# the text, with up to two words or a lacuna between; a compound ("his brother's son") is the compound, not the first word
TEXT_REL = re.compile(rf"\b(?:his|her|their)(?:/(?:his|her|their))?\s+(?:(?:\w+|\.\.\.|…)\s+){{0,2}}?({entities.REL})\b(?!'s)", re.I)
SELF = re.compile(r"in memory of (?:him|her|them)sel(?:f|ves)|in (?:his|her|their) (?:own )?lifetime", re.I)


def _clauses(t: str) -> list[str]:
    t = re.sub(r"§[A-Z]+\s*", ". ", t or "")
    return [c for c in re.split(r"[.;]", t) if c.strip()]


def _poss(clause: str) -> set[str]:
    """Possessiven i en minnesformel: 'in memory of X, her son' / 'in memory of her son'."""
    return {m.lower() for m in re.findall(r"in (?:memory|remembrance) of\b[^.;]*?\b(his|her|their)\b", clause, re.I)}


def _text_genders(rec: dict) -> dict[str, str]:
    """Kön ur texten själv (steg 1–2): {namn: 'k'|'m'}."""
    out: dict[str, str] = {}
    x = entities.extract(rec)
    t = rec.get("translation_en") or ""
    for p in x["persons"]:
        rel = p.get("rel")
        if p["role"] == "minnes" and rel:
            if rel in entities.FEMALE:
                out[p["name"]] = "k"
            elif rel in MALE_REL:
                out[p["name"]] = "m"
    raisers = [p for p in x["persons"] if p["role"] == "resare"]
    for c in _clauses(t):
        in_clause = [p for p in raisers if p["name"] in c]
        if len(in_clause) != 1 or not re.search(r"in (?:memory|remembrance) of", c, re.I):
            continue
        name, poss = in_clause[0]["name"], _poss(c)
        rels = {p.get("rel") for p in x["persons"] if p["role"] == "minnes" and p["name"] in c}
        if poss == {"her"} or rels & {"husband", "husbandman"}:
            out.setdefault(name, "k")
        elif poss == {"his"} or "wife" in rels:
            out.setdefault(name, "m")
    return out


def lexicon(inscriptions: list[dict]) -> dict[str, str]:
    """Namnens kön ur texterna (steg 1–2) på alla runstenar: det vanligaste könet per namn."""
    votes: dict[str, Counter] = {}
    for rec in inscriptions:
        if "runsten" not in (rec.get("object") or "").lower():
            continue
        for n, g in _text_genders(rec).items():
            votes.setdefault(n, Counter())[g] += 1
    return {n: c.most_common(1)[0][0] for n, c in votes.items() if len(c) == 1 or c.most_common(2)[0][1] > c.most_common(2)[1][1]}


def gender(name: str, text: dict[str, str], lex: dict[str, str]) -> str:
    if name in text:
        return text[name]
    if name in lex:
        return lex[name]
    if FEM_END.search(name):
        return "k"
    if MAL_END.search(name):
        return "m"
    return "?"


def stone(rec: dict, lex: dict[str, str]) -> dict:
    x = entities.extract(rec)
    t = rec.get("translation_en") or ""
    text = _text_genders(rec)
    raisers = [p for p in x["persons"] if p["role"] == "resare"]
    dead = [p for p in x["persons"] if p["role"] == "minnes"]
    rg = [gender(p["name"], text, lex) for p in raisers]
    dg = [("k" if p.get("rel") in entities.FEMALE else "m" if p.get("rel") in MALE_REL else gender(p["name"], text, lex))
          for p in dead]
    rels = {p.get("rel") for p in dead}
    # a relation without a name ("in memory of their father", "(their) good father") is still a relation
    rels |= {m.lower() for m in TEXT_REL.findall(re.sub(r"[()]", "", t))}
    # "Guðfastr, Brúni's father" when Brúni is one of the raisers
    for p in raisers:
        rels |= {m.lower() for m in re.findall(rf"{re.escape(p['name'])}'s ({entities.REL})\b(?!'s)", t)}
    row = {"signum": rec["signum"], "legible": int(bool(t.strip())), "n_resare": len(raisers),
           "resare_k": rg.count("k"), "resare_m": rg.count("m"), "resare_okand": rg.count("?"),
           "n_doda": len(dead), "doda_k": dg.count("k"), "doda_m": dg.count("m"), "doda_okand": dg.count("?"),
           "rel_ingen": int(bool(dead) and not (rels - {None})),
           "egen": int(bool(SELF.search(t))), "drengr": int(bool(DRENGR.search(t))), "thegn": int(bool(THEGN.search(t))),
           "god": int(bool(GOOD.search(t)))}
    for g, members in GROUPS:
        row[f"rel_{g}"] = int(bool(rels & members))
    return row


def rows(inscriptions: list[dict]) -> list[dict]:
    """En rad per vikingatida runsten, med landsdel och budskapet 'dog utanför Norden' ur src/messages.py."""
    from src import messages
    lex = lexicon(inscriptions)
    msg = {m["signum"]: m for m in messages.rows(inscriptions)}
    out = []
    for r in inscriptions:
        if r.get("period") != "V" or "runsten" not in (r.get("object") or "").lower():
            continue
        row = stone(r, lex)
        m = msg.get(r["signum"], {})
        row["region"], row["dod_borta"] = m.get("region", ""), m.get("msg_dod_borta")
        out.append(row)
    return out
