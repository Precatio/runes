"""Uppslag och sökning i Samnordisk runtextdatabas (data/rundata.json).

Filen byggs med `python -m scripts.build_rundata`.
"""
import json
import os
import re
from collections import Counter
from functools import lru_cache
from typing import Optional

from fastapi import HTTPException

from src import research_gaps as gaps
from src.signum import fold_signum

# Filters with the same definitions as the research-gaps overview (Swedish Viking Age runestones)
GAP_FILTERS = {
    "runestone": gaps.is_runestone,
    "carver": lambda r: gaps.is_runestone(r) and gaps.has_carver(r),
    "no_carver": lambda r: gaps.is_runestone(r) and not gaps.has_carver(r),
    "style": lambda r: gaps.is_runestone(r) and gaps.has_style(r),
    "no_style": lambda r: gaps.is_runestone(r) and not gaps.has_style(r),
    "dated": lambda r: gaps.is_runestone(r) and gaps.is_dated_by_year(r),
    "uncertain_interpretation": lambda r: gaps.is_runestone(r) and gaps.uncertain_interpretation(r),
    "lost": lambda r: gaps.is_runestone(r) and r["flags"]["lost"],
}

DATA_PATH = os.environ.get(
    "RUNDATA_PATH",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "rundata.json"),
)

SIGNUM_IN_TEXT_RE = re.compile(
    r"(?<![A-Za-zÅÄÖåäö])(U|Sö|So|Ög|Og|Öl|Ol|Vg|Sm|Gs|Vs|Nä|Na|Hs|M|Ån|An|D|Hr|J|Lp|Ds|Bo|G|DR|N|IS|IM|E|GR|Or)"
    r"[\s_]?(\d{1,4})(?![\d])"
)


class RundataStore:
    def __init__(self, data: dict):
        self.meta = data["meta"]
        self.inscriptions: list[dict] = data["inscriptions"]
        self.by_key: dict[str, dict] = {}
        for rec in self.inscriptions:
            self.by_key.setdefault(fold_signum(rec["signum"]), rec)
        for alias, target in data.get("aliases", {}).items():
            rec = self.by_key.get(fold_signum(target))
            if rec:
                self.by_key.setdefault(fold_signum(alias), rec)

    def get(self, signum: str) -> Optional[dict]:
        return self.by_key.get(fold_signum(signum))

    def find_in_text(self, text: str) -> list[dict]:
        """Hittar signum som nämns i fri text (t.ex. ett filnamn eller ett chattmeddelande)."""
        found, seen = [], set()
        for m in SIGNUM_IN_TEXT_RE.finditer(text or ""):
            rec = self.get(f"{m.group(1)} {m.group(2)}")
            if rec and rec["signum"] not in seen:
                seen.add(rec["signum"])
                found.append(rec)
        return found

    def search(self, q: str = "", carver: str = "", style: str = "", period: str = "",
               province: str = "", has_coords: bool = False, limit: int = 50, offset: int = 0,
               gap: str = "", signa: str = ""):
        q_l, carver_l = q.lower().strip(), carver.lower().strip()
        gap_test = GAP_FILTERS.get(gap)
        wanted = {fold_signum(x) for x in signa.split(",") if x.strip()} if signa else None
        results = []
        for rec in self.inscriptions:
            if gap_test and not gap_test(rec):
                continue
            if wanted is not None and fold_signum(rec["signum"]) not in wanted:
                continue
            if has_coords and rec["lat"] is None:
                continue
            if province and rec["signum"].split(" ")[0] != province:
                continue
            if period and rec["period"] != period:
                continue
            if style and rec["style"] != style:
                continue
            if carver_l and not any(carver_l == c["name"].lower() for c in rec["carvers"]):
                continue
            if q_l:
                hay = " ".join((rec["signum"], rec["place"], rec["parish"], rec["transliteration"],
                                rec["normalization"], rec["translation_en"], rec["carver_raw"])).lower()
                if q_l not in hay and fold_signum(q) != fold_signum(rec["signum"]):
                    continue
            results.append(rec)
        return {"total": len(results), "results": results[offset:offset + limit]}

    def carvers(self):
        counts: dict[str, Counter] = {}
        for rec in self.inscriptions:
            for c in rec["carvers"]:
                counts.setdefault(c["name"], Counter())[c["kind"]] += 1
        return sorted(
            ({"name": n, "signed": k["S"], "attributed": k["A"], "pair": k["P"], "similar": k["L"],
              "total": sum(k.values())} for n, k in counts.items()),
            key=lambda x: -x["total"],
        )

    def style_stats(self):
        """Fördelning per stilgrupp (Gräslund): antal, landskap och ristare."""
        stats: dict[str, dict] = {}
        for rec in self.inscriptions:
            st = rec["style"]
            if st not in ("RAK", "Fp", "KB", "Pr1", "Pr2", "Pr3", "Pr4", "Pr5"):
                continue
            s = stats.setdefault(st, {"style": st, "count": 0, "uncertain": 0,
                                      "provinces": Counter(), "carvers": Counter(), "examples": []})
            s["count"] += 1
            s["uncertain"] += int(rec["style_uncertain"])
            s["provinces"][rec["signum"].split(" ")[0]] += 1
            for c in rec["carvers"]:
                if c["kind"] in ("S", "A"):
                    s["carvers"][c["name"]] += 1
            if not rec["style_uncertain"] and rec["image_link"] and len(s["examples"]) < 6:
                s["examples"].append({"signum": rec["signum"], "place": rec["place"], "image_link": rec["image_link"]})
        out = []
        for st in ("RAK", "Fp", "KB", "Pr1", "Pr2", "Pr3", "Pr4", "Pr5"):
            if st in stats:
                s = stats[st]
                s["provinces"] = dict(s["provinces"].most_common(8))
                s["carvers"] = dict(s["carvers"].most_common(8))
                out.append(s)
        return out

    def geo(self):
        """Kompakt lista för kartan: [signum, lat, lon, period, style, ristare (S/A), försvunnen]."""
        return [
            [r["signum"], r["lat"], r["lon"], r["period"], r["style"],
             "; ".join(c["name"] for c in r["carvers"] if c["kind"] in ("S", "A")),
             int(r["flags"]["lost"])]
            for r in self.inscriptions if r["lat"] is not None
        ]


@lru_cache(maxsize=1)
def store() -> RundataStore:
    if not os.path.exists(DATA_PATH):
        raise HTTPException(
            status_code=503,
            detail="Rundata saknas. Kör 'python -m scripts.build_rundata' från projektroten.",
        )
    with open(DATA_PATH, encoding="utf-8") as f:
        return RundataStore(json.load(f))


def context_text(rec: dict) -> str:
    """Kortfattad, citerbar text om en inskrift för att förankra AI-svar i Rundata."""
    carvers = ", ".join(f"{c['name']} ({c['kind']}{'?' if c['uncertain'] else ''})" for c in rec["carvers"])
    lines = [
        f"Signum: {rec['signum']}" + (" (försvunnen)" if rec["flags"]["lost"] else ""),
        f"Plats: {rec['place']}, {rec['parish']}, {rec['district']}",
        f"Datering: {rec['dating'] or 'uppgift saknas'}",
        f"Stilgrupp (Gräslund): {rec['style'] or 'uppgift saknas'}{' (osäker)' if rec['style_uncertain'] and rec['style'] else ''}",
        f"Ristare: {carvers or rec['carver_raw'] or 'uppgift saknas'}",
        f"Material/föremål: {rec['material'] or rec['material_type'] or 'uppgift saknas'} / {rec['object'] or 'uppgift saknas'}",
        f"Translitterering: {rec['transliteration'] or '–'}",
        f"Normalisering: {rec['normalization'] or '–'}",
        f"Översättning (eng.): {rec['translation_en'] or '–'}",
    ]
    if rec["other"]:
        lines.append(f"Övrigt: {rec['other']}")
    return "\n".join(lines)


ATTRIBUTION_NOTE = (
    "Uppgifterna kommer från Samnordisk runtextdatabas (Uppsala universitet). "
    "Ristarkoder: S = signerad, A = attribuerad, P = parsten, L = liknar."
)
