"""Sammanställer provet (analysplaner/2026-11-07-skala-av-provet.md, sha 380fccf4): P1 Wilcoxon B > A, P2 C mot A,
per serie. Läser provet/<stem>.json, skriver provet.json och provet.md.
    .venv/bin/python utdata/skala_av/provet_sammanstall.py"""
import glob
import json
import os
import statistics as st

from scipy.stats import wilcoxon

HERE = os.path.dirname(os.path.abspath(__file__))
SERIES = {"sodermanland": "Södermanland", "vastergotland": "Västergötland", "medelpad": "Medelpad",
          "halsingland": "Hälsingland", "gravmonument_og_sm": "Gravmonument Ög/Sm", "asmund": "Åsmund"}
planned = [l.split() for l in open(os.path.join(HERE, "provet_filer.txt"), encoding="utf-8") if l.strip()]
rows = {}
for p in glob.glob(os.path.join(HERE, "provet", "*.json")):
    d = json.load(open(p, encoding="utf-8"))
    rows[d["stem"]] = d
missing = [s for _, s in planned if s not in rows]
skipped = [(s, rows[s]["skipped"]) for _, s in planned if s in rows and rows[s].get("skipped")]
ok = [rows[s] for _, s in planned if s in rows and not rows[s].get("skipped")]


def test(k, base="A"):
    a = [r[base]["lift"] for r in ok]
    b = [r[k]["lift"] for r in ok]
    diff = [y - x for x, y in zip(a, b)]
    w = wilcoxon(b, a, alternative="greater")
    return {"n": len(diff), "base": base, "median_A": st.median(a), f"median_{k}": st.median(b), "median_diff": st.median(diff),
            "share_better": sum(d > 0 for d in diff) / len(diff), "statistic": float(w.statistic), "p": float(w.pvalue)}


p1, p2 = test("B"), test("C")
# Tillägg utöver planen (beskrivande): C mot A vid samma visade andel som C
extra = test("C", "A_at_C") if all("A_at_C" in r for r in ok) else None
p1["holds"] = p1["p"] < 0.05 and p1["median_diff"] > 0
per = {}
for key, name in SERIES.items():
    rs = [r for r in ok if r["series"] == key]
    if not rs:
        continue
    med = lambda k, m="lift": st.median(r[k][m] for r in rs)  # noqa: E731
    per[name] = {"n": len(rs), "band_share": st.median(r["band_share"] for r in rs),
                 "lift_A": med("A"), "lift_B": med("B"), "lift_C": med("C"),
                 "B_better": sum(r["B"]["lift"] > r["A"]["lift"] for r in rs) / len(rs),
                 "C_better": sum(r["C"]["lift"] > r["A"]["lift"] for r in rs) / len(rs),
                 "lift_A_at_C": med("A_at_C") if extra else None,
                 "C_better_same_share": (sum(r["C"]["lift"] > r["A_at_C"]["lift"] for r in rs) / len(rs)) if extra else None,
                 "shown": med("B", "shown_share"), "shown_C": med("C", "shown_share"),
                 "coverage_A": med("A", "coverage"), "coverage_B": med("B", "coverage"), "coverage_C": med("C", "coverage")}
out = {"plan": "analysplaner/2026-11-07-skala-av-provet.md", "plan_sha": "380fccf4", "files_planned": len(planned),
       "files_measured": len(ok), "missing": missing, "skipped": skipped, "P1": p1, "P2": p2, "extra_C_vs_A_same_share": extra,
       "per_series": per,
       "per_file": [{"series": r["series"], "signum": r.get("signum"), "stem": r["stem"], "band_share": r["band_share"],
                     **{f"lift_{k}": r[k]["lift"] for k in "ABC"},
                     "lift_A_at_C": r.get("A_at_C", {}).get("lift"), "shown_B": r["B"]["shown_share"],
                     "shown_C": r["C"]["shown_share"]} for r in ok]}
json.dump(out, open(os.path.join(HERE, "provet.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

f = lambda v, d=2: f"{v:.{d}f}".replace(".", ",")  # noqa: E731
pc = lambda v: f"{100 * v:.0f} %"  # noqa: E731
L = ["# Provet: skiljer *Skala av vittringen* huggning från vittring bättre än dagens djupbild?", "",
     f"Låst plan `analysplaner/2026-11-07-skala-av-provet.md` (sha 380fccf4). Facit: Viktors granskade runslingor. "
     f"{len(ok)} av {len(planned)} filer mätta" + (f"; saknas: {', '.join(missing)}" if missing else "")
     + (f"; hoppade över: {', '.join(f'{s} ({w})' for s, w in skipped)}" if skipped else "") + ".", "",
     "Teknisk rättelse under körningen: 29 filer saknade djupbildens origo (a0, b0) i djupbildscachens metadata, så att "
     "`rune_bands.drawn_labels` inte kunde föra över slingorna och filen hoppades över. Origo fylldes i med samma funktion "
     "som studie 1b (`utdata/forskningsplan/s1b_klassning.grid_origin`, som kontrollerar att rutnätet blir djupbildens; "
     "`provet_a0.py`) och filerna kördes om. Den sista filen i listan föll först bort för att raden saknade radslut "
     "(rättat i `provet_kor.sh`). Inget i jämförelsen ändrades.", "",
     "**Lyft** = andelen av det visade som ligger inne i slingorna, delat med slingornas andel av ytan (1 = som slumpen). "
     "A = dagens djupbild med en gemensam gräns som visar lika stor del av ytan som B; B = avskalat (reglaget 0 mm), "
     "alla fläckar; C = avskalat, bara spår.", "",
     "## P1 (huvudprov): B mot A", "",
     f"- Median lyft A {f(p1['median_A'])}, B {f(p1['median_B'])}; medianskillnad B − A {f(p1['median_diff'], 3)}; "
     f"B bättre på {pc(p1['share_better'])} av filerna.",
     f"- Wilcoxon ensidigt (B > A): p = {p1['p']:.3g}. **{'Håller' if p1['holds'] else 'Håller inte'}.**", "",
     "## P2 (beskrivande): C mot A", "",
     f"- Median lyft A {f(p2['median_A'])}, C {f(p2['median_C'])}; medianskillnad C − A {f(p2['median_diff'], 3)}; "
     f"C bättre på {pc(p2['share_better'])} av filerna; Wilcoxon ensidigt p = {p2['p']:.3g}. C visar mindre yta än A.", ""]
if extra:
    L += ["## Tillägg utöver planen (beskrivande): C mot A vid samma visade yta", "",
          "Lagt till under körningen, efter de två första filerna och innan något sammanställts, eftersom C visar mindre "
          "yta än A i P2: A räknas om med en gemensam gräns som visar lika stor del av ytan som C. Inget prov är bestämt i "
          "förväg för detta; p-värdet är bara beskrivande.", "",
          f"- Median lyft A (samma yta som C) {f(extra['median_A'])}, C {f(extra['median_C'])}; medianskillnad "
          f"{f(extra['median_diff'], 3)}; C bättre på {pc(extra['share_better'])} av filerna; Wilcoxon ensidigt "
          f"p = {extra['p']:.3g}.", ""]
L += [
     "## Per serie", "",
     "| Serie | Filer | Slingornas andel | Visat B (C) | Lyft A | Lyft B | Lyft C | B > A | C > A | Lyft A vid C:s yta | C > A vid samma yta | Täckning A / B / C |",
     "|---|---|---|---|---|---|---|---|---|---|---|---|"]
for name, d in per.items():
    L.append(f"| {name} | {d['n']} | {pc(d['band_share'])} | {pc(d['shown'])} ({pc(d['shown_C'])}) | {f(d['lift_A'])} | "
             f"{f(d['lift_B'])} | {f(d['lift_C'])} | {pc(d['B_better'])} | {pc(d['C_better'])} | "
             f"{f(d['lift_A_at_C']) if extra else '–'} | {pc(d['C_better_same_share']) if extra else '–'} | "
             f"{pc(d['coverage_A'])} / {pc(d['coverage_B'])} / {pc(d['coverage_C'])} |")
L += ["", "Täckning = andelen av slingornas yta som visas. Medianer per serie.", "", "## Per fil", "",
      "| Serie | Signum | Fil | Slingornas andel | Lyft A | B | C | A vid C:s yta |", "|---|---|---|---|---|---|---|---|"]
for r in out["per_file"]:
    L.append(f"| {SERIES[r['series']]} | {r['signum'] or ''} | {r['stem']} | {pc(r['band_share'])} | {f(r['lift_A'])} | "
             f"{f(r['lift_B'])} | {f(r['lift_C'])} | {f(r['lift_A_at_C']) if r['lift_A_at_C'] else '–'} |")
open(os.path.join(HERE, "provet.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
print("\n".join(L[:20]))
