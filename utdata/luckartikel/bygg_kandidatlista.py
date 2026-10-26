"""Kandidatlistan: öppna luckor där modellen säger minst 80 %, med Visäte-korsningen.

Bygger flaggskeppsunderlaget ur en färsk runlm_luckor.json (scripts/runlm_gaps.py under aktuell
modell): alla luckor Rundata lämnat oåterställda där modellens ifyllnad når p ≥ 0,8, sorterade
efter sannolikhet. För stenar där den ifyllda läsningen innehåller visæti körs dessutom
attributionsmodellen (samma kontext som Syntes & Attribuering): stöder stil, språk, geografi och
R-modellens posteriorer att det är Visätes sten? Utdata: kandidatlista.json + kandidatlista.md.
    .venv/bin/python -m utdata.luckartikel.bygg_kandidatlista
"""
_PROJ = str(__import__("pathlib").Path(__file__).resolve().parents[2])  # projektmappen, var den än ligger
import json
import re
import sys

ROOT = _PROJ
sys.path.insert(0, ROOT)

d = json.load(open(f"{ROOT}/utdata/Malt/runlm_luckor.json"))
oppna = [r for r in d["rows"] if r["status"] == "ej återställt" and (r.get("p") or 0) >= 0.8
         and r.get("word") and r["word"] != "<unk>"]  # en säker ifyllnad i okänt ord är inget fynd
oppna.sort(key=lambda r: -r["p"])
print(f"öppna luckor ≥80 %: {len(oppna)} (av {sum(1 for r in d['rows'] if r['status'] == 'ej återställt')} öppna)")

VISETI = re.compile(r"[vu]is[æe]t", re.I)
viseti_sigs = sorted({r["sig"] for r in oppna
                      if VISETI.search(f"{r.get('word')} {r.get('fill')} {r.get('reading')}")})
print("stenar med visæti i ifylld läsning:", viseti_sigs)

korsning = {}
if viseti_sigs:
    from api.routers.research import _fp, _overview_context, store
    from src import stone_overview
    ctx, _ = _overview_context(_fp())
    for sig in viseti_sigs:
        rec = store().get(sig)
        if not rec:
            continue
        prof = stone_overview.stone(rec, ctx, detail=True)
        probs = (prof.get("model") or {}).get("probabilities") or {}
        korsning[sig] = {
            "rundata_ristare": [c.get("name") for c in rec.get("carvers") or []],
            "status": prof.get("status"), "support": prof.get("support"),
            "alternativ": prof.get("alternative"),
            "modell_posteriorer": probs,
            "visate_posterior": probs.get("Visäte"),
        }
        print(f"  {sig}: status={prof.get('status')} topp={dict(list(probs.items())[:3])} "
              f"Visäte={probs.get('Visäte')}")

ut = {"version": d.get("settings", {}), "antal": len(oppna),
      "kandidater": [{k: r.get(k) for k in ("sig", "carved", "gap", "fill", "word", "p",
                                            "reading", "p_reading", "alts", "context")}
                     for r in oppna],
      "viseti_korsning": korsning}
json.dump(ut, open(f"{ROOT}/utdata/luckartikel/kandidatlista.json", "w"), ensure_ascii=False, indent=1)

rader = ["# Kandidatlistan: öppna luckor där modellen säger ≥ 80 %", "",
         "En lucka Rundata lämnat oåterställd, modellens ifyllnad och dess kalibrerade sannolikhet.",
         "Underlag för flaggskeppsartikeln; varje rad ska granskas mot stenens foto/skanning innan publicering.",
         "", "| Sten | Hugget | Ifyllnad | Ord | p | Näst bästa |", "| --- | --- | --- | --- | --- | --- |"]
for r in oppna:
    alt = (r.get("alts") or [["–", 0]])[0]
    rader.append(f"| {r['sig']} | `{r['carved']}` | {r.get('fill')} | {r.get('word')} "
                 f"| {r['p']:.2f} | {alt[0]} ({alt[1]:.2f}) |")
if korsning:
    rader += ["", "## Visäte-korsningen", ""]
    for sig, k in korsning.items():
        rader.append(f"- **{sig}**: Rundata-ristare {k['rundata_ristare'] or 'ingen'}; "
                     f"attributionsstatus {k['status']}; Visäte-posterior {k['visate_posterior']}; "
                     f"topp {dict(list((k['modell_posteriorer'] or {}).items())[:3])}")
open(f"{ROOT}/utdata/luckartikel/kandidatlista.md", "w").write("\n".join(rader) + "\n")
print("skrivet: kandidatlista.json + kandidatlista.md")
