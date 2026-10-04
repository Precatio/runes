"""Språkdrag: fonetisk stil och språkbruk i en inskrift, och ristarens profil.

Dragen läses ur Rundata genom att translitterationen paras ord för ord med normaliseringen (samma
metod som stavningsvarianterna i den ortografiska modellen). Ett drag räknas bara där inskriften har
ordet; annars är det "ej bestämbart". Ristarens profil är fördelningen över dennes säkra inskrifter, och
en sten "stämmer" i ett drag när dess värde är det vanligaste hos ristaren eller förekommer i minst
hälften av ristarens inskrifter med ordet.

Ljudhistoriska drag (fonetisk stil) visar hur ristaren återgav uttalet; språkbruk visar formler och
ordval. Båda påverkas av dialekt, tid och beställare, inte bara av ristaren.
"""
from __future__ import annotations

import re
from collections import Counter

from src.orthography import features

# trait -> (group, label, definition)
TRAITS: dict[str, tuple[str, str, str]] = {
    "ai_sten": ("ljud", "Diftongen ai i 'sten'",
                "Ordet stæinn skrivet med ai/ia (diftongen bevarad i skrift) eller med i/e (monoftongerad, "
                "östnordisk utveckling)."),
    "au_och": ("ljud", "Diftongen au i 'och'",
               "Konjunktionen ok skriven auk (diftong) eller uk/ok/ak (monoftong)."),
    "nasal": ("ljud", "Nasal före konsonant",
              "Om n/m skrivs ut före homorgan konsonant, t.ex. bonta/bunta mot buta (bónda), kumbl mot kubl."),
    "h_bortfall": ("ljud", "h-bortfall",
                   "Om h skrivs i början av ord som hans och hjalpi (hans mot ans, hialbi mot ialbi)."),
    "stungna": ("ljud", "Stungna runor",
                "Om inskriften använder stungna runor (e, g, d, y), som skiljer ljud som den vanliga yngre "
                "futharken inte skiljer på; vanligare under 1000-talets senare del."),
    "efter": ("bruk", "Stavning av 'efter'",
              "Hur æftiR skrivs: första vokalen (a, e, i, u, y) och slutet (-iR, -ir, -R)."),
    "denna": ("bruk", "Stavning av 'denna'",
              "Hur demonstrativet þenna skrivs (þina, þino, þana, þena)."),
    "bon": ("bruk", "Kristen bön",
            "Om inskriften har en bön, t.ex. Guð hjalpi and hans (Gud hjälpe hans själ)."),
    "sjal": ("bruk", "Själsbön",
             "Om bönen nämner själen (and, sál/sálu)."),
    "signatur": ("bruk", "Ristarsignatur",
                 "Om inskriften har en ristarformel (risti, hjó, markaði, rúnaR)."),
    "runor": ("bruk", "Skrivningen av 'runor'",
              "Hur rúnaR skrivs (runaR, runa, runar)."),
}

DOTTED = set("egdy")


def _value(trait: str, variants: dict, norm: str, translit_words: list[str]) -> str | None:
    if trait == "ai_sten":
        w = variants.get("stæin") or variants.get("stæina")
        if not w:
            return None
        return "ai bevarad" if ("ai" in w or "ia" in w or "æi" in w) else "monoftong"
    if trait == "au_och":
        w = variants.get("ok")
        if not w:
            return None
        return "auk" if w.startswith("au") else "monoftong"
    if trait == "nasal":
        w = variants.get("bonda") or variants.get("kumbl")
        if not w:
            return None
        if "bonda" in variants:
            return "skriven" if "n" in w else "utelämnad"
        return "skriven" if "m" in w and "b" in w else "utelämnad"
    if trait == "h_bortfall":
        w = variants.get("hialpi") or variants.get("hans")
        if not w:
            return None
        return "h skrivet" if w.startswith("h") else "h saknas"
    if trait == "stungna":
        letters = set("".join(translit_words))
        return "ja" if letters & DOTTED else "nej"
    if trait == "efter":
        w = variants.get("æftir")
        if not w:
            return None
        end = "-R" if not re.search(r"i[Rr]$", w) and w.endswith("R") else ("-ir" if w.endswith("ir") else "-iR" if w.endswith("iR") else "annat")
        return f"{w[0]}-…{end}"
    if trait == "denna":
        return variants.get("þenna")
    if trait == "runor":
        return variants.get("runar")
    n = norm.lower()
    if trait == "bon":
        return "ja" if ("guð" in n and ("hialpi" in n or "hjalpi" in n)) else "nej"
    if trait == "sjal":
        return "ja" if re.search(r"\b(and|ǫnd|salu|sál|sial)\b", n) else "nej"
    if trait == "signatur":
        return "ja" if re.search(r"\b(risti|ristu|hiogg|hiuggu|markaði|faði|fáði)\b", n) else "nej"
    return None


_cache: dict[tuple[str, int], dict[str, str]] = {}


def traits(rec: dict, names=frozenset()) -> dict[str, str]:
    # Rundata records do not change while the server runs; cache per inscription (and name set)
    key = (rec.get("signum", ""), id(names))
    if key[0] and key in _cache:
        return _cache[key]
    out = _traits(rec, names)
    if key[0]:
        _cache[key] = out
    return out


def _traits(rec: dict, names) -> dict[str, str]:
    f = features(rec, names)
    words = [re.sub(r"[()\[\]{}<>|?/^]", "", t) for t in (rec.get("transliteration") or "").split()]
    norm = rec.get("normalization") or ""
    out = {}
    for t in TRAITS:
        v = _value(t, f["variants"], norm, [w for w in words if w and "-" not in w])
        if v is not None:
            out[t] = v
    # Short texts say nothing about formulas
    if f["n_words"] < 5:
        for t in ("bon", "sjal", "signatur", "stungna"):
            out.pop(t, None)
    return out


def carver_profile(carver: str, inscriptions: list[dict], certain_carvers, names=frozenset(),
                   exclude: str | None = None) -> dict:
    dist: dict[str, Counter] = {t: Counter() for t in TRAITS}
    n = 0
    for r in inscriptions:
        if r["signum"] == exclude or carver not in certain_carvers(r):
            continue
        n += 1
        for t, v in traits(r, names).items():
            dist[t][v] += 1
    return {"carver": carver, "n_inscriptions": n,
            "traits": {t: dict(c.most_common()) for t, c in dist.items() if c}}


def compare(stone: dict[str, str], profile: dict, min_n: int = 3) -> dict:
    rows = []
    for t, v in stone.items():
        dist = profile["traits"].get(t) or {}
        total = sum(dist.values())
        if total < min_n:
            continue
        share = dist.get(v, 0) / total
        top = max(dist, key=dist.get)
        group, label, definition = TRAITS[t]
        rows.append({"trait": t, "group": group, "label": label, "definition": definition, "stone": v,
                     "carver_common": top, "share": round(share, 3), "n": total,
                     "agrees": v == top or share >= 0.5})
    k = sum(r["agrees"] for r in rows)
    text = (f"{k} av {len(rows)} jämförbara språkdrag stämmer med inskrifterna av {profile['carver']}"
            if rows else f"Inga jämförbara språkdrag (för få gemensamma ord med inskrifterna av {profile['carver']})")
    if rows:
        off = [r for r in rows if not r["agrees"]]
        if off:
            text += ". Avviker: " + "; ".join(f"{r['label'].lower()} ({r['stone']}; hos ristaren oftast {r['carver_common']})" for r in off[:4])
    return {"rows": rows, "agree": k, "comparable": len(rows), "text": text + "."}
