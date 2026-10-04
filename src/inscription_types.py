"""Inskrifternas syfte och innehåll – kategorier per inskrift och per ristare.

Kategorierna sätts med regler på Rundatas normalisering, översättning och translitterering och kan
överlappa (en minnessten kan också vara ett brobygge med kristen bön). De är en grov katalogisering för
att se mönster, inte en tolkning av varje inskrift.

För varje ristare med minst fem säkra vikingatida inskrifter jämförs andelen i varje kategori med
genomsnittet för alla vikingatida runstenar med text (tvåsidigt binomialtest). p-värdena justeras för
antalet test med Benjamini–Hochberg (q). När en ristare saknar en kategori anges sannolikheten att få noll
av en slump om ristaren följde genomsnittet: (1 − basnivå)^n.
"""
from __future__ import annotations

import re

from scipy.stats import binomtest

# key -> (label, definition, regex on normalization, regex on English translation, regex on transliteration)
CATEGORIES: dict[str, tuple[str, str, str | None, str | None, str | None]] = {
    "minne": ("Minnesinskrift", "Rest eller huggen till minne av någon (\"æftiR\", \"in memory of\").",
              r"\bæftiR\b", r"in memory of|in remembrance", None),
    "sjalvminne": ("Självminne", "Rest av någon till minne av sig själv eller medan hen levde.",
                   r"\bkvikr\b|\bkvikkiR\b|sialfan|sialfa", r"\balive\b|in memory of (him|her|them)sel", None),
    "bro_vag": ("Bro- och vägbygge", "Nämner en bro, väg eller stig som byggts (ofta en kristen själagåva).",
                r"\bbro\b|\bbru\b|\bbrú|\bveg\b|\bvegR\b", r"\bbridge|causeway|\broad\b|\bpath\b", None),
    "kristen": ("Kristen bön eller formel", "Bön eller kristen formel, t.ex. Guð hjalpi and hans, Guðs móðir.",
                r"\bGuð\b|\bKrist", r"\bGod\b|\bChrist|\bholy\b", None),
    "fard": ("Utlandsfärd", "Nämner resa, död eller strid utomlands (England, Grekland, Ingvarståget, österut).",
             r"Ænglandi|Grikk|Langbarð|Særk|Ingvar|Holmgarð|Garðum|Virlandi|Lifland|Jórsal|\baustr\b|\bvestr\b",
             r"England|Greece|Ingvar|Langobard|Serkland|Gardar|Holmgard|Estonia|Livonia|Jerusalem|in the east|in the west|abroad",
             None),
    "arv": ("Arv och ägande", "Uppgifter om arv, ägande eller gård (owned, inherited, heir).",
            r"\barfi\b|\berfi|\bærfi", r"\bowned\b|inherit|\bheir", None),
    "ting": ("Ting och offentlighet", "Tingsplats eller offentligt åtagande (þing, assembly).",
             r"\bþing", r"assembly|thing-place", None),
    "magisk": ("Magisk eller rituell", "Åkallan eller rituell formel: Þórr vígi (\"Tor vige\"), vígi þessi kuml, "
               "förbannelser (verði at ræti/argi), futharkrader, alu.",
               r"\bvigi\b|\bræti\b|\brata\b|\bargi\b|\bseiðr|\b(?i:siði)\S*\s+\"?Þorr|\"?Þorr\S*\s+vigi", r"\bThor\b|hallow|wretch|pervert|sorcer|witch|curse",
               r"fuþ[aoᚬ]rk|fuþurk|\balu\b"),
    "grans": ("Gränsmärke", "Markerar en gräns (landamæri). Rundata översätter merki (minnesmärke) med "
              "\"landmark\", vilket inte är en gräns och inte räknas här.",
              r"landamæri", r"\bboundary|\bborder\b", None),
}


def categories(rec: dict) -> list[str]:
    norm, tr, tl = rec.get("normalization") or "", rec.get("translation_en") or "", rec.get("transliteration") or ""
    out = []
    for key, (_, _, rn, rt, rl) in CATEGORIES.items():
        if (rn and re.search(rn, norm)) or (rt and re.search(rt, tr, re.I)) or (rl and re.search(rl, tl)):
            out.append(key)
    return out


def _has_text(rec: dict) -> bool:
    return bool((rec.get("normalization") or "").strip() or (rec.get("translation_en") or "").strip())


def is_runestone_any(rec: dict) -> bool:
    return _is_runestone(rec)


def _is_runestone(rec: dict) -> bool:
    # Runestones and fragments of runestones; coins, rune sticks etc. would distort the base rates
    return rec.get("period") == "V" and "runsten" in (rec.get("object") or "").lower()


def _bh(pvalues: list[float]) -> list[float]:
    """Benjamini–Hochberg-justerade p-värden (q)."""
    n = len(pvalues)
    order = sorted(range(n), key=lambda i: pvalues[i])
    q = [0.0] * n
    prev = 1.0
    for rank in range(n, 0, -1):
        i = order[rank - 1]
        prev = min(prev, pvalues[i] * n / rank)
        q[i] = prev
    return q


def carver_categories(inscriptions: list[dict], certain_carvers, min_inscriptions: int = 5) -> dict:
    texts = [r for r in inscriptions if _is_runestone(r) and _has_text(r)]
    cats = {r["signum"]: categories(r) for r in texts}
    total = len(texts)
    base = {k: sum(k in c for c in cats.values()) / total for k in CATEGORIES}
    by_carver: dict[str, list[str]] = {}
    for r in texts:
        cs = certain_carvers(r)
        if len(cs) == 1:
            by_carver.setdefault(cs[0], []).append(r["signum"])
    rows, tests = [], []
    for carver, signa in by_carver.items():
        n = len(signa)
        if n < min_inscriptions:
            continue
        counts = {}
        for k in CATEGORIES:
            hits = sum(k in cats[s] for s in signa)
            p0 = base[k]
            p = float(binomtest(hits, n, p0).pvalue) if 0 < p0 < 1 else 1.0
            counts[k] = {"k": hits, "share": round(hits / n, 3), "expected": round(p0 * n, 2), "p": p,
                         "p_zero": round((1 - p0) ** n, 4) if hits == 0 else None}
            tests.append((carver, k, p))
        rows.append({"carver": carver, "n": n, "counts": counts})
    qs = _bh([t[2] for t in tests])
    qmap = {(c, k): q for (c, k, _), q in zip(tests, qs)}
    for row in rows:
        for k, v in row["counts"].items():
            v["q"] = round(float(qmap[(row["carver"], k)]), 4)
            v["p"] = round(v["p"], 4)
            exp = v["expected"]
            v["direction"] = ("över" if v["k"] > exp else "under") if v["q"] < 0.05 else "som genomsnittet"
    rows.sort(key=lambda r: -r["n"])
    return {
        "categories": [{"key": k, "label": v[0], "definition": v[1], "base_rate": round(base[k], 4),
                        "count": sum(k in c for c in cats.values())} for k, v in CATEGORIES.items()],
        "n_inscriptions": total, "carvers": rows,
        "method": "Tvåsidigt binomialtest mot andelen bland alla vikingatida runstenar med text; "
                  "q = Benjamini–Hochberg-justerat p över alla ristare och kategorier. p(0) = (1 − basnivå)^n.",
    }


def category_check(rec: dict, carver_row: dict | None, defs: dict) -> dict | None:
    """Stenens kategorier mot ristarens: förekommer stenens typ av inskrift hos ristaren?"""
    if not carver_row:
        return None
    cats = categories(rec)
    if not cats:
        return None
    rows = []
    for k in cats:
        v = carver_row["counts"].get(k)
        if v is None or k == "minne":
            continue
        rows.append({"category": k, "label": defs[k][0], "carver_k": v["k"], "carver_n": carver_row["n"],
                     "share": v["share"], "p_zero": v["p_zero"]})
    # Absence only counts when the carver would be expected to have the type: P(0 by chance) < 5 %
    unusual = [r for r in rows if r["carver_k"] == 0 and (r["p_zero"] or 1) < 0.05]
    parts = []
    for r in rows:
        part = f"{r['label']}: {r['carver_k']} av {r['carver_n']} hos ristaren"
        if r["carver_k"] == 0 and r["p_zero"] is not None:
            part += f" (sannolikheten för 0 av en slump är {round(r['p_zero'] * 100)} %)"
        parts.append(part)
    text = "Stenens typ: " + ", ".join(CATEGORIES[k][0].lower() for k in cats) + "." + (" " + "; ".join(parts) + "." if parts else "")
    if unusual:
        text += " Det är osannolikt att ristaren av en slump saknar " + ", ".join(r["label"].lower() for r in unusual) + "."
    return {"categories": cats, "rows": rows, "fits": None if not rows else not unusual, "text": text.strip()}
