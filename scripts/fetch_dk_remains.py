"""Danska fornlämningar ur Fund og Fortidsminder och en plats för de danska runstenar som saknar koordinater i Rundata
(METHODS.md 14f).

    python scripts/fetch_dk_remains.py

1. Hämtar Slots- og Kulturstyrelsens nedladdning av hela databasen (FF.zip, en GeoPackage på omkring 110 MB som
   uppdateras dagligen) till data/cache/dk/ och skriver varje anlägg med sin punkt till data/dk/fortidsminder.csv
   (git-ignorerad): systemnummer, huvudgrupp, typ, år från och till, sted- och lokalitetsnummer och om det är fredat.
   Tjänsten är gratis och får användas utan styrelsens godkännande; webbplatsens sidor får inte skördas, så bara
   nedladdningen används. GDAL (ogr2ogr) måste finnas.
2. Ger de danska runstenar som saknar koordinater i Rundata en plats i data/dk/runesten_koordinater.csv (i repot):
   sockenkyrkan eller orten ur OpenStreetMap via Nominatim (ett anrop i sekunden, som tjänstens regler kräver; svaren
   sparas i data/cache/dk/nominatim.json), och om en runsten i Fund og Fortidsminder ligger inom 3 km och inte redan
   hör till en sten som har koordinater i Rundata, den runstenens punkt. Kolumnen precision säger vilket: ff (runstenen
   i registret), kyrka eller ort. Stenarna i Sydslesvig söks i Tyskland och de i Skåne, Blekinge och Halland i
   Sverige; en sten med okänd socken får ingen plats.

    python scripts/fetch_dk_remains.py platser     # bara steg 2, med den fil som redan hämtats
"""
from __future__ import annotations

import csv
import json
import math
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
CACHE = os.path.join(ROOT, "data", "cache", "dk")
OUT_DIR = os.path.join(ROOT, "data", "dk")
REMAINS = os.path.join(OUT_DIR, "fortidsminder.csv")
COORDS = os.path.join(OUT_DIR, "runesten_koordinater.csv")
FF_URL = "https://kulturarv.dk/fundogfortidsminder/Download/Filer/FF.zip"
NOMINATIM = "https://nominatim.openstreetmap.org/search"
UA = "Vitki runology research (open source)"
NEAR_KM = 3.0      # a registered runestone this close to the church is taken as the stone's place
TAKEN_KM = 1.0     # a registered runestone this close to a stone with coordinates in Rundata already belongs to it

# Every monument with its point: the GeoPackage keeps the monuments (anlæg) apart from the localities' points
SQL = ('SELECT a.systemnr, a."anlægshovedgruppe" AS gruppe, a."anlægstype" AS typ, a."fra_år" AS fra, '
       'a."til_år" AS til, p.stednr, p.lokalitetsnr, p.frednr, p.geom FROM anlaeg a '
       'JOIN lokalitet_punkt p ON p.systemnr = a.systemnr')


def _get(url: str, timeout: int = 600) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001 - nätverksfel: försök igen efter en paus
            print(f"  fel ({e}), försöker igen", file=sys.stderr)
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"Svarar inte: {url}")


def fetch_remains() -> None:
    os.makedirs(CACHE, exist_ok=True)
    os.makedirs(OUT_DIR, exist_ok=True)
    zpath, gpkg = os.path.join(CACHE, "FF.zip"), os.path.join(CACHE, "ff.gpkg")
    print("Hämtar Fund og Fortidsminder (omkring 110 MB) …", flush=True)
    with open(zpath, "wb") as fh:
        fh.write(_get(FF_URL))
    with zipfile.ZipFile(zpath) as z:
        z.extract("ff.gpkg", CACHE)
    tmp = os.path.join(CACHE, "ff_punkter.csv")  # ogr2ogr writes a folder unless the name ends in .csv
    if os.path.exists(tmp):
        os.remove(tmp)
    subprocess.run(["ogr2ogr", "-f", "CSV", tmp, gpkg, "-sql", SQL, "-t_srs", "EPSG:4326",
                    "-lco", "GEOMETRY=AS_XY", "-lco", "SEPARATOR=COMMA"], check=True)
    with open(tmp, encoding="utf-8") as fh, open(REMAINS, "w", newline="", encoding="utf-8") as out:
        w = csv.writer(out)
        w.writerow(["systemnr", "gruppe", "typ", "fra", "til", "stednr", "lokalitetsnr", "fredet", "lon", "lat"])
        n = 0
        for r in csv.DictReader(fh):
            w.writerow([r["systemnr"], r["gruppe"], r["typ"], r["fra"], r["til"], r["stednr"], r["lokalitetsnr"],
                        int(bool(r["frednr"])), round(float(r["X"]), 6), round(float(r["Y"]), 6)])
            n += 1
    os.remove(tmp)
    print(f"{n} anlägg → {REMAINS}")


def _km(a: tuple[float, float], b: tuple[float, float]) -> float:
    dlat, dlon = math.radians(b[0] - a[0]), math.radians(b[1] - a[1])
    h = math.sin(dlat / 2) ** 2 + math.cos(math.radians(a[0])) * math.cos(math.radians(b[0])) * math.sin(dlon / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def _geocode(query: str, country: str, cache: dict) -> tuple[float, float] | None:
    key = f"{country}|{query}"
    if key not in cache:
        url = NOMINATIM + "?" + urllib.parse.urlencode({"q": query, "countrycodes": country, "format": "jsonv2", "limit": 1})
        res = json.loads(_get(url, timeout=60))
        cache[key] = [float(res[0]["lat"]), float(res[0]["lon"])] if res else None
        time.sleep(1.1)  # Nominatim: at most one request a second
    return tuple(cache[key]) if cache[key] else None


def _parish(rec: dict) -> str:
    # "Gjesing sn (Gesing)" → "Gjesing"; "Stadt Schleswig" → "Schleswig"
    p = re.sub(r"\s*\(.*?\)", "", rec.get("parish") or "").strip()
    return re.sub(r"\s+sn$", "", re.sub(r"^Stadt\s+", "", p)).strip()


def _place(rec: dict) -> str:
    # "Sønder Vissing 2" → "Sønder Vissing"; "Haddeby 2 (Vedelspang 1), Wedelspang" → "Haddeby"
    return re.sub(r"\s+\d+$", "", re.split(r"[,(]", rec.get("place") or "")[0].strip())


def locate() -> None:
    from api.rundata import store
    from src import nordic
    ff = []
    if os.path.exists(REMAINS):
        with open(REMAINS, encoding="utf-8") as fh:
            ff = [(float(r["lat"]), float(r["lon"]), r["systemnr"]) for r in csv.DictReader(fh) if r["typ"] == "Runesten"]
    danish = [r for r in store().inscriptions if nordic.is_runestone(r) and nordic.land_of(r) == "danmark"]
    known = [(r["lat"], r["lon"]) for r in danish if r.get("lat") is not None]
    taken = {s for lat, lon, s in ff if any(_km((lat, lon), k) < TAKEN_KM for k in known)}
    cpath = os.path.join(CACHE, "nominatim.json")
    os.makedirs(CACHE, exist_ok=True)
    cache = json.load(open(cpath, encoding="utf-8")) if os.path.exists(cpath) else {}
    rows = []
    for rec in (r for r in danish if r.get("lat") is None):
        district = rec.get("district") or ""
        german = "Schleswig" in district or "Sydslesvig" in district
        swedish = any(p in district for p in ("Skåne", "Blekinge", "Halland"))
        country = "de" if german else "se" if swedish else "dk"
        parish, muni = _parish(rec), (rec.get("municipality") or "").strip("? ")
        church = f"{parish} {'kyrka' if swedish else 'Kirke'}, {muni}"
        spot, precision = None, ""
        queries = [] if not parish.strip("? ") else [(church, "kyrka"), (f"{parish}, {muni}", "ort"), (f"{_place(rec)}, {muni}", "ort")]
        for query, kind in queries:
            if german and kind == "kyrka":
                continue
            spot = _geocode(query, country, cache)
            if spot:
                precision = kind
                break
        if spot and not german:
            near = sorted(((_km(spot, (lat, lon)), lat, lon, s) for lat, lon, s in ff if s not in taken), key=lambda x: x[0])
            if near and near[0][0] < NEAR_KM:
                spot, precision = (near[0][1], near[0][2]), "ff"
                taken.add(near[0][3])
        rows.append({"signum": rec["signum"], "lat": round(spot[0], 5) if spot else "", "lon": round(spot[1], 5) if spot else "",
                     "precision": precision if spot else "", "parish": rec.get("parish") or "", "place": rec.get("place") or ""})
        print(f'{rec["signum"]}: {precision or "hittas inte"}', flush=True)
    json.dump(cache, open(cpath, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(COORDS, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["signum", "lat", "lon", "precision", "parish", "place"])
        w.writeheader()
        w.writerows(rows)
    found = [r for r in rows if r["precision"]]
    print(f"{len(found)} av {len(rows)} stenar fick en plats → {COORDS}")


if __name__ == "__main__":
    if sys.argv[1:] != ["platser"]:
        fetch_remains()
    locate()
