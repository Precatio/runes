"""Underlag till utkasten i Månadens fynd som kräver Rundata: en exempelsten med mönstret (krok och foto) och vilka
ristare som står bakom stenarna i ett kluster (utkastets första prövning)."""
from __future__ import annotations

import re
from collections import Counter

from src.research_gaps import PROVINCE_NAMES, is_runestone, province

STYLE_YEARS = {"RAK": (980, 1015), "Fp": (1010, 1050), "Pr1": (1010, 1050), "Pr2": (1020, 1050), "Pr3": (1045, 1075),
               "Pr4": (1070, 1100), "Pr5": (1100, 1130)}


def has_pattern(rec: dict, key: str, feature: dict | None, names) -> bool:
    """Om stenen har mönstret: mönsterkartans drag (pm), eller förändringsanalysens drag med sitt ja-värde."""
    if feature is not None:
        if key == "cross":
            return bool((rec.get("cross_form") or "").strip())
        from src.language_profile import traits
        # The yes value can name several values ("o-runa, båda")
        yes = {v.strip() for v in str(feature.get("yes") or "").split(",") if v.strip()}
        return traits(rec, names).get(key) in yes
    from src.pattern_map import stone_patterns
    return stone_patterns(rec, names).get(key) == 1


def certain_carver(rec: dict) -> str | None:
    cs = [c for c in rec.get("carvers") or [] if c.get("kind") in ("S", "A") and not c.get("uncertain")]
    return cs[0]["name"] if len(cs) == 1 else None


def _clean(norm: str, limit: int = 220) -> str:
    t = re.sub(r"\s+", " ", (norm or "").replace('"', "")).strip()
    if len(t) <= limit:
        return t
    return t[:limit].rsplit(" ", 1)[0].rstrip(",;:") + " …"


def candidates(inscriptions: list[dict], key: str, feature: dict | None, names, signa: list[str] | None = None,
               styles: set[str] | None = None, prov: str | None = None) -> list[dict]:
    """Svenska runstenar med mönstret och läsbar text, i klustret (signa), stilgrupperna eller landskapet; de med en säker
    ristare och en lagom lång text först."""
    allowed = set(signa) if signa else None
    out = []
    for r in inscriptions:
        if allowed is not None and r["signum"] not in allowed:
            continue
        if not is_runestone(r) or (r.get("flags") or {}).get("lost"):
            continue
        if styles and r.get("style") not in styles:
            continue
        if prov and province(r) != prov:
            continue
        n = r.get("normalization") or ""
        if len(n) < 50 or not (r.get("translation_en") or "").strip():
            continue
        if not has_pattern(r, key, feature, names):
            continue
        out.append(r)
    out.sort(key=lambda r: (certain_carver(r) is None, abs(len(r.get("normalization") or "") - 160)))
    return out


def example(recs: list[dict], images: list[dict]) -> dict | None:
    """Den första stenen med ett fritt licensierat foto: signum, plats, datering, ristare, text och fotot."""
    by = {i["signum"]: i for i in images}
    for r in recs:
        img = by.get(r["signum"])
        if not img:
            continue
        years = STYLE_YEARS.get(r.get("style") or "")
        prov = province(r)
        place = r.get("place") or r.get("parish") or ""
        lead_sv = f"{r['signum']} vid {place} i {PROVINCE_NAMES.get(prov, prov)}."
        lead_en = f"{r['signum']} at {place} in {PROVINCE_NAMES.get(prov, prov)}."
        return {"signum": r["signum"], "place": place, "province": PROVINCE_NAMES.get(prov, prov),
                "style": r.get("style"), "years": years, "carver": certain_carver(r),
                "normalization": _clean(r.get("normalization") or ""), "translation_en": _clean(r.get("translation_en") or "", 260),
                "picture": img["markdown"].replace(f"\n{r['signum']}. ", f"\n{lead_sv} ", 1),
                "picture_en": img["markdown_en"].replace(f"\n{r['signum']}. ", f"\n{lead_en} ", 1)}
    return None


def carver_mix(inscriptions: list[dict], signa: list[str], key: str, feature: dict | None, names) -> dict:
    """Ristarna bakom stenarna med mönstret bland signa: hur många har en säker ristare, hur många ristare och hur stor
    del den vanligaste står för."""
    allowed = set(signa)
    recs = [r for r in inscriptions if r["signum"] in allowed and has_pattern(r, key, feature, names)]
    carvers = Counter(c for r in recs if (c := certain_carver(r)))
    top = carvers.most_common(1)
    return {"n": len(recs), "with_carver": sum(carvers.values()), "carvers": len(carvers),
            "top": top[0][0] if top else None, "top_n": top[0][1] if top else 0}
