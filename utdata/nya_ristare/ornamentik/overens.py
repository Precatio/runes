"""Ornamentik: hur väl stämmer de två läsarna överens? (instrumentprov – använder inget facit)

    .venv/bin/python utdata/nya_ristare/ornamentik/overens.py data/cache/hander/ornamentik/kodning_<namn>.json

Per fält: täckning (andel stenar där båda läsarna angav ett värde, inte "osäkert"), överensstämmelse och Cohens kappa bland
dem. Läsarnas stilbedömning jämförs också med Rundatas stilgrupp.
"""
import json
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)

FIELDS = ["djurhuvud", "antal_djur", "huvud_vy", "oga", "nackflik", "lappflik", "mun", "svans", "fotter", "huvud_svans", "kontur", "koppel",
          "flatverk", "fyrfota", "orm_extra", "manniska_mask", "kors", "stil"]
UNSURE = {"osäkert", "osakert", "osaker", "osäker", "", None, "oklart"}


def norm(v):
    v = (v or "").strip().lower().replace("ä", "a").replace("å", "a").replace("ö", "o")
    return None if v in {"osakert", "osaker", "", "oklart"} else v


def kappa(pairs):
    n = len(pairs)
    if n < 2:
        return None
    po = sum(a == b for a, b in pairs) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum(ca[k] * cb.get(k, 0) for k in ca) / n / n
    return None if pe >= 1 else (po - pe) / (1 - pe)


def by_stone(path):
    runs = json.load(open(path, encoding="utf-8"))
    out = defaultdict(dict)
    for r in runs:
        if not r or not r.get("stenar"):
            continue
        for s in r["stenar"]:
            out[s["signum"].strip()][r["coder"]] = s
    return out


def agreement(codes, stones=None):
    res = {}
    for f in FIELDS:
        pairs, n = [], 0
        for sig, c in codes.items():
            if stones is not None and sig not in stones or len(c) < 2:
                continue
            a, b = c[1], c[2]
            if norm(a.get("bild")) == "ingen" or norm(b.get("bild")) == "ingen":
                continue
            n += 1
            x, y = norm(a.get(f)), norm(b.get(f))
            if x and y:
                pairs.append((x, y))
        k = kappa(pairs)
        res[f] = {"stenar": n, "tackning": round(len(pairs) / n, 2) if n else None,
                  "lika": round(sum(a == b for a, b in pairs) / len(pairs), 2) if pairs else None,
                  "kappa": round(k, 2) if k is not None else None}
    return res


if __name__ == "__main__":
    codes = by_stone(sys.argv[1])
    res = agreement(codes)
    for f, r in res.items():
        print(f"{f:14s} {r}")
    from utdata.nya_ristare.belagg import load
    st = load()
    style = dict(zip(st.sig, st.corp["style"].astype(str).str.replace("\xa0", " ").str.replace(" ", "").str.strip()))
    hit = tot = 0
    for sig, c in codes.items():
        rs = style.get(sig)
        if not isinstance(rs, str) or rs in ("nan", "None", ""):
            continue
        for k, v in c.items():
            s = norm(v.get("stil"))
            if s:
                tot += 1
                hit += s.replace(" ", "") == rs.lower()
    print(f"stil mot Rundata: {hit}/{tot}")
    for sig, c in sorted(codes.items()):
        diff = [f for f in FIELDS if len(c) == 2 and norm(c[1].get(f)) != norm(c[2].get(f))]
        print(sig, style.get(sig), "olika:", diff)
