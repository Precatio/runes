"""P1 och tabellen till P2 i den låsta planen analysplaner/2026-11-10-sjalvkontroll-osterled.md.
    ../../../.venv/bin/python ingvarsstenar.py   # listan (fryst efter granskning)
    ../../../.venv/bin/python analys.py          # P1, beskrivande kurva, stenar_tid.csv
    Rscript tid.R                                # P2 (modellen) → tid_resultat.json
    ../../../.venv/bin/python analys.py --samla  # slår ihop till resultat.json
"""
import csv
import json
import os
import re
import sys
from math import sqrt

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
VARLDEN = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import entities  # noqa: E402
from src.research_gaps import province  # noqa: E402
from src.styles import BY_CODE  # noqa: E402

B = 10_000
SEED = 20261110
PLACES = list(csv.DictReader(open(os.path.join(VARLDEN, "platser.csv"), encoding="utf-8")))
REGION = {p["plats"]: p["region"] for p in PLACES}
ROWS = [r for r in csv.DictReader(open(os.path.join(VARLDEN, "platser_per_text.csv"), encoding="utf-8"))
        if r["korpus"] == "runstenar_sverige"]
for r in ROWS:
    for p in REGION:
        r[p] = int(r[p])
RECS = json.load(open(os.path.join(ROOT, "data", "rundata.json")))
RECS = RECS if isinstance(RECS, list) else RECS.get("inscriptions", list(RECS.values()))
BY = {r["signum"]: r for r in RECS}
ING = list(csv.DictReader(open(os.path.join(HERE, "ingvarsstenar.csv"), encoding="utf-8")))
INGVAR = {r["signum"] for r in ING if not r["borttagen"]}
INGVAR_NARROW = {r["signum"] for r in ING if not r["borttagen"] and "a" in r["led"]}
KNUT = {r["text"] for r in ROWS if entities.EVENTS["Knútr"] in entities.extract(BY[r["text"]])["events"]}
EARLY, LATE = ("RAK", "Fp", "Pr1", "Pr2"), ("Pr3", "Pr4", "Pr5")
ORDER = EARLY + LATE


def ew(r, hits=False):
    e = w = 0
    for p, reg in REGION.items():
        v = r[p] if hits else int(r[p] > 0)
        if reg == "öster":
            e += v
        elif reg == "väster":
            w += v
    return e, w


def arr(rows, **kw):
    return np.array([ew(r, **kw) for r in rows], dtype=float).reshape(-1, 2)


def share(a):
    s = a.sum(axis=0)
    return float(s[0] / s.sum()) if s.sum() else float("nan")


def boot(a, rng):
    idx = rng.integers(0, len(a), (B, len(a)))
    sums = a[idx].sum(axis=1)
    with np.errstate(invalid="ignore"):
        vals = sums[:, 0] / sums.sum(axis=1)
    return [float(np.nanpercentile(vals, 2.5)), float(np.nanpercentile(vals, 97.5))]


def wilson(k, n, z=1.959964):
    if n == 0:
        return [float("nan")] * 2
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [c - h, c + h]


def summary(rows, rng, **kw):
    a = arr(rows, **kw)
    a = a[a.sum(axis=1) > 0]
    return {"stenar": int(len(a)), "O": float(a[:, 0].sum()), "V": float(a[:, 1].sum()), "ostandel": share(a),
            "ci": boot(a, rng)}


def stones_share(rows):
    a = arr(rows)
    a = a[a.sum(axis=1) > 0]
    k, n = int((a[:, 0] > 0).sum()), len(a)
    return {"stenar_med_ost": k, "stenar_med_ost_eller_vast": n, "andel": k / n, "wilson": wilson(k, n)}


def as_one(rows, group):
    """Gruppen räknad som en text: dess olika platser en gång."""
    rest = [r for r in rows if r["text"] not in group]
    g = [r for r in rows if r["text"] in group]
    one = {"text": "GRUPP", **{p: int(any(r[p] for r in g)) for p in REGION}}
    return rest + [one]


def p1_verdict(s):
    if s["ci"][0] > 0.5:
        return "håller"
    if s["ostandel"] > 0.5:
        return "försvagat (obestämt)"
    return "håller inte"


def style_main(rec):
    st = re.sub(r"\s*\[Gräslund muntligt\]", "", rec.get("style") or "").strip()
    st = "Fp" if st == "FP" else st
    return st if st in ORDER and not rec.get("style_uncertain") else None


def style_wide(rec):
    """Med osäkra grupper och kombinationer när alla ingående grupper ligger på samma sida om 1050."""
    s = rec.get("style") or ""
    if "KB" in s:
        return None
    codes = [("Fp" if c == "FP" else c) for c in re.findall(r"RAK|Fp|FP|Pr\d", s)]
    codes = [c for c in codes if c in ORDER]
    if not codes:
        return None
    sides = {c in LATE for c in codes}
    if len(sides) != 1:
        return None
    lo = min(BY_CODE[c]["from"] for c in codes)
    hi = max(BY_CODE[c]["to"] for c in codes)
    return {"sen": int(sides.pop()), "mitt": (lo + hi) / 2}


def landskap(rec):
    p = province(rec)
    return {"U": "Uppland", "Sö": "Södermanland", "Ög": "Östergötland"}.get(p, "övriga")


def p1(rng):
    full = summary(ROWS, rng)
    wo = [r for r in ROWS if r["text"] not in INGVAR]
    out = {"ingvarsstenar": sorted(INGVAR), "antal_ingvarsstenar": len(INGVAR),
           "antal_ingvar_med_plats": sum(1 for r in ROWS if r["text"] in INGVAR and sum(ew(r))),
           "alla": full, "utan_ingvar": summary(wo, rng)}
    out["dom"] = p1_verdict(out["utan_ingvar"])
    out["skillnad_pe"] = 100 * (out["utan_ingvar"]["ostandel"] - full["ostandel"])
    ing_rows = [r for r in ROWS if r["text"] in INGVAR]
    a = arr(ing_rows)
    out["ingvar_gruppens_platser"] = {"O": float(a[:, 0].sum()), "V": float(a[:, 1].sum())}
    east_stones = [r for r in ROWS if ew(r)[0] > 0]
    out["oststenar"] = {"alla": len(east_stones), "varav_ingvar": sum(1 for r in east_stones if r["text"] in INGVAR)}
    besk = {
        "stenandel_alla": stones_share(ROWS),
        "stenandel_utan_ingvar": stones_share(wo),
        "traffar_alla": summary(ROWS, rng, hits=True),
        "traffar_utan_ingvar": summary(wo, rng, hits=True),
        "smal_definition": {"antal": len(INGVAR_NARROW),
                            **summary([r for r in ROWS if r["text"] not in INGVAR_NARROW], rng)},
        "ingvar_som_en_text": summary(as_one(ROWS, INGVAR), rng),
        "knutsstenar": sorted(KNUT),
        "utan_knut": summary([r for r in ROWS if r["text"] not in KNUT], rng),
        "utan_ingvar_och_knut": summary([r for r in ROWS if r["text"] not in INGVAR | KNUT], rng),
    }
    pub = json.load(open(os.path.join(VARLDEN, "analys_resultat.json"), encoding="utf-8"))["beskrivande"]
    besk["sagor_publicerade"] = {k: {"ostandel": pub[k]["ostandel"], "ci": pub[k]["ci"]}
                                 for k in ("fornaldarsagor", "heimskringla", "islanningasagor") if k in pub}
    out["beskrivande"] = besk
    return out


def table():
    """En rad per sten med östlig eller västlig plats, till tid.R och kurvan."""
    rows = []
    for r in ROWS:
        e, w = ew(r)
        if e + w == 0:
            continue
        rec = BY[r["text"]]
        sm, sw = style_main(rec), style_wide(rec)
        rows.append({"signum": r["text"], "O": e, "V": w, "stil": sm or "",
                     "sen": "" if sm is None else int(sm in LATE),
                     "mitt": "" if sm is None else (BY_CODE[sm]["from"] + BY_CODE[sm]["to"]) / 2,
                     "sen_vid": "" if sw is None else sw["sen"], "mitt_vid": "" if sw is None else sw["mitt"],
                     "landskap": landskap(rec), "ingvar": int(r["text"] in INGVAR), "knut": int(r["text"] in KNUT)})
    with open(os.path.join(HERE, "stenar_tid.csv"), "w", encoding="utf-8", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0]))
        wr.writeheader()
        wr.writerows(rows)
    return rows


def curve(rows, rng):
    out = {}
    for label, keep in (("med_ingvar", lambda t: True), ("utan_ingvar", lambda t: not t["ingvar"])):
        cur = []
        for st in ORDER:
            a = np.array([[t["O"], t["V"]] for t in rows if t["stil"] == st and keep(t)], dtype=float).reshape(-1, 2)
            hits = float(a.sum())
            cur.append({"stil": st, "ar": [BY_CODE[st]["from"], BY_CODE[st]["to"]], "stenar": len(a), "O": float(a[:, 0].sum()),
                        "V": float(a[:, 1].sum()), "ostandel": share(a) if hits else None,
                        "ci": boot(a, rng) if hits >= 10 else None})
        out[label] = cur
    for label, keep in (("med_ingvar", lambda t: True), ("utan_ingvar", lambda t: not t["ingvar"])):
        for half, flag in (("tidig", 0), ("sen", 1)):
            a = np.array([[t["O"], t["V"]] for t in rows if t["sen"] == flag and keep(t)], dtype=float).reshape(-1, 2)
            out[f"{label}_{half}"] = {"stenar": len(a), "O": float(a[:, 0].sum()), "V": float(a[:, 1].sum()),
                                      "ostandel": share(a), "ci": boot(a, rng)}
    return out


def main():
    rng = np.random.default_rng(SEED)
    res = {"plan": "analysplaner/2026-11-10-sjalvkontroll-osterled.md", "p1": p1(rng)}
    rows = table()
    res["p2_tabell"] = {"stenar_med_plats": len(rows), "med_saker_stilgrupp": sum(1 for t in rows if t["stil"]),
                        "med_vid_stilgrupp": sum(1 for t in rows if t["sen_vid"] != "")}
    res["kurva"] = curve(rows, rng)
    json.dump(res, open(os.path.join(HERE, "p1_kurva.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False, indent=1)[:6000])


def collect():
    res = json.load(open(os.path.join(HERE, "p1_kurva.json"), encoding="utf-8"))
    res["p2"] = json.load(open(os.path.join(HERE, "tid_resultat.json"), encoding="utf-8"))
    json.dump(res, open(os.path.join(HERE, "resultat.json"), "w"), ensure_ascii=False, indent=1)
    print("resultat.json skriven")


if __name__ == "__main__":
    collect() if "--samla" in sys.argv else main()
