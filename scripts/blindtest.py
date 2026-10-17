"""Det förregistrerade blindtestet (utdata/blindtest/PROTOKOLL.md). Dragningens frö är registreringscommitens SHA,
så urvalet kan inte ha valts efter utfall. --draw visar urvalet och det i förväg låsta prediktionsintervallet;
--run fyller de dragna stenarnas dokumenterade luckor EN gång med appens kedja och skriver resultatet orört.
    PYTHONPATH=. .venv/bin/python scripts/blindtest.py --draw <SHA>
    PYTHONPATH=. .venv/bin/python scripts/blindtest.py --run <SHA>"""
import argparse
import json
import os
import random
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import src.runlm as rl  # noqa: E402
import src.textmodel as tm  # noqa: E402
from scripts.luckprov import read_stone  # noqa: E402
from scripts.runlm_documented_test import items_for  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BT = os.path.join(ROOT, "utdata", "blindtest")
FROZEN = ("utdata/blindtest/PROTOKOLL.md", "utdata/blindtest/population.json", "src/runlm.py", "src/textmodel.py",
          "scripts/luckprov.py", "scripts/runlm_documented_test.py", "scripts/runlm_gaps.py", "scripts/blindtest.py")
MIN_STONES, MIN_GAPS = 10, 20
BENCH = 0.687


def verify(sha: str) -> None:
    """The protocol and the pipeline must be unchanged since the registering commit."""
    out = subprocess.run(["git", "diff", "--name-only", sha, "HEAD", "--"] + list(FROZEN),
                         cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    assert not out, f"ändrade filer sedan registreringen: {out}"
    dirty = subprocess.run(["git", "status", "--porcelain", "--"] + list(FROZEN),
                           cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    assert not dirty, f"ocommittade ändringar: {dirty}"


def rebuild_population(frozen: dict) -> None:
    """The population must be reproducible from the database with the frozen rules."""
    EX = set(frozen["undantagna"])
    d = tm._records()
    pop = []
    for r in d["V"]:
        if rl.object_kind(r) != "runsten" or r["signum"] in EX:
            continue
        try:
            its = items_for(r)
        except Exception:
            continue
        if its:
            pop.append({"signum": r["signum"], "gaps": len(its), "fold": tm.fold_of(r["signum"])})
    pop.sort(key=lambda x: x["signum"])
    assert pop == frozen["population"], "populationen gick inte att återskapa identiskt"


def draw(sha: str, frozen: dict) -> list[dict]:
    pop = list(frozen["population"])
    pop.sort(key=lambda x: x["signum"])
    random.Random(int(sha, 16) % 2**63).shuffle(pop)
    sel, gaps = [], 0
    for x in pop:
        sel.append(x)
        gaps += x["gaps"]
        if len(sel) >= MIN_STONES and gaps >= MIN_GAPS:
            break
    return sel


def interval(n: int, p: float = BENCH) -> tuple[int, int]:
    """The exact central 95 per cent prediction interval for the number right among n gaps at the benchmark rate."""
    from scipy.stats import binom
    lo = int(binom.ppf(0.025, n, p))
    hi = int(binom.ppf(0.975, n, p))
    return lo, hi


def fill(sel: list[dict]) -> list[dict]:
    d = tm._records()
    G_cal = d["G"]
    by = {r["signum"]: r for r in d["V"]}
    m0 = tm.bundle(0)["model"]  # its lexicon gives the strict lemma comparison; the filling uses each stone's fold
    rows = []
    for x in sel:
        r = by[x["signum"]]
        its = items_for(r)
        by_gap = {(g[gp[0]], tuple(gp)): (g, gp, w, tok, t) for g, gp, w, tok, t in its}
        for y in read_stone(r, [(g, gp, w, tok) for g, gp, w, tok, _ in its], own_d=True):
            g, gp, w, tok, t = by_gap[(y["group"], tuple(y["gap"]))]
            gold = rl.normtok(tok.replace("[", "").replace("]", "").lstrip("…")) if tok and tok != "..." else None
            word = y["word"]
            p = y["p_cal"] if y.get("p_cal") is not None else (tm.calibrate_gap(y["p"], word, gp[2] - gp[1], G_cal) if word else 0.0)
            w_ = (word or "").lstrip("§")
            rows.append({"sig": r["signum"], "carved": w, "lost": gp[2] - gp[1], "truth": t, "fill": y["fill"],
                         "rune_ok": y["fill"] == t, "word": word, "gold_word": gold,
                         "word_ok": bool(gold and w_ and w_ != "<unk>" and rl.same_word(w_, gold)),
                         "word_ok_strikt": bool(gold and w_ and w_ != "<unk>" and m0.lemma(w_) == m0.lemma(gold)),
                         "p": round(p, 4), "p_model": y["p"], "alts": y.get("alts")})
        print(f"{x['signum']}: {x['gaps']} luckor ifyllda", flush=True)
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--draw", metavar="SHA")
    ap.add_argument("--run", metavar="SHA")
    a = ap.parse_args()
    sha = a.run or a.draw
    assert sha, "ange --draw SHA eller --run SHA (registreringscommiten)"
    sha = subprocess.run(["git", "rev-parse", sha], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    verify(sha)
    frozen = json.load(open(os.path.join(BT, "population.json")))
    rebuild_population(frozen)
    sel = draw(sha, frozen)
    n = sum(x["gaps"] for x in sel)
    lo, hi = interval(n)
    print(f"frö: {sha}")
    print(f"urval: {len(sel)} stenar, {n} luckor: " + ", ".join(f"{x['signum']} ({x['gaps']})" for x in sel))
    print(f"låst intervall: {lo}–{hi} rätt av {n} är förenligt med riktmärket {BENCH}")
    if not a.run:
        return
    out_path = os.path.join(BT, "resultat.json")
    assert not os.path.exists(out_path), "resultat.json finns redan: testet körs bara en gång"
    rows = fill(sel)
    right = sum(x["word_ok"] for x in rows)
    strict = sum(x["word_ok_strikt"] for x in rows)
    said = sum(x["p"] for x in rows) / max(1, len(rows))
    hi95 = [x for x in rows if x["p"] >= 0.95]
    res = {"sha": sha, "stones": [x["signum"] for x in sel], "n": len(rows),
           "interval": [lo, hi], "right": right, "share": round(right / max(1, len(rows)), 4),
           "right_strikt": strict, "share_strikt": round(strict / max(1, len(rows)), 4),
           "mean_claimed": round(said, 4),
           "claimed95": {"n": len(hi95), "right": sum(x["word_ok"] for x in hi95)},
           "within_interval": lo <= right <= hi,
           "calibration_ok": abs(said - right / max(1, len(rows))) <= 0.15,
           "rows": rows}
    json.dump(res, open(out_path, "w"), ensure_ascii=False, indent=1)
    print(f"\nresultat: {right} av {len(rows)} rätt ({right / len(rows):.1%}); strikt {strict} ({strict / len(rows):.1%})")
    print(f"intervall {lo}–{hi}: {'INOM' if res['within_interval'] else 'UTANFÖR'}")
    print(f"medelpåstående {said:.3f} mot utfall {right / len(rows):.3f}: kalibrering {'OK' if res['calibration_ok'] else 'AVVIKER'}")
    print(f"minst 95 %: {res['claimed95']['right']} rätt av {res['claimed95']['n']}")
    print("skrivet:", out_path)


if __name__ == "__main__":
    main()
