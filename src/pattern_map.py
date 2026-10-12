"""Mönsterkartan: för varje svensk vikingatida runsten plats, stilgruppens mittår och om den har varje mönster
(GET /api/research/pattern-map; web/src/components/PatternMap.tsx).

Varje mönster är 1 (stenen har det), 0 (saknar det) eller None (kan inte avgöras, t.ex. oläslig text). Kartan visar
andelen stenar med mönstret per område, så att tätheten av runstenar i Uppland inte döljer mönstret.

Tro: kristna markörer är kors eller kristen bön eller formel. Hedniska eller rituella markörer är Torsåkallan (Þórr i
normaliseringen, Thor i Rundatas översättning), vígi-formler, förbannelser, alu och Tormotiv i Rundatas anmärkningar
(torshammare, Tors fiskafänge). Futharkrader räknas inte (de förekommer också i kristna sammanhang), och inte heller
Sigurdsbilder (hjältesagan används också i kristen konst). En sten utan kristna markörer är inte därmed hednisk; den
gruppen redovisas för sig som "utan religiösa markörer".
"""
from __future__ import annotations

import re

from src.inscription_types import categories
from src.language_profile import traits
from src.research_gaps import is_runestone, province
from src.styles import BY_CODE

# Gudens namn, inte namn på Þór- (Þorkell, Þori, avbrutna Þor...): dubbelt r och inget som fortsätter ordet
THOR = re.compile(r"(?<![\wÞþ])Þ[oó]rr(?![\wÞþ\[]|\.\.)")
RITUAL = re.compile(r"\bvigi\b|\bræti\b|\bargi\b|\bseiðr")
ALU = re.compile(r"\balu\b")
RITUAL_EN = re.compile(r"\bThor\b|\bhallow|\bwretch|\bpervert|\bsorcer|\bwitch|\bcurse")
THOR_MOTIF = re.compile(r"torshammar|tors fiskafänge|torsmask", re.I)

# key, label, group, help
PATTERNS = [
    ("kristen", "Kristna markörer", "Tro", "Kors eller kristen bön eller formel."),
    ("hednisk", "Hedniska eller rituella markörer", "Tro",
     "Torsåkallan, vígi-formler, förbannelser, alu eller Tormotiv (torshammare, Tors fiskafänge). Få stenar."),
    ("neutral", "Utan religiösa markörer", "Tro",
     "Varken kristna eller hedniska markörer. En sten utan kristna markörer är inte därmed hednisk."),
    ("bon", "Kristen bön", "Tro", "Bön som Guð hjalpi and hans (stenar med läsbar text)."),
    ("sjal", "Själsbön", "Tro", "Bön som nämner själen."),
    ("kors", "Kors", "Tro", "Kors i ornamentiken enligt Rundata."),
    ("stungna", "Stungna runor", "Skrift", "Stungna runor (e, g, d, y) i inskriften."),
    ("monoftong", "Monoftong (stin)", "Skrift", "Monoftong i något ai-ord, t.ex. stin för stain."),
    ("o_runa", "o-runan för o", "Skrift", "o-ljudet skrivet med o-runan (ᚬ) i stället för u-runan."),
    ("r_for_R", "r för ʀ", "Skrift", "ʀ skrivet med r-runan i ord som æftiʀ."),
    ("signatur", "Ristarsignatur", "Skrift", "Ristarformel, t.ex. risti, hjó."),
    ("bro", "Bro- och vägbygge", "Innehåll", "Nämner en bro eller väg som byggts."),
    ("fard", "Utlandsfärd", "Innehåll", "Nämner resa, död eller strid utomlands."),
    ("arv", "Arv och ägande", "Innehåll", "Uppgifter om arv, ägande eller gård."),
]


def _yes(value: str | None, yes: set[str], no: set[str]) -> int | None:
    if value in yes:
        return 1
    if value in no:
        return 0
    return None


def pagan(rec: dict) -> bool:
    norm = (rec.get("normalization") or "") + " " + (rec.get("normalization_ows") or "")
    return bool(THOR.search(norm) or RITUAL.search(norm) or ALU.search(rec.get("transliteration") or "")
                or RITUAL_EN.search(rec.get("translation_en") or "") or THOR_MOTIF.search(rec.get("other") or ""))


def stone_patterns(rec: dict, names) -> dict[str, int | None]:
    """Mönstren för en sten: 1, 0 eller None."""
    norm = (rec.get("normalization") or "") + " " + (rec.get("normalization_ows") or "")
    legible = bool(norm.strip())
    cats = set(categories(rec))
    t = traits(rec, names)
    cross = bool((rec.get("cross_form") or "").strip())
    christian = cross or "kristen" in cats
    heathen = pagan(rec)
    known = legible or cross
    return {
        "kristen": 1 if christian else (0 if known else None),
        "hednisk": 1 if heathen else (0 if legible else None),
        "neutral": (0 if christian or heathen else 1) if legible else (0 if cross else None),
        "bon": _yes(t.get("bon"), {"ja"}, {"nej"}),
        "sjal": _yes(t.get("sjal"), {"ja"}, {"nej"}),
        "kors": 1 if cross else 0,
        "stungna": _yes(t.get("stungna"), {"ja"}, {"nej"}),
        "monoftong": _yes(t.get("ai_alla"), {"monoftong", "båda"}, {"diftong"}),
        "o_runa": _yes(t.get("o_runa"), {"o-runa", "båda"}, {"u-runa"}),
        "r_for_R": _yes(t.get("r_for_R"), {"r för ʀ", "båda"}, {"ʀ-runa"}),
        "signatur": _yes(t.get("signatur"), {"ja"}, {"nej"}),
        "bro": (1 if "bro_vag" in cats else 0) if legible else None,
        "fard": (1 if "fard" in cats else 0) if legible else None,
        "arv": (1 if "arv" in cats else 0) if legible else None,
    }


def mid_year(rec: dict) -> int | None:
    st = BY_CODE.get(rec.get("style") or "")
    if not st or rec.get("style_uncertain") or not st.get("from"):
        return None
    return round((st["from"] + st["to"]) / 2)


def build(inscriptions: list[dict], names) -> dict:
    """Mönstren och stenarna; stenens värden (v) står i samma ordning som mönstren, för att svaret ska bli mindre."""
    stones, keys = [], [k for k, *_ in PATTERNS]
    for r in inscriptions:
        if not is_runestone(r) or r.get("lat") is None:
            continue
        v = stone_patterns(r, names)
        stones.append({"s": r["signum"], "lat": round(r["lat"], 4), "lon": round(r["lon"], 4), "p": province(r),
                       "y": mid_year(r), "v": [v[k] for k in keys]})
    return {"patterns": [{"key": k, "label": l, "group": g, "help": h} for k, l, g, h in PATTERNS], "stones": stones}
