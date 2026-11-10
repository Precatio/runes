"""Självkontroll av ristningens riktning enligt den låsta planen analysplaner/2026-11-10-sjalvkontroll-riktning.md.

    .venv/bin/python utdata/riktning/sjalvkontroll.py --klassa   Skriver bara sjalvkontroll_vagklasser.csv (först).
    .venv/bin/python utdata/riktning/sjalvkontroll.py            Räknar S0–S3 och det beskrivande; skriver sjalvkontroll.json.

Förutsätter data/raa/lamningar_vag.csv (utdata/riktning/hamta_vagar.py)."""
import json
import os
import re
import sys

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(OUT, "..", ".."))
sys.path.insert(0, ROOT)

NPERM = 9999
SEED = 2026
GAMMAL = re.compile(r"hålväg|vägbank|vadställe|kavelbro|förhistori|järnålder|vikingatid|bronsålder|medeltid")
UNG = re.compile(r"banvall|järnväg|fäbod|militärväg|valv")
HALV_BANK = re.compile(r"hålväg|vägbank")
RUNSTEN = re.compile(r"runsten|runristning")
FLYTT = re.compile(r"återrest|återupprest|rest upp|restes upp|rests upp|nyrest|rests på nytt|restes på nytt|uppsatt|"
                   r"uppställd|lagad|lagades|lagats|reparerad|restaurer|flyttad|flyttades|flyttats|tidigare stått|"
                   r"tidigare stod|ursprungligen stått|ursprungligen stod|påträffad|hittad|hittades|återfunnen|"
                   r"återfanns|låg tidigare|kullfallen|omkullfallen", re.I)
NEG = {"ej", "inte", "icke", "aldrig", "knappast", "önskar"}
KLASSER = os.path.join(OUT, "sjalvkontroll_vagklasser.csv")


def klassa() -> pd.DataFrame:
    v = pd.read_csv(os.path.join(ROOT, "data", "raa", "lamningar_vag.csv"))
    b = v.beskrivning.fillna("").str.lower()
    v["gammal"] = (v.type.isin(["färdväg", "färdvägssystem", "bro"]) & b.str.contains(GAMMAL) & ~b.str.contains(UNG)).astype(int)
    v["halvag_vagbank"] = (v.gammal.astype(bool) & b.str.contains(HALV_BANK)).astype(int)
    v["nämner_runsten"] = b.str.contains(RUNSTEN).astype(int)
    v[["id", "type", "lon", "lat", "lan", "kommun", "landskap", "label", "gammal", "halvag_vagbank", "nämner_runsten"]].to_csv(KLASSER, index=False)
    return v


if "--klassa" in sys.argv:
    v = klassa()
    print("vägar", len(v), "gamla", int(v.gammal.sum()), v[v.gammal == 1].type.value_counts().to_dict(),
          "hålväg/vägbank", int(v.halvag_vagbank.sum()), "gamla som nämner runsten", int((v.gammal & v.nämner_runsten).sum()))
    sys.exit(0)

from src import places  # noqa: E402

assert os.path.exists(KLASSER), "kör --klassa först"
vk = pd.read_csv(KLASSER)

# --- stenarna, en rad per sten ---
d0 = pd.read_csv(os.path.join(OUT, "stenar.csv"))
assert len(d0) == 219
assert (d0.groupby("signum").riktning.nunique() == 1).all()
d = d0.sort_values("vag_text", na_position="last").drop_duplicates("signum").sort_index().reset_index(drop=True)
assert len(d) == 214
d["vag"] = d.vag_text.fillna(d.vag_reg)

# --- län via kommunen i Rundata ---
k2l = vk[vk.kommun.notna()].groupby("kommun").lan.agg(lambda s: s.value_counts().index[0]).to_dict()
rdl = json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]
rdm = {r["signum"]: r for r in rdl}
d["lan"] = d.signum.map(lambda s: k2l.get((rdm.get(s) or {}).get("municipality") or ""))

# --- flyttad eller omrest ---
runor = {x["signum"]: x for x in json.load(open(os.path.join(ROOT, "data", "raa", "runor_2020.json"), encoding="utf-8"))["inscriptions"]}
corp = pd.read_csv(os.path.join(ROOT, "data", "cache", "r", "corpus", "e83202e01a5e6d27", "corpus.csv"), low_memory=False).set_index("signum")
kmr = {}
for r in json.load(open(os.path.join(ROOT, "data", "raa", "kmr_runstenar.json"), encoding="utf-8"))["records"]:
    t = " ".join(" ".join(r["fields"].get(k, [])) for k in ("Beskrivning", "Placering", "Skadestatus", "Orientering"))
    for s in r["signa"]:
        kmr[s] = kmr.get(s, "") + " " + t


def flytt_text(text: str) -> list[str]:
    hits = []
    for m in FLYTT.finditer(text):
        before = [w.strip(".,;:!?()[]\"'”“").lower() for w in text[:m.start()].split()][-3:]
        if not NEG.intersection(before):
            hits.append(m.group(0).lower())
    return hits


rows = []
for s in d.signum:
    ru = runor.get(s) or {}
    txt = " ".join([kmr.get(s, ""), (rdm.get(s) or {}).get("placement") or "", (rdm.get(s) or {}).get("other") or "",
                    str(ru.get("placement") or ""), str(ru.get("original_text") or "")] + [str(n) for n in (ru.get("notes") or [])])
    hits = flytt_text(txt)
    rows.append({"r1_runor_original_false": ru.get("original") is False,
                 "r2_runor_current": ru.get("current") is not None,
                 "r3_korpus": bool(s in corp.index and (corp.moved.get(s) != 0 or corp.lost.get(s) != 0)),
                 "r4_text": bool(hits), "text_traffar": "; ".join(hits)})
fl = pd.DataFrame(rows)
d = pd.concat([d, fl], axis=1)
d["flyttad"] = d[["r1_runor_original_false", "r2_runor_current", "r3_korpus", "r4_text"]].any(axis=1)
n_saknas_korpus = int((~d.signum.isin(corp.index)).sum())

# --- bäringar ---
xy = places._xy(d.lat.to_numpy(float), d.lon.to_numpy(float))


def bearing_to(sub: pd.DataFrame, radius: float) -> np.ndarray:
    pts = places._xy(sub.lat.to_numpy(float), sub.lon.to_numpy(float))
    dist, idx = cKDTree(pts).query(xy)
    dx, dy = pts[idx, 0] - xy[:, 0], pts[idx, 1] - xy[:, 1]
    return np.where(dist <= radius, (np.degrees(np.arctan2(dx, dy)) + 360) % 360, np.nan)


old = vk[vk.gammal == 1]
d["vag_gammal"] = bearing_to(old, 500)
d["vag_gammal_300"] = bearing_to(old, 300)
d["vag_gammal_1000"] = bearing_to(old, 1000)
d["vag_gammal_ej_runsten"] = bearing_to(old[old.nämner_runsten == 0], 500)
d["vag_halvag_bank"] = bearing_to(vk[vk.halvag_vagbank == 1], 500)


def test(df: pd.DataFrame, target: str, stratum: str = "province") -> dict:
    x = df[df[target].notna() & df[stratum].notna()].reset_index(drop=True)
    if len(x) < 5:
        return {"n": len(x)}
    f, t = x.riktning.to_numpy(), x[target].to_numpy()
    groups = list(x.groupby(stratum).indices.values())
    rng = np.random.default_rng(SEED)
    stat = lambda ff: np.cos(np.radians(ff - t)).mean()
    obs = stat(f)
    sims = np.empty(NPERM)
    for i in range(NPERM):
        idx = np.arange(len(x))
        for g in groups:
            idx[g] = rng.permutation(g)
        sims[i] = stat(f[idx])
    r = {"n": len(x), "medel_cos": float(obs), "vantat": float(sims.mean()),
         "andel_inom_45": float((np.abs((f - t + 180) % 360 - 180) <= 45).mean()),
         "p": float((1 + (sims >= obs).sum()) / (NPERM + 1))}
    r["haller"] = bool(r["medel_cos"] > r["vantat"] and r["p"] < 0.05)
    return r


S = {}
S["S0"] = test(d, "vag")
S["S1"] = test(d, "vag_gammal")
if S["S1"]["n"] < 30:
    S["S1"]["haller"] = None
    S["S1"]["status"] = "kan inte prövas"
S["S2"] = test(d, "vag", "lan")
S["S3"] = test(d[~d.flyttad], "vag")

besk = {"S1_S3_inom_lan": test(d[~d.flyttad], "vag_gammal", "lan"),
        "S1_300m": test(d, "vag_gammal_300"), "S1_1km": test(d, "vag_gammal_1000"),
        "S1_utan_runstensvagar": test(d, "vag_gammal_ej_runsten"), "S1_halvag_vagbank": test(d, "vag_halvag_bank"),
        "halvor": {h: {"S0": test(d[d.half == h], "vag"), "S1": test(d[d.half == h], "vag_gammal"),
                       "S2": test(d[d.half == h], "vag", "lan"), "S3": test(d[(d.half == h) & ~d.flyttad], "vag")} for h in "AB"}}
for k in ("S1_S3_inom_lan", "S1_300m", "S1_1km", "S1_utan_runstensvagar", "S1_halvag_vagbank"):
    besk[k].pop("haller", None)
for h in "AB":
    for k in besk["halvor"][h].values():
        k.pop("haller", None)

info = {"stenar": len(d), "med_vag": int(d.vag.notna().sum()), "med_textvag": int(d.vag_text.notna().sum()),
        "utan_lan": int(d.lan.isna().sum()), "lan": d.lan.value_counts().to_dict(),
        "flyttade": int(d.flyttad.sum()), "flyttade_med_vag": int((d.flyttad & d.vag.notna()).sum()),
        "flyttregler": {c: int(d[c].sum()) for c in ("r1_runor_original_false", "r2_runor_current", "r3_korpus", "r4_text")},
        "flyttregler_med_vag": {c: int((d[c] & d.vag.notna()).sum()) for c in ("r1_runor_original_false", "r2_runor_current", "r3_korpus", "r4_text")},
        "saknas_i_korpus": n_saknas_korpus, "gamla_vagar": int(len(old)),
        "med_gammal_vag_500": int(d.vag_gammal.notna().sum()),
        "gammal_och_textvag_samma_sten": int((d.vag_gammal.notna() & d.vag_text.notna()).sum()),
        "S1_typer": old.set_index(old.index).type.value_counts().to_dict()}
d.drop(columns=["lat", "lon"]).to_csv(os.path.join(OUT, "sjalvkontroll_stenar.csv"), index=False)
out = {"plan": "analysplaner/2026-11-10-sjalvkontroll-riktning.md", "info": info, "prov": S, "beskrivande": besk}
json.dump(out, open(os.path.join(OUT, "sjalvkontroll.json"), "w"), ensure_ascii=False, indent=1)


def fmt(r):
    if "medel_cos" not in r:
        return f"n {r['n']} (för få)"
    return (f"n {r['n']:3d}  cos {r['medel_cos']:.3f} mot {r['vantat']:.3f}  inom 45° {r['andel_inom_45']:.2f}  p {r['p']:.4f}"
            + ("" if "haller" not in r else f"  {'HÅLLER' if r['haller'] else ('KAN INTE PRÖVAS' if r['haller'] is None else 'HÅLLER INTE')}"))


print(json.dumps(info, ensure_ascii=False))
for k, r in S.items():
    print(k, fmt(r))
for k in ("S1_S3_inom_lan", "S1_300m", "S1_1km", "S1_utan_runstensvagar", "S1_halvag_vagbank"):
    print(" ", k, fmt(besk[k]))
for h in "AB":
    for k, r in besk["halvor"][h].items():
        print("  halva", h, k, fmt(r))
