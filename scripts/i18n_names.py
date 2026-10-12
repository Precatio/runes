"""Namn och termer för översättningen: ristare och orter ur Rundata (web/src/i18n/names.json), som lämnas orörda,
och termer som översätts var för sig inne i meningar (web/src/i18n/terms.json): språkdragen och deras värden och
bergarterna i Rundata.

Översättningen i webbläsaren (web/src/i18n/core.ts) slår upp meningar som mallar; ristarnamn, orter, socknar, härader,
kommuner och landskap byts mot platshållare före uppslaget och sätts tillbaka efteråt. Kör om när Rundata uppdateras:

    .venv/bin/python scripts/i18n_names.py
"""
from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.rundata import store  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web", "src", "i18n", "names.json")
TERMS = os.path.join(os.path.dirname(OUT), "terms.json")

# Names that are also ordinary Swedish words or terms in the app's own text; they are translated, not kept
STOP = {"Bro", "Ed", "By", "Hus", "Sten", "Mot", "Ön", "Berg", "Kyrka", "Kyrkan", "Vik", "Ås", "Näs", "Sund", "Torp",
        "Holm", "Lund", "Hov", "Mo", "Ö", "Sjö", "Backe", "Hög", "Gård", "Ny", "Runsten", "Okänd", "Okänt", "Ristare",
        "Vi", "Mark", "Dal", "Åker", "Bo", "Fors", "Kil", "Kyrkogården", "Kyrkogård", "Gamla", "Övre", "Nedre", "Norra", "Södra", "Västra", "Östra", "Stora", "Lilla",
        "Prästgården", "Prästgård", "Skolan", "Torget", "Stationen", "Museet", "Okänd ristare", "Samma", "Vid", "Under"}
PROVINCES = ["Uppland", "Södermanland", "Östergötland", "Västergötland", "Småland", "Öland", "Gotland", "Gästrikland",
             "Hälsingland", "Västmanland", "Närke", "Medelpad", "Ångermanland", "Dalarna", "Härjedalen", "Jämtland",
             "Lappland", "Värmland", "Dalsland", "Bohuslän", "Halland", "Skåne", "Blekinge", "Mälardalen", "Götaland",
             "Svealand", "Norrland"]


def main() -> None:
    names: set[str] = set(PROVINCES)
    for r in store().inscriptions:
        for c in r.get("carvers") or []:
            names.add(c["name"])
        for key in ("place", "parish", "district", "municipality"):
            v = (r.get(key) or "").strip()
            if not v:
                continue
            # "Villberga sn", "Trögds hd": only the name, so that the abbreviation is translated (sn → parish)
            base = re.sub(r"\s+(sn|hd|socken|härad|kn|stad|kommun)\.?$", "", v)
            names.add(base)
            # "Trögds" is the genitive form; the plain form is also used in the app's texts
            if key == "district" and base.endswith("s"):
                names.add(base[:-1])
    names = {n for n in names if n and n not in STOP and len(n) > 1 and not re.search(r"[?()\[\]{}]", n)
             and re.match(r"^\w", n)}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(sorted(names), fh, ensure_ascii=False, indent=0)
    print(f"{len(names)} namn → {OUT}")
    terms = sorted(build_terms())
    with open(TERMS, "w", encoding="utf-8") as fh:
        json.dump(terms, fh, ensure_ascii=False, indent=0)
    print(f"{len(terms)} termer → {TERMS}")


def build_terms() -> set[str]:
    """Språkdragens namn (med liten och stor bokstav, som i listor och rubriker), deras värden och Rundatas
    materialuppgifter. Värden i runtext (þino, i-…-iR) är också termer: de står i katalogen som sig själva."""
    from api.routers.orthography import model
    from src.language_profile import TRAITS, traits
    out: set[str] = set()
    for _, label, _ in TRAITS.values():
        out |= {label, label[:1].lower() + label[1:]}
    # The pattern map's patterns and the kinds of place, which the scan and the clusters put into sentences
    from src.pattern_map import PATTERNS
    from src.places import KINDS
    for _, label, *_ in list(PATTERNS) + list(KINDS):
        out |= {label, label[:1].lower() + label[1:]}
    names = model().names
    for r in store().inscriptions:
        out |= {v for v in traits(r, names).values() if v and len(v) > 1}
        m = (r.get("material") or "").strip()
        if m and len(m) > 2:
            out |= {m, m[:1].upper() + m[1:]}
    return {t for t in out if not re.fullmatch(r"[\d\W]+", t)}


if __name__ == "__main__":
    main()
