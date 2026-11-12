"""Kontroll av SRI-utplockningen (A1, tillägg 1): citat mot texten, stickprov och träffsäkerhet.

    .venv/bin/python scripts/sri_fakta_kontroll.py sammanstall sri3   slår ihop delarna, kollar varje citat mot artikeln,
                                                                       stryker uppgifter vars citat inte hittas, lottar
                                                                       stickprovet (60 stenar, slumpfrö 2026) och skriver
                                                                       granskningsunderlaget
    (lägg till 2 sist för runda 2)
    .venv/bin/python scripts/sri_fakta_kontroll.py utfall sri3         räknar träffsäkerheten per fältgrupp ur granskningen
                                                                       (och Viktors kontroll, som går före)

Citat och artikeltext är SRI:s text och ligger utanför repot (/Volumes/2TB/Antigrvity/Runes/downloads/sri_fakta/).
Bara siffrorna skrivs i repots utdata/sri_fakta/<verk>_kontroll.json (git-ignorerat som resten av utdata/).
"""
from __future__ import annotations

import glob
import json
import math
import os
import random
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = "/Volumes/2TB/Antigrvity/Runes/downloads/sri_artiklar"
FAKTA = "/Volumes/2TB/Antigrvity/Runes/downloads/sri_fakta"
UTDATA = os.path.join(ROOT, "utdata", "sri_fakta")
SEED, N_STICK = 2026, 60
RUNDOR = {1: {"suffix": "", "delar": "delar", "seed": 2026}, 2: {"suffix": "_r2", "delar": "delar_r2", "seed": 2028}}
# runda 2 (not 1 till A1-tillägg 1, 2026-11-12): ny instruktion, nytt stickprov bland stenar som inte låg i runda 1
FALT = ["lage_vid_utgavan", "ursprunglig_plats_text", "flyttningar", "forsvunnen", "aterfunnen", "inmurad", "fragment",
        "kallor_i_ordning", "samma_sten_som", "datering_text"]
GRUPPER = {"läget": ["lage_vid_utgavan", "ursprunglig_plats_text", "inmurad"], "flyttningarna": ["flyttningar"],
           "försvunnen och återfunnen": ["forsvunnen", "aterfunnen"], "samma sten": ["samma_sten_som"]}
LAGE = {"ursprunglig plats", "flyttad", "försvunnen", "okänt"}
ORSAK = {"kyrkbygge eller restaurering", "vägbygge", "odling, dikning eller annat jordbruk", "samling eller museum",
         "återresning på samma plats eller i närheten", "annat", "okänd"}


def norm(s: str) -> str:
    s = re.sub(r"\[\[sida [^\]]*\]\]", " ", s)
    s = re.sub(r"[-‐­]\s*\n\s*", "", s)  # avstavning över radbrytning
    s = s.replace("»", '"').replace("«", '"').replace("”", '"').replace("“", '"').replace("’", "'")
    return re.sub(r"\s+", " ", s).strip().lower()


def alnum(s: str) -> str:
    return re.sub(r"[\W_]+", "", s)


def finns(citat: str, text_n: str, text_t: str) -> bool:
    c = norm(citat or "")
    if len(c) < 4:
        return False
    if c in text_n:
        return True
    # OCR sprider bokstäver ("ä r") och avstavningen skrivs olika ("ut- taget"): jämför bara bokstäver och siffror
    return len(alnum(c)) >= 12 and alnum(c) in text_t


def poster(rad: dict):
    """(fält, index, post) för varje ifylld uppgift."""
    for f in FALT:
        v = rad.get(f)
        if isinstance(v, list):
            for i, p in enumerate(v):
                yield f, i, p
        elif isinstance(v, dict):
            yield f, None, v


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if not n:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(c - h, 4), round(c + h, 4))


def sammanstall(verk: str, runda: int = 1) -> None:
    R = RUNDOR[runda]
    art = {a["signum"]: a for a in map(json.loads, open(os.path.join(ART, f"{verk}.jsonl"), encoding="utf-8"))}
    rader, fel = {}, []
    for p in sorted(glob.glob(os.path.join(FAKTA, R["delar"], f"{verk}_*.jsonl"))):
        for ln in open(p, encoding="utf-8"):
            if not ln.strip():
                continue
            try:
                r = json.loads(ln)
            except json.JSONDecodeError as e:
                fel.append(f"{os.path.basename(p)}: ogiltig JSON ({e})")
                continue
            rader[r.get("signum")] = r
    saknas = sorted(set(art) - set(rader))
    okanda = sorted(set(rader) - set(art))
    strukna, behallna, schemafel = [], 0, []
    for sig, r in rader.items():
        if sig not in art:
            continue
        t = art[sig]["text"]
        tn, tt = norm(t), alnum(norm(t))
        lv = (r.get("lage_vid_utgavan") or {}).get("varde")
        if lv is not None and lv not in LAGE:
            schemafel.append(f"{sig}: lage_vid_utgavan '{lv}'")
        for fl in r.get("flyttningar") or []:
            if fl.get("orsak") not in ORSAK:
                schemafel.append(f"{sig}: orsak '{fl.get('orsak')}'")
        for f, i, post in list(poster(r)):
            if finns(post.get("citat"), tn, tt):
                behallna += 1
                continue
            strukna.append({"signum": sig, "falt": f, "citat": (post.get("citat") or "")[:120]})
            if i is None:
                r[f] = None
            else:
                r[f][i] = None
        for f in FALT:
            if isinstance(r.get(f), list):
                r[f] = [p for p in r[f] if p]
    with open(os.path.join(FAKTA, f"{verk}.jsonl"), "w", encoding="utf-8") as fh:
        for sig in sorted(rader, key=lambda s: int(re.sub(r"\D", "", s.split()[-1]) or 0)):
            if sig in art:
                fh.write(json.dumps(rader[sig], ensure_ascii=False) + "\n")
    # stickprovet: lottas bland bandets artiklar som har en utplockning
    pool = sorted(s for s in art if s in rader)
    if runda > 1:  # stenar som granskades i tidigare rundor lottas inte igen
        tidigare = set()
        for r0 in range(1, runda):
            p0 = os.path.join(FAKTA, "granskning", f"{verk}_stickprov{RUNDOR[r0]['suffix']}.jsonl")
            tidigare |= {json.loads(x)["signum"] for x in open(p0, encoding="utf-8")}
        pool = [x for x in pool if x not in tidigare]
    stick = sorted(random.Random(R["seed"]).sample(pool, min(N_STICK, len(pool))))
    os.makedirs(os.path.join(FAKTA, "granskning"), exist_ok=True)
    with open(os.path.join(FAKTA, "granskning", f"{verk}_stickprov{R['suffix']}.jsonl"), "w", encoding="utf-8") as fh:
        for s in stick:
            fh.write(json.dumps({"signum": s, "pages": art[s]["pages"], "text": art[s]["text"], "utplockning": rader[s]},
                                ensure_ascii=False) + "\n")
    rapport = {"verk": verk, "artiklar": len(art), "utplockade": len(set(rader) & set(art)), "saknas": saknas,
               "okanda_signum": okanda, "json_fel": fel, "schemafel": schemafel[:50], "n_schemafel": len(schemafel),
               "uppgifter_behallna": behallna, "uppgifter_strukna": len(strukna),
               "andel_strukna": round(len(strukna) / max(1, behallna + len(strukna)), 4),
               "strukna_per_falt": dict(sorted({f: sum(1 for x in strukna if x["falt"] == f) for f in FALT}.items())),
               "stickprov": stick, "slumpfro": R["seed"], "runda": runda}
    os.makedirs(UTDATA, exist_ok=True)
    json.dump(rapport, open(os.path.join(UTDATA, f"{verk}_kontroll{R['suffix']}.json"), "w", encoding="utf-8"), ensure_ascii=False,
              indent=1)
    json.dump(strukna, open(os.path.join(FAKTA, f"{verk}_strukna.json"), "w", encoding="utf-8"), ensure_ascii=False,
              indent=1)
    print(json.dumps({k: v for k, v in rapport.items() if k not in ("stickprov", "schemafel")}, ensure_ascii=False))


def utfall(verk: str, runda: int = 1) -> None:
    R = RUNDOR[runda]
    """Granskningen: granskning/<verk>_bedomning.jsonl, en rad per sten:
    {"signum", "bedomning": {fält: "rätt"|"fel"|"saknat"}}; Viktors i <verk>_viktor.jsonl går före."""
    g = {r["signum"]: r for r in map(json.loads, open(os.path.join(FAKTA, "granskning", f"{verk}_bedomning{R['suffix']}.jsonl"),
                                                      encoding="utf-8"))}
    vp = os.path.join(FAKTA, "granskning", f"{verk}_viktor{R['suffix']}.jsonl")
    if os.path.exists(vp):
        for r in map(json.loads, open(vp, encoding="utf-8")):
            g.setdefault(r["signum"], {"bedomning": {}})["bedomning"].update(r["bedomning"])
    ut = {}
    for grupp, falt in GRUPPER.items():
        k = n = 0
        for r in g.values():
            for f in falt:
                b = r["bedomning"].get(f)
                if b in ("rätt", "fel", "saknat"):
                    n += 1
                    k += b == "rätt"
        lo, hi = wilson(k, n)
        ut[grupp] = {"ratt": k, "n": n, "andel": round(k / n, 4) if n else None, "wilson95": [lo, hi],
                     "klarar": bool(n) and k / n >= 0.95 and lo >= 0.88}
    rp = os.path.join(UTDATA, f"{verk}_kontroll{R['suffix']}.json")
    rapport = json.load(open(rp, encoding="utf-8"))
    rapport["granskning"] = ut
    rapport["viktor_kontroll"] = os.path.exists(vp)
    json.dump(rapport, open(rp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(ut, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    {"sammanstall": sammanstall, "utfall": utfall}[sys.argv[1]](sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 1)
