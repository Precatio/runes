"""Hämtar Digitala Sveriges runinskrifter (RAÄ) till litteraturmappen (/Volumes/2TB/litteratur).

Tre sidor på raa.se/kulturarv/runor-och-runstenar/digitala-sveriges-runinskrifter/:
- de publicerade banden (sri_<landskap>_b<band>_..._text*.pdf, register, inledningar; planscherna bara med --planscher);
- Gotlands runinskrifter 3, RAÄ:s preliminära manus per socken (sparas som gr3_<fil>.pdf);
- Supplement till Upplands runinskrifter, en PDF per sten (sparas som urs_<fil>.pdf).

Ett anrop i taget med paus. Filer som redan finns hoppas över, så skriptet kan avbrytas och startas om.
Logg: /Volumes/2TB/Antigrvity/Runes/logs/sri.log. Förteckning: <mappen>/sri_hamtning.json (url, fil, storlek, sha256).

    .venv/bin/python scripts/hamta_sri.py [--planscher]
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from urllib.parse import unquote

BAS = "https://www.raa.se/kulturarv/runor-och-runstenar/digitala-sveriges-runinskrifter/"
SIDOR = {
    "digitala-sveriges-runinskrifter-publicerade-volymer/": "",
    "gotlands-runinskrifter-3/": "gr3_",
    "supplement-till-upplands-runinskrifter/": "urs_",
}
MAPP = os.environ.get("LITERATURE_DIR", "/Volumes/2TB/litteratur")
LOGG = "/Volumes/2TB/Antigrvity/Runes/logs/sri.log"
UA = {"User-Agent": "Mozilla/5.0 (research download; one request at a time)"}
PAUS = 2.0


def logg(msg: str) -> None:
    rad = f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    print(rad, flush=True)
    with open(LOGG, "a", encoding="utf-8") as fh:
        fh.write(rad + "\n")


def hamta(url: str, timeout: int = 600) -> bytes:
    # curl i stället för urllib: Pythons certifikatkedja saknar RAÄ:s utfärdare på den här datorn
    r = subprocess.run(["curl", "-sfL", "--max-time", str(timeout), "-A", UA["User-Agent"], url],
                       capture_output=True, timeout=timeout + 30)
    if r.returncode:
        raise OSError(f"curl {r.returncode}")
    return r.stdout


def lankar(planscher: bool) -> list[tuple[str, str]]:
    ut = []
    for sida, prefix in SIDOR.items():
        html = hamta(BAS + sida).decode("utf-8", "replace")
        for url in sorted(set(re.findall(r'href="([^"]+\.pdf)"', html, flags=re.I))):
            namn = unquote(url.rsplit("/", 1)[-1])
            if "raa.se" not in url:
                logg(f"hoppar över extern länk {url}")
                continue
            if not planscher and re.search(r"plansch|pl_titel", namn):
                continue
            namn = prefix + re.sub(r"[^\w.,-]", "_", namn)
            ut.append((url, namn))
    return ut


def main() -> None:
    os.makedirs(os.path.dirname(LOGG), exist_ok=True)
    forteckning_fil = os.path.join(MAPP, "sri_hamtning.json")
    forteckning = json.load(open(forteckning_fil, encoding="utf-8")) if os.path.exists(forteckning_fil) else {}
    lista = lankar("--planscher" in sys.argv)
    logg(f"{len(lista)} filer att hämta")
    for i, (url, namn) in enumerate(lista, 1):
        mal = os.path.join(MAPP, namn)
        if os.path.exists(mal) and os.path.getsize(mal) > 0:
            if namn not in forteckning:
                data = open(mal, "rb").read()
                forteckning[namn] = {"url": url, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                                     "hamtad": "fanns redan"}
            continue
        for forsok in range(3):
            try:
                data = hamta(url)
                if not data.startswith(b"%PDF"):
                    raise ValueError("inte en PDF")
                with open(mal + ".tmp", "wb") as fh:
                    fh.write(data)
                os.replace(mal + ".tmp", mal)
                forteckning[namn] = {"url": url, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                                     "hamtad": datetime.now().isoformat(timespec="seconds")}
                logg(f"[{i}/{len(lista)}] {namn} {len(data) / 1e6:.1f} MB")
                break
            except Exception as e:  # noqa: BLE001
                logg(f"[{i}/{len(lista)}] {namn} försök {forsok + 1} misslyckades: {e}")
                time.sleep(10 * (forsok + 1))
        with open(forteckning_fil, "w", encoding="utf-8") as fh:
            json.dump(forteckning, fh, ensure_ascii=False, indent=1)
        time.sleep(PAUS)
    logg(f"klart: {len(forteckning)} filer i förteckningen")


if __name__ == "__main__":
    main()
