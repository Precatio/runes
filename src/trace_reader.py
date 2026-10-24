"""Spårläsaren: vad som syns av runorna direkt ur 3D-skanningen, som förslag till panelens spår.

Bistavarna går inte att lita på i de uttunnade spårlinjerna, så de läses ur själva djupbilden: sammanhängande
spårblobbar utanför stavarnas egen bredd och slinglinjerna, fästa vid närmaste stav. Varje blobb viktas efter
huggdjup mot sin stav, avlånghet och längd, och varje runmall betalar ett pris per bistavsplats; kostnaderna blir
en sannolikhetsfördelning över de sexton runorna. Valideringen (utdata/sparlasare, led A–G): på 157 maskerade
helord på 17 skannade stenar lyfte spåren andelen rätt ord från 53,5 till 59,9 procent (parat p = 3,7e-6), och
slumpvis omflyttade spår raderade vinsten. Vid svårt vittrade partier kan blobbarna ändå vilseleda, och en
bindruna ser ut som en runa med för många bistavar. Därför är allt här FÖRSLAG: panelen visar vad skannern ser,
och spåren räknas först när användaren har bekräftat dem (de postas till det vanliga spår-API:t). En runa med
fler djupa bistavar än den rikaste mallen rymmer föreslår ingenting ("möjlig bindruna").

Mätreglerna i groove-5 rörs inte: analyze_grooves läses bara (keep_arrays=True). Den tunga djupbildskörningen
görs en gång per sten (scripts/trace_cache.py) och sparas i data/cache/traces/."""
from __future__ import annotations

import itertools
import json
import math
import os
import re

import numpy as np

import src.runlm as rl

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "data", "cache", "traces")
REFS = os.path.join(ROOT, "utdata", "Rak", "referenser_g4")
# The other open scans (scripts/batch_scans.py): file path under skanningar/ and the normal of the protocol measurement
REFS_AUTO = os.path.join(ROOT, "utdata", "automatisk_korning", "referenser")

TAU = 0.25      # softmax temperature (swept on Sö 113; Sö 134 and Sö 207 untouched replication)
PRIOR = 0.08    # cost per template slot: a rune with many branches must earn them
EPS = 0.10      # probability floor: no rune is ever impossible (weathering, detector faults)
D_MID, D_SLOPE = 0.55, 0.12  # depth-ratio logistic: a real branch is carved about as deep as its stave
MARGIN = 0.75   # the proposed set: runes within this cost of the best
DEEP_W = 0.5    # a blob at least this likely real counts against the bind-rune guard
MAX_SLOTS = 4   # the richest template (b) holds four branches; more deep blobs → possible bind rune

FUT = "fuþorkhniastbmlR"
BASE = {"e": "i", "y": "u", "æ": "a", "ø": "o", "g": "k", "d": "t", "p": "b", "c": "k", "v": "u", "w": "u", "q": "k",
        "x": "k", "z": "s", "å": "o", "ä": "a", "ö": "o", "ą": "o"}
PRE: dict[str, set[str]] = {}
for _ch in list(FUT) + list(BASE):
    PRE.setdefault(BASE.get(_ch, _ch), set()).add(_ch)


def expand(s: set[str]) -> set[str]:
    """A trace set in futhark space widened with the dotted variants the model fills with (u → u, v, w, y …)."""
    return set().union(*(PRE.get(c, {c}) for c in s))


# --- templates: each rune as alternative branch lists of (crossing, zone 'end'/'mid', side group, long). Side groups
# are relative (mirroring and reading direction are unknown); an 'end' observation may sit in a 'mid' slot but never
# the other way; a long branch (u's bow) needs a long slot.
T: dict[str, list[list[tuple]]] = {
    "i": [[]],
    "s": [[], [(False, "end", "A", False)]],
    "u": [[(False, "end", "A", True)], [(False, "end", "A", False), (False, "end", "A", False)]],
    "k": [[(False, "end", "A", False)], [(False, "mid", "A", False)]],
    "l": [[(False, "end", "A", False)]],
    "t": [[(False, "end", "A", False)], [(False, "end", "A", False), (False, "end", "B", False)]],
    "m": [[(False, "end", "A", False), (False, "end", "B", False)]],
    "R": [[(False, "end", "A", False), (False, "end", "B", False)]],
    "f": [[(False, "end", "A", False), (False, "mid", "A", False)],
          [(False, "end", "A", False), (False, "end", "A", False)],
          [(False, "end", "A", False), (False, "mid", "A", False), (False, "mid", "A", False)]],
    "r": [[(False, "end", "A", False), (False, "mid", "A", False)],
          [(False, "end", "A", False), (False, "mid", "A", False), (False, "mid", "A", False)]],
    "b": [[(False, "end", "A", False), (False, "mid", "A", False)],
          [(False, "end", "A", False), (False, "mid", "A", False), (False, "mid", "A", False), (False, "end", "A", False)]],
    "þ": [[(False, "mid", "A", False)], [(False, "mid", "A", False), (False, "mid", "A", False)]],
    "n": [[(True, "mid", "A", False)]],
    "a": [[(True, "mid", "A", False)]],
    "h": [[(True, "mid", "A", False)]],
    "o": [[(True, "mid", "A", False)], [(True, "mid", "A", False), (True, "mid", "A", False)]],
}


def blob_weight(depth_ratio: float, elong: float, length: float) -> float:
    """How likely the blob is a carved branch rather than weathering or a serif."""
    w_d = 1.0 / (1.0 + math.exp(-(depth_ratio - D_MID) / D_SLOPE))
    w_e = 0.5 + 0.5 * min(1.0, max(0.0, (elong - 1.6) / 2.4))
    w_l = 0.5 + 0.5 * min(1.0, max(0.0, (length - 3.0) / 4.0))
    return w_d * w_e * w_l


def _stave(rune: dict) -> tuple[np.ndarray, np.ndarray]:
    st = max(rune["strokes_detail"], key=lambda s: s["length_mm"])
    return np.array(st["p0_mm"]), np.array(st["p1_mm"])


def _seg_dist(P: np.ndarray, A: np.ndarray, B: np.ndarray) -> np.ndarray:
    u = B - A
    L2 = float(u @ u) or 1e-9
    t = np.clip((P - A) @ u / L2, 0.0, 1.0)
    return np.linalg.norm(P - (A + t[:, None] * u), axis=1)


def weighted_blobs(runes: list[dict], lines: list[dict], arrays: dict) -> dict:
    """{rune id: [branch blob]} from the groove mask: elongated blobs outside every stave's width and the band
    lines, assigned to the nearest stave, weighted by depth ratio, elongation and length. Opposite blobs at matching
    height merge into one crossing stroke."""
    from scipy import ndimage
    mask, wide, hw_img, res = arrays["mask"], arrays["wide_area"], arrays["half_width"], arrays["res"]
    depth = arrays["depth"]
    hw = float(np.median(hw_img[mask])) if mask.any() else 3.0
    staves = {r["id"]: _stave(r) for r in runes}
    pts_all = np.argwhere(mask & ~wide) * res
    keep = np.ones(len(pts_all), bool)
    for A, B in staves.values():
        keep &= _seg_dist(pts_all, A, B) > hw + 0.6
    for s in lines:
        if s["kind"] == "ornament" or s.get("length_mm", 0) > 60:
            keep &= _seg_dist(pts_all, np.array(s["p0_mm"]), np.array(s["p1_mm"])) > hw + 0.6
    img = np.zeros(mask.shape, bool)
    px = (pts_all[keep] / res).astype(int)
    img[px[:, 0], px[:, 1]] = True
    lab, n = ndimage.label(img, structure=np.ones((3, 3)))
    out: dict = {r["id"]: [] for r in runes}
    for k in range(1, n + 1):
        pts = np.argwhere(lab == k) * res
        if len(pts) * res * res < 4.0:
            continue
        best_id, best_d = None, None
        for rid, (A, B) in staves.items():
            d = float(_seg_dist(pts, A, B).min())
            if best_d is None or d < best_d:
                best_id, best_d = rid, d
        if best_d > hw + 3.5:
            continue
        A, B = staves[best_id]
        L = float(np.linalg.norm(B - A))
        u = (B - A) / max(L, 1e-9)
        nrm = np.array([-u[1], u[0]])
        C = pts - pts.mean(axis=0)
        w_, v_ = np.linalg.eigh(C.T @ C / len(pts))
        elong = w_[1] / max(w_[0], 1e-9)
        axis = v_[:, 1]
        t_ = C @ axis
        length = float(t_.max() - t_.min())
        if length < 3.0 or elong < 1.6:
            continue
        ang = float(np.degrees(np.arccos(min(1.0, abs(float(axis @ u))))))
        near = pts[np.argmin(_seg_dist(pts, A, B))]
        t_attach = float(np.clip((near - A) @ u / max(L, 1e-9), -0.2, 1.2))
        if ang < 15 and not 0.05 < t_attach < 0.95:
            continue
        bpx = (pts / res).astype(int)
        blob_d = float(np.median(depth[bpx[:, 0], bpx[:, 1]]))
        spx = np.array([(A + t * u) / res for t in np.linspace(0, L, 25)]).astype(int)
        spx = spx[(spx[:, 0] >= 0) & (spx[:, 0] < depth.shape[0]) & (spx[:, 1] >= 0) & (spx[:, 1] < depth.shape[1])]
        stave_d = float(np.median(depth[spx[:, 0], spx[:, 1]])) if len(spx) else 0.0
        ratio = blob_d / stave_d if stave_d > 0 else 1.0
        tz = min(max(t_attach, 0.0), 1.0)
        out[best_id].append({"zone": "end" if min(tz, 1 - tz) < 0.35 else "mid",
                             "side": float(np.sign((pts.mean(axis=0) - A) @ nrm)) or 1.0,
                             "angle": ang, "length": round(length, 1), "t": t_attach, "long": length > 0.55 * L,
                             "elong": round(float(elong), 2), "ratio": round(float(ratio), 3)})
    feats = {}
    for rid, bs in out.items():
        merged, used = [], set()
        for i, b in enumerate(bs):
            if i in used:
                continue
            j = next((j for j, c in enumerate(bs) if j > i and j not in used and c["side"] != b["side"]
                      and abs(c["t"] - b["t"]) < 0.3 and abs(c["angle"] - b["angle"]) < 30), None)
            if j is not None and b["zone"] == "mid":
                used |= {i, j}
                c = bs[j]
                merged.append({"cross": True, "zone": "mid", "side": 0, "long": False,
                               "length": max(b["length"], c["length"]), "ratio": max(b["ratio"], c["ratio"]),
                               "w": round(max(blob_weight(b["ratio"], b["elong"], b["length"]),
                                              blob_weight(c["ratio"], c["elong"], c["length"])), 3)})
            else:
                used.add(i)
                merged.append({"cross": False, "zone": b["zone"], "side": b["side"], "long": b["long"],
                               "length": b["length"], "ratio": b["ratio"],
                               "w": round(blob_weight(b["ratio"], b["elong"], b["length"]), 3)})
        feats[rid] = merged
    return feats


def template_cost(obs: list[dict], template: list[tuple], prior: float = PRIOR) -> float:
    """The cheapest weighted way to lay the observed blobs into the template's slots: discarding a blob as noise
    costs its weight, using it costs the weight times the fit penalties, a missed slot 0.25, each slot `prior`."""
    best = None
    for polarity in (1, -1):
        for perm in itertools.permutations(range(len(template))) if len(template) <= 4 else [tuple(range(len(template)))]:
            cost, used, side_of = 0.0, set(), {}
            for o in sorted(obs, key=lambda b: -b["w"]):
                slot = None
                for ti in perm:
                    if ti in used:
                        continue
                    cross, zone, grp, long_ = template[ti]
                    if o["cross"] != cross:
                        continue
                    c = 0.0
                    if not o["cross"]:
                        if o["zone"] == "mid" and zone == "end":
                            c += 0.3
                        if o["long"] and not long_:
                            c += 0.5
                        want = side_of.get(grp)
                        if want is not None and want != o["side"] * polarity:
                            c += 0.6
                    slot = (c, ti, o)
                    break
                if slot is None or slot[0] >= 1.0:
                    cost += o["w"]
                else:
                    c, ti, o2 = slot
                    cost += o2["w"] * c
                    used.add(ti)
                    if not o2["cross"]:
                        side_of.setdefault(template[ti][2], o2["side"] * polarity)
            cost += 0.25 * (len(template) - len(used))
            if best is None or cost < best:
                best = cost
    return (best if best is not None else 99.0) + prior * len(template)


def rune_probs(obs: list[dict]) -> dict[str, float] | None:
    """P(rune | blobs) over the sixteen runes – or None when the rune may be a bind rune (more deep branches than
    the richest template holds), where a guess would mislead."""
    if sum(1 for b in obs if b["w"] >= DEEP_W) > MAX_SLOTS:
        return None
    costs = {r: min(template_cost(obs, t) for t in alts) for r, alts in T.items()}
    m = min(costs.values())
    ex = {r: math.exp(-(c - m) / TAU) for r, c in costs.items()}
    z = sum(ex.values())
    return {r: (1 - EPS) * v / z + EPS / 16 for r, v in ex.items()}


def margin_set(probs: dict[str, float]) -> set[str]:
    mx = max(probs.values())
    return {c for c, p in probs.items() if math.log(mx / p) * TAU <= MARGIN}


def rune_depth_check(g: dict) -> dict[int, dict]:
    """Djupbildens andra ögon på den automatiska analysens igenkända runor: bistavsblobbarna kring varje stav
    prövas mot de sexton runmallarna (samma maskineri som spårläsarens luckförslag). En runa flaggas när blobbarna
    inte liknar någon runa – antingen för många djupa bistavslägen (bindrune-vakten: kan också vara en
    ornamentikknut) eller en platt fördelning över hela runraden trots flera blobbar (formen pekar ingenstans,
    som korsarmar och slingor gör). INTE I DRIFT: tvåstenspiloten 2026-10-19 (Sö 143 med kända korsarmsfel mot
    välbevarade Sö 128) gav "svag" 23 mot 12 procent – signal åt rätt håll men för mycket brus – och "tät" 11 mot
    24, alltså åt FEL håll (den fångar bistavsrika äkta runor). Flaggan kopplas in i granskningen först när
    handmärkta facit (scripts/evaluate_rune_detection.py) visar vilka trösklar som håller.
    Kräver analyze_grooves(keep_arrays=True)."""
    runes = [r for r in g.get("runes") or [] if r.get("strokes_detail")]
    if not runes or "arrays" not in g:
        return {}
    feats = weighted_blobs(runes, g["stroke_lines"], g["arrays"])
    out: dict[int, dict] = {}
    for r in runes:
        obs = feats.get(r["id"]) or []
        probs = rune_probs(obs)
        if probs is None:
            out[r["id"]] = {"flag": "tät", "top": [],
                            "note": "fler djupa bistavslägen än någon runa har – bindruna eller ornamentik"}
            continue
        top = sorted(probs.items(), key=lambda kv: -kv[1])[:3]
        flat = len(margin_set(probs)) >= len(FUT)
        out[r["id"]] = {"flag": "svag" if flat and len(obs) >= 2 else None,
                        "top": [[c, round(p, 3)] for c, p in top],
                        **({"note": "bistavarna liknar ingen runa – kan vara ornamentik"} if flat and len(obs) >= 2 else {})}
    return out


# --- the stone: cached features and gap proposals --------------------------------------------------------------------

def _safe(signum: str) -> str:
    return re.sub(r"[^A-Za-z0-9ÅÄÖåäö]+", "_", signum)


def scan_ref(signum: str) -> str | None:
    for d in (REFS, REFS_AUTO):
        p = os.path.join(d, signum.replace(" ", "_") + ".json")
        # The signum comes from a URL: only a file inside the folder counts (not "../../x" anywhere on disk)
        refs = os.path.realpath(d)
        if os.path.commonpath([os.path.realpath(p), refs]) != refs:
            return None
        if os.path.exists(p):
            return p
    return None


def features(signum: str) -> dict | None:
    """The cached scan features: {"runes": the detected runes, "feats": {id: [weighted blobs]}} – or None when the
    heavy run has not been made (scripts/trace_cache.py)."""
    path = os.path.join(CACHE, _safe(signum) + ".json")
    if not os.path.exists(path):
        return None
    d = json.load(open(path, encoding="utf-8"))
    d["feats"] = {int(k) if k.lstrip("-").isdigit() else k: v for k, v in d["feats"].items()}
    return d


def compute_features(signum: str) -> dict:
    """The heavy run (minutes): groove analysis with the depth image kept, then the weighted blobs. Writes the cache."""
    import trimesh
    from src.auto_grooves import analyze_grooves
    ref_path = scan_ref(signum)
    if not ref_path:
        raise FileNotFoundError(f"ingen skanningsreferens för {signum}")
    ref = json.load(open(ref_path))
    scan = next(p for p in (os.path.join(ROOT, "skanningar", ref["file"]), os.path.join(ROOT, ref["file"]))
                if os.path.exists(p))
    g = analyze_grooves(trimesh.load(scan, process=False), ref["parameters"]["normal"],
                        up=ref["parameters"].get("up"), resolution_mm=0.6, keep_arrays=True)
    runes = [r for r in g["runes"] if r.get("strokes_detail")]
    feats = weighted_blobs(runes, g["stroke_lines"], g["arrays"])
    out = {"signum": signum, "runes": runes, "feats": feats}
    os.makedirs(CACHE, exist_ok=True)
    tmp = os.path.join(CACHE, _safe(signum) + ".json.tmp")
    json.dump(out, open(tmp, "w", encoding="utf-8"), ensure_ascii=False)
    os.replace(tmp, os.path.join(CACHE, _safe(signum) + ".json"))
    return out


def _rows(runes: list[dict], gap_factor: float = 0.8) -> list[list[dict]]:
    """The detected runes grouped into rows by vertical position, each row left to right."""
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


def _gap_align(sets: list[set[str]], seq: list[tuple[int, str]]) -> tuple[float, list[tuple[int, int]]]:
    """DP pairing of detected runes against the text; a lost rune (?) matches every set for free, so damaged but
    detected runes can land on their own positions."""
    n, m = len(sets), len(seq)
    D = np.full((n + 1, m + 1), 1e9)
    D[0, :] = np.arange(m + 1) * 0.4
    D[:, 0] = np.arange(n + 1) * 0.7
    back = {}
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            c = seq[j - 1][1]
            sub = D[i - 1, j - 1] + (0.0 if (c == "?" or c in sets[i - 1]) else 1.0)
            dele = D[i - 1, j] + 0.7
            ins = D[i, j - 1] + 0.4
            D[i, j] = min(sub, dele, ins)
            back[(i, j)] = "s" if D[i, j] == sub else ("d" if D[i, j] == dele else "i")
    pairs, i, j = [], n, m
    while i > 0 and j > 0:
        mv = back[(i, j)]
        if mv == "s":
            pairs.append((i - 1, seq[j - 1][0]))
            i, j = i - 1, j - 1
        elif mv == "d":
            i -= 1
        else:
            j -= 1
    return float(D[n, m]), pairs[::-1]


def proposals(signum: str) -> dict:
    """What the scan sees at the inscription's gaps, keyed like the panel's gaps (textmodel.analyze numbering):
    {"available": bool, "reason": str?, "gaps": {gap number: [{"pos", "set", "top", "blobs", "bind"}]},
    "quality": {...}}. Everything is a proposal: the pairing of detected runes to text positions is estimated, and
    the traces only count once the user has confirmed them in the panel."""
    import src.textmodel as tm
    if not scan_ref(signum):
        return {"available": False, "reason": "Stenen har ingen inmätt 3D-skanning."}
    data = features(signum)
    if data is None:
        return {"available": False, "reason": "Spårläsningen är inte beräknad för stenen ännu (scripts/trace_cache.py)."}
    d = tm._records()
    r = d["by"].get(signum)
    if r is None or not (rl.viking(r) and r.get("transliteration")):
        return {"available": False, "reason": "Inskriften kan inte läsas av modellen."}
    groups, _ = tm.text_groups(r["transliteration"])
    full = "".join(groups)
    if "?" not in full:
        return {"available": False, "reason": "Inskriften har inga förlorade runor."}
    off, at = [], 0
    for g in groups:
        off.append(at)
        at += len(g)
    runes, feats = data["runes"], data["feats"]
    if len(runes) < 5:
        return {"available": False, "reason": "För få runor upptäckta i skanningen för att föreslå spår."}
    probs = {x["id"]: rune_probs(feats[x["id"]]) for x in runes}
    msets = {rid: (margin_set(p) if p else set(FUT)) for rid, p in probs.items()}
    seq = [(i, BASE.get(c, c)) for i, c in enumerate(full) if BASE.get(c, c) in FUT or c == "?"]
    best = None
    rows = _rows(runes)
    for td in (True, False):
        for lr in (True, False):
            order = [x for row in (rows if td else rows[::-1]) for x in (row if lr else row[::-1])]
            cost, pairs = _gap_align([msets[x["id"]] for x in order], seq)
            if best is None or cost < best[0]:
                best = (cost, pairs, order)
    _, pairs, order = best
    pd = {pos: i for i, pos in pairs}
    ana = tm.analyze(signum)
    out_gaps = {}
    for g in ana.get("gaps") or []:
        entries = []
        for i in range(g["start"], g["end"]):
            ap = off[g["group"]] + i
            if groups[g["group"]][i] != "?" or ap not in pd:
                continue
            rid = order[pd[ap]]["id"]
            p = probs[rid]
            if p is None:
                entries.append({"pos": i - g["start"], "bind": True, "set": "",
                                "top": [], "blobs": feats[rid]})
                continue
            top = sorted(p.items(), key=lambda kv: -kv[1])[:5]
            entries.append({"pos": i - g["start"], "bind": False,
                            "set": "".join(sorted(expand(msets[rid]))),
                            "informative": len(msets[rid]) < len(FUT),
                            "top": [[c, round(q, 3)] for c, q in top],
                            "blobs": feats[rid]})
        if entries:
            out_gaps[str(g["number"])] = entries
    n_lost = full.count("?")
    return {"available": True, "gaps": out_gaps,
            "quality": {"detected": len(runes), "text_runes": len(seq), "paired": len(pairs),
                        "lost_total": n_lost, "lost_with_proposal": sum(len(v) for v in out_gaps.values())}}
