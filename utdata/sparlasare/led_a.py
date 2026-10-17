"""Spårläsaren, led A (2026-10-17): kan detektorns streck skilja runorna åt? På en skannad sten med känt svar byggs
för varje upptäckt runa en mängd möjliga runor ur streckens geometri (stav + bistavar: korsande eller ej, var på staven,
vinkel). Mängden är oberoende av läsriktning och av vilket håll som är upp, eftersom runorna längs ett band kan luta åt
olika håll. De upptäckta runorna ordnas i rader (här: Sö 113, fyra raka rader), paras mot translittereringens runor med
dynamisk programmering (fyra rad-/riktningskombinationer, den bästa väljs), och vi mäter:
  täckning   hur ofta den sanna runan finns i mängden för sin upptäckta runa
  snävhet    mängdens medelstorlek (16 = säger ingenting)
  slumpen    samma parning mot omkastade texter (20 gånger) – ligger täckningen inte klart över den är allt värdelöst
Skriver <signum>_grooves.json (cache av den automatiska analysen) och led_a.json.
    cd aagaard-research && PYTHONPATH=. .venv/bin/python utdata/sparlasare/led_a.py ["Sö 113"]"""
import json
import math
import os
import random
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
from src import runlm as rl  # noqa: E402

FUT = "fuþorkhniastbmlR"
BASE = {"e": "i", "y": "u", "æ": "a", "ø": "o", "g": "k", "d": "t", "p": "b", "c": "k", "v": "u", "w": "u", "q": "k",
        "x": "k", "z": "s", "å": "o", "ä": "a", "ö": "o", "ą": "o"}


def grooves(signum: str) -> dict:
    """The automatic groove analysis, cached (it takes minutes)."""
    path = os.path.join(HERE, signum.replace(" ", "_") + "_grooves.json")
    if os.path.exists(path):
        return json.load(open(path))
    import trimesh
    from src.auto_grooves import analyze_grooves
    ref = json.load(open(os.path.join(ROOT, "utdata", "Rak", "referenser_g4", signum.replace(" ", "_") + ".json")))
    scan = next(p for p in (os.path.join(ROOT, "skanningar", ref["file"]), os.path.join(ROOT, ref["file"]))
                if os.path.exists(p))
    r = analyze_grooves(trimesh.load(scan, process=False), ref["parameters"]["normal"], up=ref["parameters"].get("up"),
                        resolution_mm=0.6)
    out = {"signum": signum, "counts": r["counts"], "runes": r["runes"], "stroke_lines": r["stroke_lines"]}
    json.dump(out, open(path, "w"))
    return out


# --- the shape of each rune as branches on a stave, direction- and mirror-free: (crossing?, zone 'end'/'mid') and how
# many at most. A detected branch must fit an unused expected one; a rune with every branch missed is still possible
# (detection misses branches far more often than it invents them), so a bare stave allows every rune.
SHAPES = {
    "i": [],
    "u": [(False, "end"), (False, "end")],
    "k": [(False, "end")],
    "l": [(False, "end")],
    "t": [(False, "end"), (False, "end")],
    "m": [(False, "end"), (False, "end")],
    "R": [(False, "end"), (False, "end")],
    "f": [(False, "end"), (False, "end"), (False, "mid")],
    "r": [(False, "end"), (False, "mid"), (False, "mid")],
    "b": [(False, "end"), (False, "mid"), (False, "mid"), (False, "end")],
    "þ": [(False, "mid"), (False, "mid")],
    "s": [(False, "end")],  # short-twig s is a short stave, often with a foot; generous
    "n": [(True, "mid")],
    "a": [(True, "mid")],
    "h": [(True, "mid")],
    "o": [(True, "mid"), (True, "mid")],
}


def recovered(rune: dict, lines: list[dict]) -> list[dict]:
    """Short strokes the classifier threw away as irregular, when one end sits on the rune's stave: lost branches.
    The groove measurements never see these; they are only read for the rune's shape. Straightness and evenness are
    still required, so cracks stay out."""
    det = rune["strokes_detail"]
    stave = max(det, key=lambda s: s["length_mm"])
    A, B = np.array(stave["p0_mm"]), np.array(stave["p1_mm"])
    u = (B - A) / max(np.linalg.norm(B - A), 1e-9)
    L = np.linalg.norm(B - A)
    have = {(tuple(np.round(s["p0_mm"], 1)), tuple(np.round(s["p1_mm"], 1))) for s in det}
    out = []
    for s in lines:
        if s["kind"] not in ("irregular",) or not (3.0 <= s["length_mm"] <= 0.8 * L):
            continue
        if s["deviation_mm"] > max(1.5, 0.1 * s["length_mm"]) or s["width_cv"] > 0.8:
            continue
        key = (tuple(np.round(s["p0_mm"], 1)), tuple(np.round(s["p1_mm"], 1)))
        if key in have:
            continue
        ds = []
        for e in (np.array(s["p0_mm"]), np.array(s["p1_mm"])):
            t = float(np.clip((e - A) @ u, 0, L))
            ds.append(float(np.linalg.norm(e - (A + u * t))))
        if min(ds) <= 3.0:
            out.append(s)
    return out


def features(rune: dict, lines=None) -> list[tuple[bool, str]]:
    """The detected branches of one rune as (crossing?, zone), measured against its longest stroke (the stave).
    lines: every stroke of the stone, for recovering branches the classifier dropped as too short."""
    det = rune["strokes_detail"] + (recovered(rune, lines) if lines else [])
    stave = max(det, key=lambda s: s["length_mm"])
    A, B = np.array(stave["p0_mm"]), np.array(stave["p1_mm"])
    u = (B - A) / max(np.linalg.norm(B - A), 1e-9)
    nrm = np.array([-u[1], u[0]])
    L = np.linalg.norm(B - A)
    out = []
    for s in det:
        if s is stave:
            continue
        e0, e1 = np.array(s["p0_mm"]), np.array(s["p1_mm"])
        d0, d1 = float((e0 - A) @ nrm), float((e1 - A) @ nrm)
        cross = (d0 < -2.0 and d1 > 2.0) or (d0 > 2.0 and d1 < -2.0)
        near = e0 if abs(d0) <= abs(d1) else e1
        t = float((near - A) @ u) / max(L, 1e-9)
        t = min(t, 1 - t)  # which end is up is unknown: distance to the nearest end
        zone = "end" if t < 0.35 else "mid"
        out.append((bool(cross), zone))
    return out


def consistent(branches: list[tuple[bool, str]], rune: str) -> bool:
    """Every detected branch must fit an unused expected branch; 'end' may fall on 'mid' (attachments are inexact)
    but a crossing stroke never fits a non-crossing one."""
    want = list(SHAPES[rune])
    for cross, zone in sorted(branches, key=lambda b: (not b[0], b[1])):
        hit = next((i for i, (wc, wz) in enumerate(want) if wc == cross and (wz == zone or zone == "mid")), None)
        if hit is None:
            hit = next((i for i, (wc, wz) in enumerate(want) if wc == cross), None)
        if hit is None:
            return False
        want.pop(hit)
    return True


def candidate_set(rune: dict, lines=None) -> set[str]:
    return {r for r in FUT if consistent(features(rune, lines), r)}


def text_runes(signum: str) -> str:
    """The inscription's runes in carved order (the main reading), dotted runes to their base."""
    by = {r["signum"]: r for r in rl.load_rundata()}
    t = " ".join(p for _, p in rl.sections(by[signum]["transliteration"]))
    t = rl.runekey(rl.clean_translit(t))
    return "".join(BASE.get(c, c) for c in t if BASE.get(c, c) in FUT)


def rows_of(runes: list[dict], gap_factor: float = 0.8) -> list[list[dict]]:
    """The detected runes grouped into rows by their vertical position (row 0 is at the top of the heightfield)."""
    ys = sorted((float(np.mean([p for s in r["strokes_detail"] for p in (s["p0_mm"][0], s["p1_mm"][0])])), r)
                for r in runes)
    med_h = float(np.median([r["height_mm"] for r in runes]))
    rows, cur, last = [], [], None
    for y, r in ys:
        if last is not None and y - last > gap_factor * med_h:
            rows.append(cur)
            cur = []
        cur.append(r)
        last = y
    rows.append(cur)
    for row in rows:
        row.sort(key=lambda r: float(np.mean([p for s in r["strokes_detail"] for p in (s["p0_mm"][1], s["p1_mm"][1])])))
    return rows


def align(sets: list[set[str]], text: str) -> tuple[float, list[tuple[int, str]]]:
    """DP alignment of the detected runes against the text: a pair costs 0 when the true rune is in the set, 1 when
    not; an unmatched detected rune costs 0.7, an unmatched text rune 0.4. Returns (cost, pairs)."""
    n, m = len(sets), len(text)
    INF = 1e9
    D = np.full((n + 1, m + 1), INF)
    D[0, :] = np.arange(m + 1) * 0.4
    D[:, 0] = np.arange(n + 1) * 0.7
    back = {}
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            sub = D[i - 1, j - 1] + (0.0 if text[j - 1] in sets[i - 1] else 1.0)
            dele = D[i - 1, j] + 0.7
            ins = D[i, j - 1] + 0.4
            D[i, j] = min(sub, dele, ins)
            back[(i, j)] = "s" if D[i, j] == sub else ("d" if D[i, j] == dele else "i")
    pairs, i, j = [], n, m
    while i > 0 and j > 0:
        mv = back[(i, j)]
        if mv == "s":
            pairs.append((i - 1, text[j - 1]))
            i, j = i - 1, j - 1
        elif mv == "d":
            i -= 1
        else:
            j -= 1
    return float(D[n, m]), pairs[::-1]


def evaluate(order: list[dict], text: str, lines=None):
    sets = [candidate_set(r, lines) for r in order]
    cost, pairs = align(sets, text)
    cov = [text_r in sets[i] for i, text_r in pairs]
    return {"cost": cost, "pairs": len(pairs), "coverage": float(np.mean(cov)) if cov else 0.0,
            "set_size": float(np.mean([len(sets[i]) for i, _ in pairs])) if pairs else 16.0,
            "informative": [(i, t, sorted(sets[i])) for i, t in pairs if len(sets[i]) < 16]}


def main(signum="Sö 113"):
    g = grooves(signum)
    runes = [r for r in g["runes"] if r.get("strokes_detail")]
    lines = g.get("stroke_lines")
    rows = rows_of(runes)
    text = text_runes(signum)
    print(f"{signum}: {len(runes)} upptäckta runor i {len(rows)} rader {[len(r) for r in rows]}; texten har {len(text)} runor")
    nb = [len(features(r, lines)) for r in runes]
    print(f"bistavar per runa: medel {np.mean(nb):.2f}; utan bistav {sum(x == 0 for x in nb)} av {len(nb)}")
    best, best_lab = None, None
    for top_down in (True, False):
        for left_right in (True, False):
            order = [r for row in (rows if top_down else rows[::-1]) for r in (row if left_right else row[::-1])]
            e = evaluate(order, text, lines)
            lab = f"rader {'uppifrån' if top_down else 'nerifrån'}, {'vänster→höger' if left_right else 'höger→vänster'}"
            print(f"  {lab:34} kostnad {e['cost']:.1f}  par {e['pairs']}  täckning {e['coverage']:.2f}  mängd {e['set_size']:.1f}")
            if best is None or e["cost"] < best["cost"]:
                best, best_lab, best_order = e, lab, order
    rng = random.Random(7)
    null = []
    for _ in range(20):
        sh = list(text)
        rng.shuffle(sh)
        null.append(evaluate(best_order, "".join(sh), lines)["coverage"])
    print(f"\nbäst: {best_lab}. Täckning {best['coverage']:.2f} (mängd {best['set_size']:.1f}); "
          f"omkastad text {np.mean(null):.2f} ± {np.std(null):.2f}")
    print("runor där mängden säger något (<16):")
    for i, t, ss in best["informative"]:
        print(f"   runa {i:3} facit {t}  {'JA ' if t in ss else 'NEJ'} mängd ({len(ss)}): {''.join(ss)}")
    json.dump({"signum": signum, "rows": [len(r) for r in rows], "text_len": len(text), "best": best_lab,
               "coverage": best["coverage"], "set_size": best["set_size"], "null": null,
               "n_branches_mean": float(np.mean(nb))},
              open(os.path.join(HERE, "led_a.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(*(sys.argv[1:] or ()))
