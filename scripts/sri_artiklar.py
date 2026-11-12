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
            rad = text[m.start():text.find("\n", m.start()) if "\n" in text[m.start():] else len(text)]
            bokst = [c for c in rad if c.isalpha()]
            overst = text[:m.start()].count("\n") - len(re.findall(r"\n\s*\n", text[:m.start()])) <= 3 or \
                len([x for x in text[:m.start()].splitlines() if x.strip()]) <= 2
            versaler = bool(bokst) and sum(c.isupper() for c in bokst) / len(bokst) > 0.6
            sidnr = bool(re.search(r"\s{3,}\d{1,4}\s*$", rad)) or len(literature.ENTRY.findall(rad)) > 1
            if overst and (versaler or sidnr):
                continue  # sidhuvud ("311—312. H A R G , SKÅNELA SN.   25"), inte artikelns rubrik
            a = int(m.group(1))
            b = int(m.group(2)) if m.group(2) and 0 < int(m.group(2)) - a <= 12 else a  # "309—311."
            heads.append((si, m.start(), a, b))
    if work.get("entry_range"):  # bandets egna nummer; andra numrerade listor (inledning, register) faller bort
        lo, hi = work["entry_range"]
        heads = [h for h in heads if lo <= h[2] <= hi]
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
    # lösa nummer före bandets första artikel ("1.", "2." i en inledning): ett hopp på över 100 bland de första
    # rubrikerna betyder att det som står före hoppet inte är artiklar
    for i in range(min(10, len(keep)) - 1):
        if keep[i + 1][2] - keep[i][2] > 100:
            keep = keep[i + 1:]
            break
    egna = {h[2] for h in keep if h[2] == h[3]}
    ut = []
    for n, (si, pos, num, sista) in enumerate(keep):
        end = keep[n + 1] if n + 1 < len(keep) else (len(flat) - 1, len(flat[-1][2]), None, None)
        delar, pages, files = [], [], []
        for sj in range(si, end[0] + 1):
            f, pg, text = flat[sj]
            a = pos if sj == si else 0
            b = end[1] if sj == end[0] else len(text)
            if b > a:
                delar.append(f"[[sida {pg}]]\n" + text[a:b])  # sidmarkör: agenterna anger sidan ur den
                pages.append(pg)
                files.append(f)
        text = "\n".join(delar).strip()
        trunk = len(text) > MAX_TECKEN  # sista artikeln i en fil kan dra med sig register och tillägg
        text = text[:MAX_TECKEN]
        omfattar = [f"{prefix} {x}" for x in range(num, sista + 1)]
        for x, sig in zip(range(num, sista + 1), omfattar):
            if sista > num and x in egna:
                continue  # numret har en egen artikel  # en artikel om flera stenar läggs ut på var och en
            ut.append({"signum": sig, "i_rundata": fold_signum(sig) in signa, "work": work["id"],
                       "files": sorted(set(files)), "pages": pages, "trunkerad": trunk, "omfattar": omfattar,
                       "text": text})
    stat = {"trunkerade": [a["signum"] for a in ut if a["trunkerad"]], "rubriker": len(heads), "artiklar": len(ut), "i_rundata": sum(a["i_rundata"] for a in ut),
            "nummer_min": keep[0][2] if keep else None, "nummer_max": keep[-1][2] if keep else None,
            "luckor": [x for x in range(keep[0][2], keep[-1][3] + 1)
                       if x not in {int(a["signum"].split()[-1]) for a in ut}] if keep else []}
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
