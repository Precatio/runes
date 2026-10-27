"""Uppslag och sökning i Samnordisk runtextdatabas (data/rundata.json).

Filen byggs med `python -m scripts.build_rundata`.
"""
import json
import os
import re
import unicodedata
from collections import Counter
from functools import lru_cache
from typing import Optional

from fastapi import HTTPException

from src import research_gaps as gaps
from src.inscription_types import categories as inscription_categories, is_runestone_any
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
    r"(?<![A-Za-zÅÄÖåäö])(U|Sö|So|Ög|Og|Öl|Ol|Vg|Sm|Gs|Vs|Nä|Na|Hs|M|Ån|An|D|Hr|J|Lp|Ds|Bo|G|DR|N ?A|N|IS|IM|E|GR|Or)"
    # A number followed by a percent sign or a decimal is a share ("Vg 84 %", "U 26,5 %"), not a signum
    r"[\s_]?(\d{1,4})(?![\d])(?![,.]\d)(?!\s*(?:%|procent))"
)


SAME_CARVER_RE = re.compile(r"samma (?:ristare )?som (?:gjort|ristat|har gjort)\s+(.+)", re.I)


def same_carver_as(rec: dict) -> list[str]:
    """Stenar som Rundata anger är gjorda av samma (ofta namnlösa) ristare (U 1026: 'Samma som gjort U 1027.')."""
    m = SAME_CARVER_RE.search(rec.get("carver_raw") or "")
    if not m:
        return []
    return [f"{a} {b}" for a, b in SIGNUM_IN_TEXT_RE.findall(m.group(1))]


NORWEGIAN_A = re.compile(r"NA\d")  # the exact key of the Norwegian series 'N A1', 'N A11' (Närke is 'Nä', ASCII 'Na')


def _exact_key(signum: str) -> str:
    """Signumet som det skrivs, bara utan mellanslag: håller isär signa som fold_signum slår ihop ("N A11" och "Nä 11")."""
    return re.sub(r"[\s_]+", "", unicodedata.normalize("NFC", signum or ""))


class RundataStore:
    def __init__(self, data: dict):
        self.meta = data["meta"]
        self.inscriptions: list[dict] = data["inscriptions"]
        self.by_key: dict[str, dict] = {}
        # Exact signa first: fold_signum drops diacritics, so the Norwegian 'N A11' and the Närke 'Nä 11' share a folded
        # key; the folded key stays the fallback for everything else (case, 'So 113' for 'Sö 113', aliases)
        self.by_exact: dict[str, dict] = {}
        for rec in self.inscriptions:
            self.by_exact.setdefault(_exact_key(rec["signum"]), rec)
            self.by_key.setdefault(fold_signum(rec["signum"]), rec)
            rec["same_carver_as"] = same_carver_as(rec)
        for alias, target in data.get("aliases", {}).items():
            rec = self.by_exact.get(_exact_key(target)) or self.by_key.get(fold_signum(target))
            if rec:
                # The exact alias too, after every record signum: the alias 'N A14' (Bo Peterson1992) shares the folded
                # key 'na14' with the Närke Nä 14, so without it the folded key handed 'N A14' to Nä 14
                self.by_exact.setdefault(_exact_key(alias), rec)
                self.by_key.setdefault(fold_signum(alias), rec)

    def get(self, signum: str) -> Optional[dict]:
        rec = self.by_exact.get(_exact_key(signum))
        if rec:
            return rec
        rec = self.by_key.get(fold_signum(signum))
        # A Norwegian 'N A12' that Rundata lacks must not fall back to the Närke Nä 12 through the folded key
        if rec and NORWEGIAN_A.match(_exact_key(signum)) and not NORWEGIAN_A.match(_exact_key(rec["signum"])):
            return None
        return rec

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
               gap: str = "", signa: str = "", category: str = "", certain: bool = False):
        q_l, carver_l = q.lower().strip(), carver.lower().strip()
        gap_test = GAP_FILTERS.get(gap)
        # The wanted records through get() (exact signum first), not through folded keys: a list with 'Nä 11' must not
        # also bring the Norwegian 'N A11'
        wanted = {id(r) for r in (self.get(x.strip()) for x in signa.split(",") if x.strip()) if r} if signa else None
        q_rec = self.get(q.strip()) if q.strip() else None
        results = []
        for rec in self.inscriptions:
            if gap_test and not gap_test(rec):
                continue
            if wanted is not None and id(rec) not in wanted:
                continue
            # Same population as the category statistics: Viking Age runestones
            if category and (not is_runestone_any(rec) or category not in inscription_categories(rec)):
                continue
            # Only inscriptions where the carver is the single certain (signed or attributed) carver
            if certain and carver_l and [c.lower() for c in gaps.certain_carvers(rec)] != [carver_l]:
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
                if q_l not in hay and rec is not q_rec:
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
        """Kompakt lista för kartan: [signum, lat, lon, period, stil, ristare (S/A), försvunnen, landskap, föremål,
        bergart (grupp), kors, ristarstatus, innehållskategorier, vikingatida runsten]."""
        return [
            [r["signum"], r["lat"], r["lon"], r["period"], r["style"],
             "; ".join(c["name"] for c in r["carvers"] if c["kind"] in ("S", "A")),
             int(r["flags"]["lost"]), r["signum"].split(" ")[0], r.get("object") or "",
             material_group(r), int(bool((r.get("cross_form") or "").strip(" ;0"))),
             carver_status(r), inscription_categories(r), int(gaps.is_runestone(r))]
            for r in self.inscriptions if r["lat"] is not None
        ]

    def text_matches(self, q: str) -> list[str]:
        """Signum för inskrifter med koordinater vars text, plats eller socken innehåller q (skiftlägesokänsligt)."""
        q = q.lower().strip()
        return [r["signum"] for r in self.inscriptions if r["lat"] is not None and q in " ".join(
            (r["place"], r["parish"], r["transliteration"], r["normalization"], r.get("normalization_ows") or "",
             r["translation_en"])).lower()]


MATERIAL_GROUPS = ("granit", "gnejs", "sandsten", "kalksten", "gråsten", "skiffer", "diabas", "porfyr")


OTHER_MATERIALS = {"trä": "trä", "metall": "metall", "ben/horn": "ben och horn", "puts": "puts"}


def material_group(rec: dict) -> str:
    """Materialet i grova grupper för kartan: bergarten för sten (första träffen i Rundatas fritext, så att
    'gnejsgranit' blir granit), annars materialtypen (trä, metall, ben och horn, puts)."""
    kind = rec.get("material_type") or ""
    if kind in OTHER_MATERIALS:
        return OTHER_MATERIALS[kind]
    m = (rec.get("material") or "").lower()
    if not m:
        return ""
    return next((g for g in MATERIAL_GROUPS if g in m), "annan sten")


def carver_status(rec: dict) -> str:
    """S = signerad, A = attribuerad (säker), ? = bara osäker attribuering, tom = ingen ristare i Rundata."""
    kinds = {(c["kind"], c["uncertain"]) for c in rec["carvers"] if c["kind"] in ("S", "A")}
    if any(k == "S" and not u for k, u in kinds):
        return "S"
    if any(k == "A" and not u for k, u in kinds):
        return "A"
    return "?" if kinds else ""


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
