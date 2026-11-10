"""Självkontrollen (analysplaner/2026-11-10-sjalvkontroll-gravfalt.md): hämtar ur K-samsök (RAÄ:s Kulturmiljöregister,
CC0) detaljerna för alla gravfält och runristningar: antikvarisk bedömning, aktualitetsstatus, ingående lämningar,
undersökningsstatus, län, socken och beskrivning. Sidor om 100 RDF-poster med en paus mellan anropen; id som saknas
efter sidhämtningen hämtas en och en.
    .venv/bin/python utdata/familjens_plats/sjalvkontroll/hamta_gravfalt.py
Skriver data/raa/gravfalt_detaljer.csv och data/raa/runristning_lan.csv (git-ignorerade)."""
from __future__ import annotations

import csv
import html
import os
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
API = "https://kulturarvsdata.se/ksamsok/api"
PAGE = 100
PAUSE_S = 1.5
UA = {"User-Agent": "Vitki runology research (open source)"}
try:
    import certifi
    CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:  # pragma: no cover
    CTX = ssl.create_default_context()

ENTITY = re.compile(r'<ksam:Entity rdf:about="http://kulturarvsdata.se/raa/lamning/([^"]+)">(.*?)</ksam:Entity>', re.S)
DESC = re.compile(r'<ksam:type xml:lang="sv">([^<]*)</ksam:type>\s*<ksam:(?:desc|spec)[^>]*>([^<]*)</ksam:(?:desc|spec)>')
NUM = re.compile(r'<ksam:number xml:lang="sv">([^<]*)</ksam:number>\s*<ksam:type xml:lang="sv">([^<]*)</ksam:type>')
TOTAL = re.compile(r"<totalHits>(\d+)</totalHits>")
FIELDS = {"Antikvarisk bedömning": "bedomning", "Aktualitetsstatus": "aktualitet", "Ingående lämningar": "ingaende",
          "Undersökningsstatus": "undersokning", "Beskrivning": "beskrivning", "Lämningstyp": "typ"}
COLS = ["id", "typ", "lan_kod", "lan", "landskap", "socken", "raa_nr", "lamningsnr", "bedomning", "aktualitet",
        "undersokning", "ingaende", "beskrivning"]


def get(url: str) -> str:
    req = urllib.request.Request(url, headers=UA)
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=180, context=CTX) as r:
                return r.read().decode("utf-8")
        except Exception as e:  # noqa: BLE001 - nätverksfel: försök igen efter en paus
            print(f"  fel ({e}), försöker igen", file=sys.stderr, flush=True)
            time.sleep(10 * (attempt + 1))
    raise RuntimeError(f"K-samsök svarar inte: {url}")


def parse(xml: str) -> list[dict]:
    rows = []
    for eid, body in ENTITY.findall(xml):
        body_np = re.sub(r"<ksam:presentation.*?</ksam:presentation>", "", body, flags=re.S)
        row = {c: "" for c in COLS}
        row["id"] = eid
        for t, v in DESC.findall(body_np):
            k = FIELDS.get(t)
            if k:
                v = html.unescape(v).replace("\n", " ").strip()
                row[k] = (row[k] + " | " + v) if row[k] else v
        for v, t in NUM.findall(body_np):
            if t == "RAÄ-nummer":
                row["raa_nr"] = v
            elif t == "Lämningsnummer":
                row["lamningsnr"] = v
        m = re.search(r'county#(\d+)"', body_np)
        row["lan_kod"] = m.group(1) if m else ""
        for key, tag in (("lan", "countyName"), ("landskap", "provinceName"), ("socken", "parishName"),
                         ("typ", "itemClassName")):
            m = re.search(rf'<ksam:{tag} xml:lang="sv">([^<]*)<', body_np)
            row[key] = html.unescape(m.group(1)) if m else ""
        rows.append(row)
    return rows


def fetch_class(cls: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    q = f'serviceName=kmr_lamningar and itemClassName="{cls}"'
    start, total = 1, None
    while total is None or start <= total:
        xml = get(API + "?" + urllib.parse.urlencode({"method": "search", "hitsPerPage": PAGE, "startRecord": start,
                                                      "query": q}))
        m = TOTAL.search(xml)
        total = int(m.group(1)) if m else 0
        for r in parse(xml):
            out[r["id"]] = r
        print(f"{cls}: {min(start + PAGE - 1, total)} av {total} ({len(out)} unika)", flush=True)
        start += PAGE
        time.sleep(PAUSE_S)
    return out


def fetch_one(eid: str) -> dict | None:
    rows = parse(get(f"https://kulturarvsdata.se/raa/lamning/RDF/{eid}"))
    time.sleep(PAUSE_S)
    return rows[0] if rows else None


def write(path: str, rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    want = [r["id"] for r in csv.DictReader(open(os.path.join(ROOT, "data", "raa", "lamningar.csv"), encoding="utf-8"))
            if r["type"] == "gravfält"]
    got = fetch_class("gravfält")
    missing = [i for i in want if i not in got]
    print(f"gravfält: {len(want)} i lamningar.csv, {len(missing)} saknas efter sidorna – hämtas en och en", flush=True)
    for i in missing:
        r = fetch_one(i)
        if r:
            got[i] = r
    still = [i for i in want if i not in got]
    print(f"gravfält utan detaljer (finns inte längre i K-samsök): {len(still)}", flush=True)
    write(os.path.join(ROOT, "data", "raa", "gravfalt_detaljer.csv"), [got[i] for i in want if i in got])

    import json
    kmr = json.load(open(os.path.join(ROOT, "data", "raa", "kmr_runstenar.json"), encoding="utf-8"))["records"]
    ids = [r["kmr_id"] for r in kmr]
    rr = fetch_class("runristning")
    for i in [i for i in ids if i not in rr]:
        r = fetch_one(i)
        if r:
            rr[i] = r
    print(f"runristningar: {len(ids)} i kmr_runstenar.json, {sum(i in rr for i in ids)} med län", flush=True)
    write(os.path.join(ROOT, "data", "raa", "runristning_lan.csv"), [rr[i] for i in ids if i in rr])


if __name__ == "__main__":
    main()
