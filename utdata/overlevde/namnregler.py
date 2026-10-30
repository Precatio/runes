"""Reglerna som översätter ett runnamn till nutida svensk form (utdata/overlevde/namn.py och
utdata/namn_utanfor/). extra=True ger känslighetsprovets á → a och f → v."""
import re
import unicodedata


def fold(n):
    s_ = unicodedata.normalize("NFKD", n.replace("Þ", "Th").replace("þ", "th").replace("ð", "d").replace("ô", "o")
                               .replace("æ", "ae").replace("ø", "o"))
    return re.sub(r"[^a-z]", "", "".join(ch for ch in s_ if not unicodedata.combining(ch)).lower())


def _translit(n, a_long="å"):
    t = n
    for a, b in (("Þ", "T"), ("þ", "t"), ("ð", "d"), ("ô", "å"), ("Ó", "O"), ("ó", "o"), ("Á", a_long.upper()),
                 ("á", a_long), ("Æ", "Ä"), ("æ", "ä"), ("ø", "ö"), ("ey", "ö"), ("Ey", "Ö"), ("ei", "e"), ("Ei", "E"),
                 ("au", "ö"), ("Au", "Ö"), ("í", "i"), ("Í", "I"), ("ú", "u"), ("Ú", "U"), ("ý", "y"), ("é", "e"),
                 ("É", "E")):
        t = t.replace(a, b)
    t = re.sub(r"rr$", "r", t)
    t = re.sub(r"([^aeiouyåäöAEIOUYÅÄÖr])r$", r"\1", t)
    return re.sub(r"nn$", "n", t)


def rules(n, sex="?", extra=False):
    t = _translit(n)
    out = {t}
    # Old Norse weak masculines end in -i where Swedish has -e (Helgi → Helge, Áki → Åke, Kári → Kåre). Added
    # 2026-10-30 after Viktor asked about Helge; not in the locked plan (resultat.md, Avvikelser). Men only: for women
    # -a → -e gives men's names (Helga → Helge, Þóra → Tore).
    if sex == "m" and t.endswith("i"):
        out.add(t[:-1] + "e")
    for a, b in (("ä", "e"), ("å", "o"), ("o", "å")):
        out |= {x.replace(a, b) for x in list(out)}
    if extra:  # á as a (Ástríðr → Astrid) and f as v (Tófa → Tova), on the name itself, not chained
        alt = _translit(n, "a")
        out |= {alt, alt.replace("f", "v"), t.replace("f", "v")}
    return {x[:1].upper() + x[1:] for x in out if x}
