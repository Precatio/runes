"""A2, tillägg 1: D4-täckning och D4-val, skrivna innan något läggs mot stenarna eller gravfälten.

Läser bara D4-tabellen (data/raa/d4_inventeringsar_socken.csv) och rådata för fältdatumen. Runstenssocknarna
används bara som flagga för täckningen, som i D4 och i analysplanen A2. Inga stenantal, gravfält eller kovariater läses.

Skriver utdata/registret/d4_tackning.json och utdata/registret/d4_val.json.
Kör: .venv/bin/python scripts/a2_d4_tackning.py
"""
from __future__ import annotations

import collections
import csv
import datetime as dt
import hashlib
import json
import statistics as st
from pathlib import Path

ROT = Path(__file__).resolve().parents[1]
D4 = ROT / "data/raa/d4_inventeringsar_socken.csv"
RA = Path("/Volumes/2TB/Antigrvity/Runes/downloads/kmr_faltdatum/faltdatum.jsonl")
UT = ROT / "utdata/registret"
UTANFOR = {"Skåne", "Blekinge", "Halland"}  # DR-signum, utanför Vitkis svenska korpus
GRAVTYPER = {"Gravfält", "Hög", "Stensättning", "Röse"}
TILLAGG = ROT / "analysplaner/2027-02-A2-tillagg-1-inventeringsar.md"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def ar(r: dict) -> list[int]:
    return [int(y) for y in r["faltdatum_ar"].split()] if r["faltdatum_ar"] else []


def main() -> None:
    rows = [r for r in csv.DictReader(D4.open(encoding="utf-8")) if r["lan"] not in UTANFOR]
    rs = [r for r in rows if r["runstenssocken"] == "1"]

    grav = collections.Counter()
    for line in RA.open(encoding="utf-8"):
        d = json.loads(line)
        if d["lan"] in UTANFOR:
            continue
        if d["lamningstyp"] in GRAVTYPER and d["faltdatum"]:
            grav[(d["lan"], d["socken"])] += 1

    def andel(a: int, b: int) -> float:
        return round(a / b, 4) if b else 0.0

    urval = sum(int(r["n_urval"] or 0) for r in rows)
    med_ar = sum(int(r["n_faltdatum"] or 0) for r in rows)

    def grupp(g: list[dict]) -> dict:
        flagga = [sum(y >= 1974 for y in ar(r)) >= len(ar(r)) / 2 for r in g if ar(r)]
        return {
            "socknar": len(g),
            "minst_5_faltdatum_alla_typer": sum(int(r["n_faltdatum"] or 0) >= 5 for r in g),
            "minst_5_faltdatum_gravtyper": sum(grav[(r["lan"], r["socken"])] >= 5 for r in g),
            "minst_3_faltdatum_gravtyper": sum(grav[(r["lan"], r["socken"])] >= 3 for r in g),
            "osakerhet": dict(collections.Counter(r["osakerhet"] for r in g)),
            "period": dict(collections.Counter(r["period"] or "saknas" for r in g)),
            "reviderad_enligt_planen_andel": andel(sum(flagga), len(flagga)),
            "forstagangsar_i_texten_till_1977": sum(
                bool(r["text_tidigaste"]) and int(r["text_tidigaste"]) <= 1977 for r in g),
        }

    per_lan = {}
    avvik_alla, avvik_till_2003 = [], []
    by = collections.defaultdict(list)
    for r in rows:
        if r["osakerhet"] in ("låg", "medel") and r["huvudar"]:
            by[r["lan"] or "(utan län)"].append(int(r["huvudar"]))
    for lan, v in sorted(by.items()):
        v2 = [y for y in v if y <= 2003]
        per_lan[lan] = {"socknar": len(v), "median": st.median(v), "sd": round(st.pstdev(v), 1),
                        "efter_2003": sum(y > 2003 for y in v)}
        avvik_alla += [y - st.mean(v) for y in v]
        if len(v2) > 1:
            avvik_till_2003 += [y - st.mean(v2) for y in v2]

    efter = [int(r["huvudar"]) for r in rows if r["huvudar"] and int(r["huvudar"]) > 2003]
    tack = {
        "skriven": dt.date.today().isoformat(),
        "studieomrade": "alla län utom Skåne, Blekinge och Halland",
        "d4_fil": str(D4.relative_to(ROT)), "d4_sha256": sha(D4),
        "radata": str(RA), "radata_sha256": sha(RA),
        "poster_i_urvalet": urval, "poster_med_ar": med_ar, "andel_poster_med_ar": andel(med_ar, urval),
        "alla_socknar": grupp(rows),
        "runstenssocknar": grupp(rs),
        "huvudar_inom_lan_sd_ar": round(st.pstdev(avvik_alla), 1),
        "huvudar_inom_lan_sd_ar_till_2003": round(st.pstdev(avvik_till_2003), 1),
        "efter_2003": {"socknar": len(efter), "median": st.median(efter), "min": min(efter), "max": max(efter)},
        "per_lan_lag_eller_medel_osakerhet": per_lan,
    }
    rs_n = len(rs)
    krav_f = {
        "planens_D4F_gravtyper": {
            "krav_80_procent_runstenssocknar_minst_5": andel(tack["runstenssocknar"]["minst_5_faltdatum_gravtyper"], rs_n),
            "klarar": tack["runstenssocknar"]["minst_5_faltdatum_gravtyper"] / rs_n >= 0.80},
        "tillagg_D4F_alla_typer": {
            "krav_70_procent_poster_med_ar": tack["andel_poster_med_ar"],
            "krav_80_procent_runstenssocknar_minst_5": andel(tack["runstenssocknar"]["minst_5_faltdatum_alla_typer"], rs_n),
            "klarar": tack["andel_poster_med_ar"] >= 0.70
            and tack["runstenssocknar"]["minst_5_faltdatum_alla_typer"] / rs_n >= 0.80},
    }
    tack["krav"] = krav_f
    val = {
        "skriven": tack["skriven"],
        "tillagg": str(TILLAGG.relative_to(ROT)),
        "variant": "D4-F (alla typer), enligt tillägg 1" if krav_f["tillagg_D4F_alla_typer"]["klarar"] else "D4-H",
        "matt": "huvudar = senast systematiskt inventerad (ofta revideringsinventeringen)",
        "d4_fil": tack["d4_fil"], "d4_sha256": tack["d4_sha256"],
        "hamtdatum_faltdatum": "2026-11-11",
    }
    UT.mkdir(parents=True, exist_ok=True)
    (UT / "d4_tackning.json").write_text(json.dumps(tack, ensure_ascii=False, indent=1), encoding="utf-8")
    (UT / "d4_val.json").write_text(json.dumps(val, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: tack[k] for k in ("andel_poster_med_ar", "runstenssocknar", "huvudar_inom_lan_sd_ar",
                                           "huvudar_inom_lan_sd_ar_till_2003", "efter_2003", "krav")},
                     ensure_ascii=False, indent=1))
    print("val:", val["variant"])


if __name__ == "__main__":
    main()
