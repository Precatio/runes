from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request

from api.cache import cached_json
from api.rundata import ATTRIBUTION_NOTE, store
from src.styles import SOURCE as STYLE_SOURCE, STYLE_GROUPS

router = APIRouter()


@router.get("/meta")
def meta():
    s = store()
    return {**s.meta, "note": ATTRIBUTION_NOTE}


@router.get("/inscription/{signum:path}")
def inscription(signum: str):
    rec = store().get(signum)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Signum '{signum}' finns inte i Rundata.")
    from src import runor, stone_dimensions
    dims = stone_dimensions.lookup(rec["signum"])
    if dims:
        dims = {**dims, "in_province": stone_dimensions.province_percentile(rec["signum"], lambda s: s.split(" ")[0])}
    # Runor 2020 bredvid Rundata 2018 (src/runor.py): visas, räknas inte på
    return {**rec, "dimensions": dims, "runor": runor.for_inscription(rec)}


@router.get("/search")
def search(
    q: str = "",
    carver: str = "",
    style: str = "",
    period: Optional[str] = Query(None, pattern="^[UVM]$"),
    province: str = "",
    has_coords: bool = False,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    gap: str = Query("", pattern="^(|runestone|carver|no_carver|style|no_style|dated|uncertain_interpretation|lost)$"),
    signa: str = Query("", max_length=20000),  # comma-separated, e.g. the measured stones
    category: str = Query("", pattern="^(|minne|sjalvminne|bro_vag|kristen|fard|arv|ting|magisk|grans)$"),
    certain: bool = False,
):
    return store().search(q=q, carver=carver, style=style, period=period or "", province=province,
                          has_coords=has_coords, limit=limit, offset=offset, gap=gap, signa=signa,
                          category=category, certain=certain)


@router.get("/find")
def find_in_text(text: str = Query(..., max_length=2000)):
    """Hittar signum i fri text, t.ex. ett filnamn som 'U_11_mesh.obj'."""
    return [{"signum": r["signum"], "place": r["place"]} for r in store().find_in_text(text)]


@router.get("/carvers")
def carvers():
    return store().carvers()


@router.get("/styles")
def styles():
    return {"groups": STYLE_GROUPS, "source": STYLE_SOURCE, "distribution": store().style_stats()}


# --- Ordmolnet: orden på de vikingatida runstenarna, ur Rundatas normalisering ---
import re as _re  # noqa: E402

_WORD_OK = _re.compile(r"^[a-zåäöæøǫœęþðáéíóúýūōR]+$")


def _word_tokens(norm):
    """(ord, är_namn) ur Rundatas normalisering. Citattecken märker namn, hakparenteser är utgivarnas
    återställningar och tas med; ord med kvarstående skade- eller osäkerhetsmarkering (… - ?) hoppas över.
    Slut-R (palatalt ʀ) behålls som i normaliseringen."""
    for raw in (norm or "").split():
        name = '"' in raw
        t = raw.translate(str.maketrans("", "", '"[]()<>{}«»')).strip(".,;:!?+·×=§|/\\'’")
        if not t or "..." in t or "-" in t or "?" in t or "…" in t:
            continue
        # single letters are nearly always fragments, not words – utom prepositionerna a, i och danska ø
        if len(t) == 1 and t.lower() not in ("a", "i", "ø"):
            continue
        head = t[:1].upper() if name else t[:1].lower()  # namnen behåller Rundatas stora bokstav
        t = head + "".join(ch if ch == "R" else ch.lower() for ch in t[1:])
        if _WORD_OK.match(t.lower() if name else t):
            yield t, name


def _viking_runestones():
    from src import runlm as rl
    return [r for r in store().inscriptions if rl.object_kind(r) == "runsten" and rl.viking(r)]


_words_common_cache: dict = {}


def _words_common() -> list:
    """De vanligaste orden (utan namn) på alla vikingatida runstenar, för molnets 'dölj de vanligaste'-val."""
    from collections import Counter
    key = id(store().inscriptions)
    if key not in _words_common_cache:
        c = Counter()
        for rec in _viking_runestones():
            c.update({w for w, name in set(_word_tokens(rec.get("normalization"))) if not name})
        _words_common_cache.clear()
        _words_common_cache[key] = [w for w, _ in c.most_common(30)]
    return _words_common_cache[key]


@router.get("/words")
def words(area: str = "", epoch: str = "", style: str = "", top: int = 400):
    """Ordmolnets underlag: orden på de vikingatida runstenarna, räknade per sten (hur många stenar ordet står
    på) och per förekomst. area är en trakt (runlm.AREAS) eller ett signumprefix; epoch 800/900/1000/1100 eller
    'odaterad' (epoken ur Rundatas datering eller stilgruppen, som i modellen); style en stilgrupp."""
    from src import runlm as rl
    from src.research_gaps import PROVINCE_NAMES
    pres = set(rl.AREAS[area].split()) if area in rl.AREAS else {area} if area else None
    stones = 0
    agg: dict = {}
    present: set = set()
    for rec in _viking_runestones():
        pre = rec["signum"].split(" ")[0]
        present.add(pre)
        if pres is not None and pre not in pres:
            continue
        if epoch:
            ep = rl.epoch(rec)
            if (ep is not None) if epoch == "odaterad" else (ep != epoch):
                continue
        if style and style not in _re.findall(r"RAK|Fp|KB|Pr\d", rec.get("style") or ""):
            continue
        toks = list(_word_tokens(rec.get("normalization")))
        if not toks:
            continue
        stones += 1
        seen = set()
        for k in toks:
            a = agg.setdefault(k, [0, 0])
            a[1] += 1
            if k not in seen:
                a[0] += 1
                seen.add(k)
    # Namnen får en egen kvot: de flesta namn står på en enda sten och skulle annars aldrig nå topplistan
    lim = max(1, min(top, 1000))
    order = sorted(agg.items(), key=lambda kv: (-kv[1][0], -kv[1][1], kv[0][0]))
    ranked = [kv for kv in order if not kv[0][1]][:lim] + [kv for kv in order if kv[0][1]][:lim // 2]
    names = {**PROVINCE_NAMES, **OTHER_REGIONS}
    return {"stones": stones,
            "words": [{"w": w, "name": nm, "stones": s, "n": n} for (w, nm), (s, n) in ranked],
            "common": _words_common(),
            "areas": list(rl.AREAS),
            "provinces": sorted(({"code": p, "label": names.get(p, p)} for p in present), key=lambda x: x["label"])}


# Signum prefixes outside Sweden that occur on the map
OTHER_REGIONS = {"N": "Norge", "DR": "Danmark", "IS": "Island", "GR": "Grönland", "Or": "Orkney", "Sh": "Shetland",
                 "IM": "Isle of Man", "E": "England", "Sc": "Skottland", "Ir": "Irland", "FI": "Finland",
                 "By": "Bysans", "Fær": "Färöarna"}


@router.get("/geo")
def geo(request: Request):
    """Inskrifter med koordinater för kartan, med etiketter för landskap, innehåll och språkdrag. Byggs en gång per
    Rundata-version (api/cache.py)."""
    return cached_json(request, geo_key(), _geo)


def geo_key() -> str:
    return f"geo|{id(store().inscriptions)}"


def _geo() -> dict:
    from src.inscription_types import CATEGORIES
    from src.language_profile import TRAITS
    from src.research_gaps import PROVINCE_NAMES
    return {"fields": ["signum", "lat", "lon", "period", "style", "carvers", "lost", "province", "object",
                       "material", "cross", "carver_status", "categories", "runestone"],
            "rows": store().geo(),
            "provinces": {**OTHER_REGIONS, **PROVINCE_NAMES},
            "categories": {k: v[0] for k, v in CATEGORIES.items()},
            "traits": {k: {"group": v[0], "label": v[1]} for k, v in TRAITS.items()}}


@router.get("/geo/trait/{key}")
def geo_trait(key: str):
    """Ett språkdrag för alla inskrifter med koordinater: värdet per signum och hur vanligt varje värde är."""
    from collections import Counter
    from api.routers.orthography import model as orthography_model
    from src.language_profile import TRAITS, traits
    if key not in TRAITS:
        raise HTTPException(status_code=404, detail=f"Okänt språkdrag: {key}")
    names = orthography_model().names
    rows = {}
    for r in store().inscriptions:
        if r["lat"] is not None:
            v = traits(r, names).get(key)
            if v:
                rows[r["signum"]] = v
    return {"key": key, "label": TRAITS[key][1], "definition": TRAITS[key][2],
            "values": dict(Counter(rows.values()).most_common()), "rows": rows}


@router.get("/geo/match")
def geo_match(q: str = Query(..., min_length=2, max_length=100)):
    """Signum för inskrifter med koordinater där texten (translitterering, normalisering, översättning), platsen
    eller socknen innehåller söktexten."""
    return {"q": q, "signa": store().text_matches(q)}
