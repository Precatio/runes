"""Ristarattribueringar i litteraturen som Rundatas ristarfält saknar (data/carver_literature.json), för de möjliga
okända ristarnas grupper (r/anonymous.R). En grupp där litteraturen redan knyter minst hälften av stenarna till en
ristare är "beskriven", en där den knyter några är "delvis beskriven", och en vars stenar är genomlästa utan träff har
"inget i litteraturen". Grupper som inte är genomlästa får "inte kontrollerad". Gruppen matchas på stenarna, inte på
numret, eftersom numren kan ändras när korpusen räknas om."""
import json
import os

PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "carver_literature.json")
CHECKED_SHARE = 0.6  # a group counts as read when this share of its stones has been looked up (n_read says how many)
_cache: tuple[float, dict] | None = None


def load() -> dict:
    global _cache
    try:
        mtime = os.path.getmtime(PATH)
    except OSError:
        return {}
    if _cache is None or _cache[0] != mtime:
        with open(PATH, encoding="utf-8") as fh:
            _cache = (mtime, json.load(fh))
    return _cache[1]


def for_group(stones: list[str], lit: dict | None = None) -> dict:
    """Vad litteraturen säger om gruppens stenar: status, attribueringarna som rör dem och hur många stenar de täcker."""
    lit = load() if lit is None else lit
    group = set(stones)
    hits = [a for a in lit.get("attributions") or [] if group & set(a["stones"])]
    covered = sorted(group & {s for a in hits for s in a["stones"]})
    checked = set((lit.get("checked") or {}).get("stones") or [])
    read = len(group & checked) / len(group) if group else 0
    if covered and len(covered) >= len(group) / 2:
        status = "beskriven"
    elif covered:
        status = "delvis beskriven"
    elif read >= CHECKED_SHARE:
        status = "inget i litteraturen"
    else:
        status = "inte kontrollerad"
    sources = lit.get("sources") or {}
    return {"status": status, "covered": covered, "n_covered": len(covered), "n_read": len(group & checked),
            "attributions": [{**a, "stones": [s for s in a["stones"] if s in group],
                              "reference": f"{a['source']} {a['page']}", "source_full": sources.get(a["source"])}
                             for a in hits],
            "nearby_signed": [x for x in lit.get("nearby_signed") or [] if x.get("anchor") in group],
            "not_read": (lit.get("checked") or {}).get("not_read")}


def by_stone(lit: dict | None = None) -> dict[str, dict]:
    """Signum -> attribueringen som gäller stenen."""
    lit = load() if lit is None else lit
    return {s: a for a in lit.get("attributions") or [] for s in a["stones"]}


def annotate(anon: dict) -> dict:
    """De okända ristarnas resultat med litteraturen på varje grupp (en kopia)."""
    if not anon or not anon.get("groups"):
        return anon
    lit = load()
    return {**anon, "groups": [{**g, "literature": for_group(list(g.get("stones") or []), lit)} for g in anon["groups"]]}
