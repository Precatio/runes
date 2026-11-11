"""D4: hämtar fältdatum (senaste fältbesök) ur Fornsök för ett slumpurval av lämningar i varje socken.

    .venv/bin/python -m scripts.fetch_kmr_faltdatum                # k=6 per socken (runstenssocknar först)
    .venv/bin/python -m scripts.fetch_kmr_faltdatum --k 10         # fyller på till 10 per socken (samma ordning)
    .venv/bin/python -m scripts.fetch_kmr_faltdatum --lan Dalarna  # bara ett län
    .venv/bin/python -m scripts.fetch_kmr_faltdatum --k 6 --k-ovriga 4  # runstenssocknar 6, övriga 4 (sedan fyllt på till 6)

Varför: Kulturmiljöregistrets GeoPackage (geografi_kallor/raa/lamningar_sverige.gpkg) saknar inventeringsår, men
Fornsöks öppna API (https://app.raa.se/open/fornsok/api/lamning/lamning/<uuid>) ger varje lämnings `faltdatum`, det
datum då lämningen senast besöktes i fält enligt FMIS. För poster som inte ändrats sedan migreringen från FMIS
(publiceringsdatum 2018) är det i de allra flesta fall fornminnesinventeringens (oftast revideringsinventeringens)
besök. Datum som slutar på -01-01 betyder att bara året är känt.

Urval: bara poster med publiceringsdatum 2018 (oförändrade sedan FMIS) och med en enda socken och ett enda län.
Ordningen inom varje socken är en fast slumpordning (seed per socken), så --k 10 tar samma 6 först och lägger till
4. Socknar med Runors vikingatida runstenar (data/raa/kmr_runstenar.json) hämtas först, sedan resten.

Utdata (utanför repot, på 2TB-disken): downloads/kmr_faltdatum/faltdatum.jsonl, en rad per lämning, bara de fält
som behövs (inga geometrier). Skriptet kan avbrytas och startas om; redan hämtade id hoppas över.
Ett anrop i taget med paus. Licens: CC0 (Riksantikvarieämbetet).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sqlite3
import sys
import time

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DISK = os.path.dirname(ROOT)  # /Volumes/2TB/Antigrvity/Runes
GPKG = os.path.join(DISK, "geografi_kallor", "raa", "lamningar_sverige.gpkg")
OUTDIR = os.path.join(DISK, "downloads", "kmr_faltdatum")
OUT = os.path.join(OUTDIR, "faltdatum.jsonl")
RUNSTENAR = os.path.join(ROOT, "data", "raa", "kmr_runstenar.json")
URL = "https://app.raa.se/open/fornsok/api/lamning/lamning/{}"
HEADERS = {"User-Agent": "Vitki/1.0 (runestone research; https://github.com/Precatio/runes)",
           "Accept": "application/json"}
PAUSE_S = 0.25


def gpkg() -> sqlite3.Connection:
    return sqlite3.connect(f"file:{GPKG}?mode=ro", uri=True)


def runestone_parishes(con: sqlite3.Connection) -> set[tuple[str, str]]:
    ids = [r["kmr_id"] for r in json.load(open(RUNSTENAR, encoding="utf-8"))["records"]]
    out: set[tuple[str, str]] = set()
    for i in range(0, len(ids), 500):
        chunk = ids[i:i + 500]
        q = f"select lan, socken from lamning where uuid in ({','.join('?' * len(chunk))})"
        for lan, soc in con.execute(q, chunk):
            for s in (soc or "").split(","):
                out.add((lan, s.strip()))
    return out


def plan(k: int, lan_filter: str | None, k_other: int | None = None) -> list[tuple[str, str, str]]:
    con = gpkg()
    by: dict[tuple[str, str], list[str]] = {}
    q = ("select lan, socken, uuid from lamning where publiceringsdatum like '2018%' and socken <> '' "
         "and socken not like '%,%' and lan not like '%,%'")
    for lan, soc, uuid in con.execute(q):
        by.setdefault((lan, soc), []).append(uuid)
    rs = runestone_parishes(con)
    con.close()
    keys = sorted(by, key=lambda p: (p not in rs, p))
    jobs = []
    for p in keys:
        if lan_filter and p[0] != lan_filter:
            continue
        ids = sorted(by[p])
        seed = int(hashlib.sha256(f"{p[0]}|{p[1]}".encode()).hexdigest()[:12], 16)
        random.Random(seed).shuffle(ids)
        jobs.extend((p[0], p[1], u) for u in ids[:k if (p in rs or k_other is None) else k_other])
    return jobs


def slim(d: dict, lan: str, soc: str) -> dict:
    a = d.get("aktivitetsref") or {}
    leg = d.get("legacy") or {}
    return {"uuid": d.get("lamning_id"), "lan": lan, "socken": soc, "faltdatum": d.get("faltdatum"),
            "lamningsnummer": d.get("lamningsnummer"), "raa_nummer": leg.get("raa_nummer"),
            "fmis_id": leg.get("fmis_id"), "lamningstyp": d.get("lamningstyp_namn"),
            "bedomning": d.get("antikvariskbedomningtyp_namn"),
            "aktualitet": (d.get("aktualitetstatus") or {}).get("aktualitetstatustyp_namn"),
            "atgard": a.get("atgardtyp_namn"), "publiceringsdatum": d.get("publiceringsdatum"),
            "registrerare": d.get("registrerare_organisationsnamn"), "senast_andrad": d.get("senast_andrad")}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=6)
    ap.add_argument("--lan")
    ap.add_argument("--k-ovriga", type=int, help="k för socknar utan runsten (standard: samma som --k)")
    args = ap.parse_args()
    os.makedirs(OUTDIR, exist_ok=True)
    done = set()
    if os.path.exists(OUT):
        for line in open(OUT, encoding="utf-8"):
            try:
                done.add(json.loads(line)["uuid"])
            except Exception:  # noqa: BLE001 - halvskriven sista rad efter avbrott
                pass
    jobs = [j for j in plan(args.k, args.lan, args.k_ovriga) if j[2] not in done]
    print(f"{len(done)} redan hämtade, {len(jobs)} kvar", flush=True)
    s = requests.Session()
    s.headers.update(HEADERS)
    t0 = time.time()
    with open(OUT, "a", encoding="utf-8") as fh:
        for n, (lan, soc, uuid) in enumerate(jobs, 1):
            for attempt in range(5):
                try:
                    r = s.get(URL.format(uuid), timeout=(10, 30))
                    if r.status_code == 404:
                        rec = {"uuid": uuid, "lan": lan, "socken": soc, "faltdatum": None, "saknas": True}
                        break
                    r.raise_for_status()
                    rec = slim(r.json(), lan, soc)
                    rec["uuid"] = uuid
                    break
                except Exception as e:  # noqa: BLE001 - nätverksfel: vänta och försök igen
                    print(f"  fel {uuid} ({e}), försöker igen", file=sys.stderr, flush=True)
                    time.sleep(15 * (attempt + 1))
            else:
                raise RuntimeError("Fornsök svarar inte; avbryter (starta om senare)")
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            if n % 200 == 0:
                rate = (time.time() - t0) / n
                print(f"{n}/{len(jobs)}  {rate:.2f} s/st  ~{rate * (len(jobs) - n) / 3600:.1f} h kvar  ({lan}, {soc})",
                      flush=True)
            time.sleep(PAUSE_S)


if __name__ == "__main__":
    main()
