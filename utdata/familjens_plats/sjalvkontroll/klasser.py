"""Självkontrollen (analysplaner/2026-11-10-sjalvkontroll-gravfalt.md), steg 1: klassar registrets gravfält (V = granskat
gravfält, Y = yngre järnålderns former) och skriver antalen i klasser.csv INNAN gravfälten läggs mot stenarna.
Klassningen (funktionen klass) används också av data.py.
    .venv/bin/python utdata/familjens_plats/sjalvkontroll/klasser.py"""
from __future__ import annotations

import collections
import csv
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

SAFE_TYPES = {"Hög", "Grav markerad av sten/block", "Stenkrets/stenrad", "Stenkammargrav"}
SAFE_SETTING_FORMS = {"Treudd", "Kvadratisk", "Rektangulär", "Triangulär", "Skeppsformig"}


def components(s: str) -> list[tuple[str, str]]:
    """'Hög - Form: Rund, antal 2.Stensättning - Konstruktion: Övertorvad, Form: Treudd, antal 1' →
    [('Hög', 'Rund'), ('Stensättning', 'Treudd')]."""
    out = []
    for part in re.split(r"\.(?=[A-ZÅÄÖ])", s or ""):
        part = part.strip()
        if not part:
            continue
        typ = re.sub(r",\s*antal.*$", "", part.split(" - ")[0]).strip()
        m = re.search(r"Form: ([^,]+)", part)
        out.append((typ, m.group(1).strip() if m else ""))
    return out


def klass(row: dict) -> dict:
    comp = components(row.get("ingaende", ""))
    safe = [(t, f) for t, f in comp if t in SAFE_TYPES or (t == "Stensättning" and f in SAFE_SETTING_FORMS)]
    safe_nb = [(t, f) for t, f in safe if t != "Grav markerad av sten/block"]
    granskad = row.get("bedomning") == "Fornlämning" and row.get("aktualitet") == "Bekräftad i fält"
    yngre = any((t == "Stensättning" and f in ("Treudd", "Kvadratisk")) or (t == "Stenkrets/stenrad" and f == "Kvadratisk")
                for t, f in comp)
    V = granskad and bool(safe)
    return {"V": V, "V_utan_block": granskad and bool(safe_nb), "Y": V and yngre, "komponenter": comp}


def load() -> list[dict]:
    det = {r["id"]: r for r in csv.DictReader(open(os.path.join(ROOT, "data", "raa", "gravfalt_detaljer.csv"),
                                                   encoding="utf-8"))}
    out = []
    for r in csv.DictReader(open(os.path.join(ROOT, "data", "raa", "lamningar.csv"), encoding="utf-8")):
        if r["type"] != "gravfält":
            continue
        d = det.get(r["id"])
        k = klass(d) if d else {"V": False, "V_utan_block": False, "Y": False, "komponenter": []}
        out.append({"id": r["id"], "lat": float(r["lat"]), "lon": float(r["lon"]), "province": r["province"],
                    "detaljer": d is not None, "lan": d["lan"] if d else "", **k,
                    "bedomning": d["bedomning"] if d else "", "aktualitet": d["aktualitet"] if d else ""})
    return out


def main() -> None:
    g = load()
    rows = []

    def add(grupp, nyckel, n):
        rows.append({"grupp": grupp, "nyckel": nyckel, "antal": n})

    add("totalt", "gravfält i lamningar.csv", len(g))
    add("totalt", "med detaljer ur K-samsök", sum(x["detaljer"] for x in g))
    add("totalt", "utan detaljer", sum(not x["detaljer"] for x in g))
    add("totalt", "med ingående lämningar", sum(bool(x["komponenter"]) for x in g))
    add("klass", "V granskat gravfält", sum(x["V"] for x in g))
    add("klass", "V utan grav markerad av sten/block", sum(x["V_utan_block"] for x in g))
    add("klass", "Y yngre järnålderns former", sum(x["Y"] for x in g))
    for k, v in collections.Counter(x["bedomning"] for x in g).most_common():
        add("antikvarisk bedömning", k or "(saknas)", v)
    for k, v in collections.Counter(x["aktualitet"] for x in g).most_common():
        add("aktualitetsstatus", k or "(saknas)", v)
    comp = collections.Counter()
    for x in g:
        for t, f in set(x["komponenter"]):
            comp[f"{t} – {f or '(ingen form)'}"] += 1
    for k, v in comp.most_common():
        add("ingående form (antal gravfält)", k, v)
    lan = collections.defaultdict(lambda: [0, 0, 0])
    for x in g:
        lan[x["lan"] or "(saknas)"][0] += 1
        lan[x["lan"] or "(saknas)"][1] += x["V"]
        lan[x["lan"] or "(saknas)"][2] += x["Y"]
    for k, (n, v, y) in sorted(lan.items()):
        add("län: alla / V / Y", k, f"{n} / {v} / {y}")
    with open(os.path.join(HERE, "klasser.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["grupp", "nyckel", "antal"])
        w.writeheader()
        w.writerows(rows)
    for r in rows[:12]:
        print(r)


if __name__ == "__main__":
    main()
