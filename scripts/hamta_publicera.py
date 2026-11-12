"""Hämtar fritt licensierade tidskrifter från KB:s plattform Publicera (publicera.kb.se, OJS).

Bara det som har en fri licens (Viktor 2026-11-12: "undvik de som inte är fria licenser"):
- nob  Namn och bygd, vol. 98–113 (2010–2025): hela arkivet på Publicera, CC BY 4.0.
- csa  Current Swedish Archaeology, vol. 28 och senare (2020–): CC BY 4.0. Vol. 1–27 har upphovsrätt
       (samfundet och författarna) och hämtas inte.

Licensen läses från varje nummers sida (creativecommons.org-länken); ett nummer utan CC BY hoppas över.
Sparas som downloads/tidskrifter/<tidskrift>/{pdf,text}/<nyckel>.{pdf,txt} med index.jsonl, som Fornvännen och Futhark.
Ett anrop i taget med paus; redan hämtade filer hoppas över.

    .venv/bin/python scripts/hamta_publicera.py nob csa
"""
from __future__ import annotations

import html
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime

BAS = "https://publicera.kb.se"
UT = "/Volumes/2TB/Antigrvity/Runes/downloads/tidskrifter"
LOGG = "/Volumes/2TB/Antigrvity/Runes/logs/publicera.log"
PAUS = 2.0
TIDSKRIFTER = {
    "nob": {"namn": "Namn och bygd", "katalog": "namnochbygd", "fran_vol": 0},
    "csa": {"namn": "Current Swedish Archaeology", "katalog": "csa", "fran_vol": 28},
}


def logg(msg: str) -> None:
    rad = f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    print(rad, flush=True)
    os.makedirs(os.path.dirname(LOGG), exist_ok=True)
    with open(LOGG, "a", encoding="utf-8") as fh:
        fh.write(rad + "\n")


def hamta(url: str, timeout: int = 300) -> bytes:
    r = subprocess.run(["curl", "-sfL", "--max-time", str(timeout), url], capture_output=True, timeout=timeout + 30)
    if r.returncode:
        raise OSError(f"curl {r.returncode} {url}")
    time.sleep(PAUS)
    return r.stdout


def text(url: str) -> str:
    return hamta(url).decode("utf-8", "replace")


def nummer(kort: str) -> list[str]:
    ids, sida = [], 1
    while True:
        t = text(f"{BAS}/{kort}/issue/archive" + (f"/{sida}" if sida > 1 else ""))
        nya = [i for i in dict.fromkeys(re.findall(rf"{kort}/issue/view/(\d+)", t)) if i not in ids]
        if not nya:
            return ids
        ids += nya
        sida += 1


def main() -> None:
    for kort in sys.argv[1:] or list(TIDSKRIFTER):
        cfg = TIDSKRIFTER[kort]
        mapp = os.path.join(UT, cfg["katalog"])
        for sub in ("pdf", "text"):
            os.makedirs(os.path.join(mapp, sub), exist_ok=True)
        index = os.path.join(mapp, "index.jsonl")
        har = {json.loads(r)["key"] for r in open(index, encoding="utf-8")} if os.path.exists(index) else set()
        ids = nummer(kort)
        logg(f"{cfg['namn']}: {len(ids)} nummer i arkivet")
        for nid in ids:
            sida = text(f"{BAS}/{kort}/issue/view/{nid}")
            rubrik = html.unescape(re.sub(r"\s+", " ", (re.search(r"<title>(.*?)</title>", sida, re.S) or [None, ""])[1])).strip()
            m = re.search(r"Vol\.?\s*(\d+)(?:\s*No\.?\s*(\d+))?\s*\((\d{4})\)", rubrik + " " + sida)
            if not m:
                logg(f"  nummer {nid}: hittar inte volym i '{rubrik[:80]}', hoppar över")
                continue
            vol, nr, ar = int(m.group(1)), m.group(2), int(m.group(3))
            if vol < cfg["fran_vol"]:
                continue
            lic = re.search(r"creativecommons\.org/licenses/([a-z-]+)/([0-9.]+)", sida)
            if not lic or lic.group(1) != "by":
                logg(f"  vol {vol} ({ar}): ingen CC BY på sidan ({lic.group(0) if lic else 'ingen licens'}), hoppar över")
                continue
            licens = f"CC BY {lic.group(2)}"
            # helt nummer om det finns, annars artiklarna
            gal = [("issue", nid, g) for g in dict.fromkeys(re.findall(rf"{kort}/issue/view/{nid}/(\d+)", sida))]
            if not gal:
                gal = [("article", a, g) for a, g in dict.fromkeys(re.findall(rf"{kort}/article/view/(\d+)/(\d+)", sida))]
            sett_art = set()
            for typ, a, g in gal:
                if typ == "article" and a in sett_art:
                    continue
                nyckel = f"{vol}_{ar}" + (f"_{nr}" if nr else "") + (f"_{a}" if typ == "article" else "")
                if nyckel in har:
                    sett_art.add(a)
                    continue
                try:
                    data = hamta(f"{BAS}/{kort}/{typ}/download/{a}/{g}")
                except OSError as e:
                    logg(f"  {nyckel}: {e}")
                    continue
                if not data.startswith(b"%PDF"):
                    continue  # html- eller xml-version av artikeln; PDF:en är en annan galley
                sett_art.add(a)
                pdf = os.path.join(mapp, "pdf", nyckel + ".pdf")
                with open(pdf, "wb") as fh:
                    fh.write(data)
                txt = os.path.join(mapp, "text", nyckel + ".txt")
                subprocess.run(["pdftotext", "-layout", pdf, txt], capture_output=True, timeout=600)
                titel = ""
                if typ == "article":
                    t = re.search(rf'article/view/{a}"[^>]*>\s*(.*?)\s*</a>', sida, re.S)
                    titel = html.unescape(re.sub(r"<[^>]+>|\s+", " ", t.group(1))).strip() if t else ""
                post = {"key": nyckel, "journal": cfg["namn"], "volume": vol, "number": nr, "year": ar,
                        "title": titel or rubrik, "licence": licens,
                        "source": f"{BAS}/{kort}/{typ}/view/{a}/{g}", "bytes": len(data),
                        "fetched": datetime.now().isoformat(timespec="seconds")}
                with open(index, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(post, ensure_ascii=False) + "\n")
                har.add(nyckel)
                logg(f"  {nyckel} {len(data) / 1e6:.1f} MB {licens} {titel[:60]}")
        logg(f"{cfg['namn']}: klart, {len(har)} filer")


if __name__ == "__main__":
    main()
