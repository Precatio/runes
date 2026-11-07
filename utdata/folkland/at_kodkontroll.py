"""Kontroll av prepositionsdraget efter läsningen av Peterson 1996 (2026-11-07) – UTANFÖR de låsta planerna, deklarerad.

Draget prep_at (src/language_profile.py, regeln "preposition") räknar *at* bara när ett personnamn följer direkt efter.
Minnesformelns *at* framför ett släktord missas därför: "æftiR "Æist, faður sinn, ok "Fastlaug at bonda sinn" (U 461)
kodas som bara æftiR. Det är just det mönster Palm (1992 s. 232) och Peterson (1996 s. 246) beskriver: *at* som andra
preposition. Den korta formen aft/æft räknas dessutom in i æftiR, fast den är den äldre formen (Peterson s. 242–244).

Skriptet bygger två rättade varianter av raderna och kör de låsta skripten at_ristare.R och at_trappa.R oförändrade på dem,
i kodkontroll/A och kodkontroll/B (originalfilerna i den här mappen rörs inte):
  A  *at* framför ett possessiv eller släktord (sinn, sina, faður, broður, bonda, sun, dottur, moður …) räknas som at
  B  som A, och stenar där minnesformeln bara har aft/æft (varken at eller æftiR) utesluts
    PYTHONPATH=. .venv/bin/python utdata/folkland/at_kodkontroll.py"""
import csv
import json
import os
import re
import shutil
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(HERE, "kodkontroll")
AT_KIN = re.compile(r"\bat (sinn|sina|sini|sinum|sinni|faður|broður|bonda|sun|dottur|moður)\b", re.I)
SHORT = re.compile(r"\b(æft|aft)\b", re.I)

rd = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json")))["inscriptions"]}
summary = {}
for variant in ("A", "B"):
    d = os.path.join(OUT, variant)
    os.makedirs(d, exist_ok=True)
    for name in ("at_rader.csv", "at_rader2.csv"):
        rows = list(csv.DictReader(open(os.path.join(HERE, name), encoding="utf-8")))
        out, changed, dropped = [], [], []
        for r in rows:
            r = dict(r)
            norm = rd[r["signum"]].get("normalization") or ""
            if r["prep_at"] == "0" and AT_KIN.search(norm):
                r["prep_at"] = "1"
                changed.append(r["signum"])
            if variant == "B" and r["prep_at"] == "0" and SHORT.search(norm) and not re.search(r"\bæftiR\b", norm):
                dropped.append(r["signum"])
                continue
            out.append(r)
        with open(os.path.join(d, name), "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(out)
        summary[variant] = {"stones": len(out), "recoded_to_at": changed, "dropped_short_form": dropped}
    for script in ("at_ristare.R", "at_trappa.R"):
        shutil.copy(os.path.join(HERE, script), d)
        subprocess.run(["Rscript", os.path.join(d, script)], check=True, capture_output=True)
    r = json.load(open(os.path.join(d, "at_ristare.json")))
    t = json.load(open(os.path.join(d, "at_trappa.json")))
    summary[variant].update({"border": r["step1"]["border"], "all": r["step1"]["all"],
                             "carvers": r["step2"]["carvers"], "ladder_all_hold": t.get("all_hold"),
                             "unmoved": t.get("unmoved")})
json.dump(summary, open(os.path.join(OUT, "sammanfattning.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for v, s in summary.items():
    b = s["border"]
    print(v, s["stones"], "stenar;", len(s["recoded_to_at"]), "omkodade;", len(s["dropped_short_form"]), "uteslutna;",
          f"gränszon OR {b['or']:.2f} p1 {b['p1']:.4f}; trappan håller helt: {s['ladder_all_hold']}")
