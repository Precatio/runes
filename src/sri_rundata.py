"""Rundata och SRI säger olika: stenar där fyndhistoriken i Sveriges runinskrifter inte stämmer med Rundata.

SRI:s fyndhistorik (src/sri_fyndhistorik.py, A1 tillägg 1, noterna 1–9) ställs mot Rundata och appens flyttregel
(src/r_bridge.is_moved), för svenska vikingatida runstenar. Bara de fältgrupper som klarade granskningen används:
läget när bandet skrevs och försvunnen/återfunnen. Fyra slags oenighet:

  SRI flyttad, Rundata på plats   SRI:s läge är "flyttad", men Rundatas placering anger ingen flytt, så flyttregeln
                                  räknar stenen som stående på sin plats
  SRI på plats, Rundata flyttad   SRI:s läge är "ursprunglig plats", men flyttregeln räknar stenen som flyttad
  SRI försvunnen, Rundata finns   SRI säger att stenen var försvunnen när bandet skrevs och nämner ingen återfinning,
                                  men Rundata anger inte stenen som försvunnen
  SRI finns, Rundata försvunnen   SRI beskriver stenen som bevarad, men Rundata anger den som försvunnen

Det är en jämförelse, inget prov: banden skrevs 1900–1981 och Rundata är från 2018, så en del oenighet är
verkliga händelser efter bandet (en sten som flyttats, hittats eller försvunnit sedan). Listan är ett förslag att
granska; is_moved ändras inte (A1 tillägg 1, "Vad som inte får göras"), och inga tal här används i någon beräkning.
Runor 2020:s uppgift om ursprunglig plats visas bredvid som en tredje källa där den finns.
"""
from __future__ import annotations

from collections import Counter

KINDS = {
    "sri_flyttad": ("SRI flyttad, Rundata på plats",
                    "SRI säger att stenen var flyttad när bandet skrevs, men Rundatas placering anger ingen flytt, så appens "
                    "flyttregel räknar den som stående på sin plats. Platsstudierna (lerkanten, vägen, gravfälten) räknar "
                    "den då som rest där den står."),
    "rundata_flyttad": ("SRI på plats, Rundata flyttad",
                        "SRI säger att stenen stod på sin ursprungliga plats, men Rundatas placering pekar på en flytt. "
                        "Stenen kan ha flyttats efter att bandet skrevs."),
    "sri_forsvunnen": ("SRI försvunnen, Rundata finns",
                       "SRI säger att stenen var försvunnen när bandet skrevs och nämner ingen återfinning, men Rundata "
                       "anger den inte som försvunnen. Den kan ha hittats igen efter utgåvan."),
    "rundata_forsvunnen": ("SRI finns, Rundata försvunnen",
                           "SRI beskriver stenen som bevarad, men Rundata anger den som försvunnen. Den kan ha försvunnit "
                           "efter utgåvan."),
}


def _rundata_text(r: dict) -> str:
    parts = [r.get("place") or ""]
    if r.get("placement"):
        parts.append(f"placering: {r['placement']}")
    return "; ".join(p for p in parts if p) or "–"


def disagreements(inscriptions: list[dict]) -> dict:
    """Stenarna där SRI och Rundata säger olika, med SRI:s sida och korta citat, och antalen per slag och landskap."""
    from src import research_gaps as gaps, runor, sri_fyndhistorik
    from src.r_bridge import is_moved
    if not sri_fyndhistorik.available():
        return {"available": False, "rows": [], "counts": {}, "kinds": {k: v[0] for k, v in KINDS.items()},
                "note": "SRI:s fyndhistorik finns inte på den här datorn (/Volumes/2TB/Antigrvity/Runes/downloads/sri_fakta)."}
    rows, compared, per_prov = [], Counter(), Counter()
    has_runor = runor.available()
    for r in inscriptions:
        if not gaps.is_runestone(r):
            continue
        s = sri_fyndhistorik.for_inscription(r)
        if not s:
            continue
        prov = gaps.province(r)
        compared["stenar"] += 1
        per_prov[prov] += 1
        pos = s.get("position") or {}
        lost = s.get("lost") or {}
        moved = bool(is_moved(r))
        rd_lost = bool((r.get("flags") or {}).get("lost"))
        kinds = []
        if pos.get("value") == "flyttad" and not moved:
            kinds.append(("sri_flyttad", pos))
        elif pos.get("value") == "ursprunglig plats" and moved:
            kinds.append(("rundata_flyttad", pos))
        if lost.get("lost_at_edition") and not rd_lost and not s.get("refound"):
            kinds.append(("sri_forsvunnen", {"value": "försvunnen", "page": lost.get("page"), "quote": lost.get("quote")}))
        elif not lost.get("lost_at_edition") and pos.get("value") != "försvunnen" and rd_lost:
            kinds.append(("rundata_forsvunnen", {"value": "bevarad", "page": pos.get("page"), "quote": pos.get("quote")}))
        if not kinds:
            continue
        from src import redan_kant
        article = redan_kant.sri_for(r["signum"]) or {}
        ru = runor.for_inscription(r) if has_runor else None
        orig = (ru or {}).get("original_location")
        for kind, ev in kinds:
            rows.append({
                "signum": r["signum"], "place": r.get("place"), "province": prov, "kind": kind, "label": KINDS[kind][0],
                "sri": {"value": ev.get("value"), "page": ev.get("page"), "quote": ev.get("quote"),
                        "volume": s.get("volume"), "year": s.get("year"), "url": s.get("url"),
                        "article_pages": (article.get("pages") or [])[:3]},
                "rundata": {"text": _rundata_text(r), "moved_rule": moved, "lost": rd_lost},
                "runor_original": None if orig is None else bool(orig),
            })
    counts = Counter(x["kind"] for x in rows)
    by_prov: dict[str, dict] = {}
    for x in rows:
        by_prov.setdefault(x["province"], {"name": gaps.PROVINCE_NAMES.get(x["province"], x["province"]),
                                           "compared": per_prov[x["province"]], **{k: 0 for k in KINDS}})[x["kind"]] += 1
    rows.sort(key=lambda x: (list(KINDS).index(x["kind"]), x["province"], x["signum"]))
    return {"available": True, "n_compared": compared["stenar"], "counts": {k: counts.get(k, 0) for k in KINDS},
            "kinds": {k: {"label": v[0], "help": v[1]} for k, v in KINDS.items()}, "per_province": by_prov,
            "rows": rows, "method": sri_fyndhistorik.METOD}
