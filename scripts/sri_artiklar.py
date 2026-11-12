"""Delar ett SRI-band i en artikel per runsten, som underlag för faktautplockningen (A1, tillägg 1).

Läser bandets PDF:er (data/literature/catalog.json, `files`) i LITERATURE_DIR, tar ut texten sida för sida och klyver
den vid utgåvans egna rubriker ("179. Kölaby sn, Stommen.", src/literature.ENTRY). Varje artikel får signum
(utgåvans prefix + numret), tryckta sidor och texten. Bara rubriker vars nummer kommer i stigande ordning räknas, så att
hänvisningar inne i löptexten ("se 179. Kölaby sn") inte klyver en artikel.

Utdata innehåller SRI:s text och ligger därför UTANFÖR repot (källregeln, METHODS §17):
/Volumes/2TB/Antigrvity/Runes/downloads/sri_artiklar/<verk>.jsonl

    .venv/bin/python scripts/sri_artiklar.py sri3 [sri6 …]
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from api.rundata import store  # noqa: E402
from src import literature  # noqa: E402
from src.signum import fold_signum  # noqa: E402

UT = "/Volumes/2TB/Antigrvity/Runes/downloads/sri_artiklar"
MAX_TECKEN = 40000


def sidor(path: str) -> list[str]:
    return subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, text=True, timeout=600).stdout.split("\f")


def artiklar(work: dict, signa: dict) -> tuple[list[dict], dict]:
    prefix = work["entry_prefix"]
    flat: list[tuple[str, str, str]] = []  # (fil, tryckt sida, text)
    for f in literature.files(work):
        if not re.search(r"_text", f) or re.search(r"_(ord|karta|titel)", f):
            continue  # inledning, titelblad, ordregister och karta är inga stenartiklar
        p = os.path.join(literature.DIR, f)
        if not os.path.exists(p):
            continue
        raws = sidor(p)
        printed = literature.fill_pages([literature.printed_page(r, i) for i, r in enumerate(raws, 1)])
        flat += [(f, printed[i], r) for i, r in enumerate(raws)]
    # alla rubriker i ordning: (sidindex, position, nummer)
    heads = []
    for si, (_, _, text) in enumerate(flat):
        for m in literature.ENTRY.finditer(text):
            heads.append((si, m.start(), int(m.group(1))))
    # stigande nummer: behåll den längsta stigande följden (hänvisningar och fotnoter faller bort)
    best: list[int] = []
    prev: list[int] = [-1] * len(heads)
    tails: list[int] = []
    import bisect
    for i, h in enumerate(heads):
        keys = [heads[t][2] for t in tails]
        j = bisect.bisect_left(keys, h[2])
        if j > 0:
            prev[i] = tails[j - 1]
        if j == len(tails):
            tails.append(i)
        else:
            tails[j] = i
    k = tails[-1] if tails else -1
    while k >= 0:
        best.append(k)
        k = prev[k]
    keep = [heads[i] for i in reversed(best)]
    ut = []
    for n, (si, pos, num) in enumerate(keep):
        end = keep[n + 1] if n + 1 < len(keep) else (len(flat) - 1, len(flat[-1][2]), None)
        delar, pages, files = [], [], []
        for sj in range(si, end[0] + 1):
            f, pg, text = flat[sj]
            a = pos if sj == si else 0
            b = end[1] if sj == end[0] else len(text)
            if b > a:
                delar.append(f"[[sida {pg}]]\n" + text[a:b])  # sidmarkör: agenterna anger sidan ur den
                pages.append(pg)
                files.append(f)
        sig = f"{prefix} {num}"
        text = "\n".join(delar).strip()
        trunk = len(text) > MAX_TECKEN  # sista artikeln i en fil kan dra med sig register och tillägg
        text = text[:MAX_TECKEN]
        ut.append({"signum": sig, "i_rundata": fold_signum(sig) in signa, "work": work["id"],
                   "files": sorted(set(files)), "pages": pages, "trunkerad": trunk, "text": text})
    stat = {"trunkerade": [a["signum"] for a in ut if a["trunkerad"]], "rubriker": len(heads), "artiklar": len(ut), "i_rundata": sum(a["i_rundata"] for a in ut),
            "nummer_min": keep[0][2] if keep else None, "nummer_max": keep[-1][2] if keep else None,
            "luckor": [x for x in range(keep[0][2], keep[-1][2] + 1) if x not in {h[2] for h in keep}][:50] if keep else []}
    return ut, stat


def main() -> None:
    signa = {fold_signum(r["signum"]): r["signum"] for r in store().inscriptions}
    works = {w["id"]: w for w in literature._load(literature.CATALOG).get("works") or []}
    os.makedirs(UT, exist_ok=True)
    for wid in sys.argv[1:]:
        ut, stat = artiklar(works[wid], signa)
        with open(os.path.join(UT, f"{wid}.jsonl"), "w", encoding="utf-8") as fh:
            for a in ut:
                fh.write(json.dumps(a, ensure_ascii=False) + "\n")
        print(wid, json.dumps(stat, ensure_ascii=False))


if __name__ == "__main__":
    main()
