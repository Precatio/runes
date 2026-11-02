"""De vikingatida regionerna (IMPLEMENTATIONSPLAN Fas 5.1): varje svensk runsten i sitt gamla land i stället för dagens
landskap. Uppland i folkland, Småland i små land och Gotland i tredingar enligt web/src/lib/historiska_land.json (stenen
knuten genom sin socken, scripts/assign_sten_land.py → web/public/geo/sten_land.json); övriga landskap räknas som de
land de var (Södermanland, Östergötland, Västergötland, Öland …) och behåller landskapets kod. En sten i Uppland,
Småland eller Gotland vars socken inte gick att knyta får landskapets kod, alltså "land okänt"."""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STONE_LANDS = os.path.join(ROOT, "web", "public", "geo", "sten_land.json")
LANDS = os.path.join(ROOT, "web", "src", "lib", "historiska_land.json")
_cache: dict | None = None
_names: dict | None = None


def stone_lands() -> dict[str, str]:
    global _cache
    if _cache is None:
        _cache = json.load(open(STONE_LANDS, encoding="utf-8")) if os.path.exists(STONE_LANDS) else {}
    return _cache


def old_region(signum: str, province: str) -> str:
    """Stenens gamla land (id ur historiska_land.json), annars landskapets kod."""
    return stone_lands().get(signum) or province


def names() -> dict[str, str]:
    """Namnen på de gamla landen per id (landskapens koder namnges där landskapen namnges)."""
    global _names
    if _names is None:
        d = json.load(open(LANDS, encoding="utf-8"))
        _names = {r["id"]: r["name"] for r in d["epoch"]["regions"]}
    return _names
