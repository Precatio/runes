"""Överblick över en lucka (stenanalyssidan och panelen Läsning och luckor): alla ord som sannolikhetsmodellen prövar i
en lucka, inte bara de fem bästa, med sannolikheten i sammanhanget, ordets belägg i korpusen och varifrån kandidaten
kom. Användaren kan också välja ett annat antal förlorade runor än Rundatas, när det är osäkert hur många som fattas.

Samma modell och inställning som appens förslag (textmodel.MODEL, textmodel.FILL, stenens del-modell, stenens egen
andel skiljetecken, namnen på närliggande stenar) och samma kalibrering (textmodel.calibrate_words). Luckan fylls på
nytt med rl.restore, med de andra luckorna fyllda med läsningens val, och resultatet sparas per sten, lucka och
antal runor i data/cache/textmodel/<version>-overview/. Inget av detta ändrar läsningen eller förslagen i appen.

Kalibreringen ger en sannolikhet åt de kmax (6) troligaste orden, som i appen; de övriga orden och möjligheten att
inget av de prövade orden är rätt delar på resten ("unassigned"). För dem redovisas modellens egen andel, okalibrerad."""
import json
import os
import re
import tempfile
import threading
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone

from src import runlm as rl
from src import textmodel as tm

CACHE = tm.CACHE + "-overview"
LIMIT = 200          # at most this many candidates (fillings) and words are returned
MIN_N, MAX_N = 1, 6  # the number of lost runes a user may choose; the model is tested on 1–4 (tm.MAX_GAP)
UNSURE = 0.45        # a first choice under this calibrated probability is marked as uncertain
EXAMPLES = 6
CLASS = {0: "formel", 1: "annat", 2: "namn", 3: "sammansatt namn"}

_index: dict = {}
_index_lock = threading.Lock()


def _safe(signum: str) -> str:
    return tm._safe(signum)


def corpus_index(k: int, m) -> dict:
    """For the fold model k: {lemma: {"runsten": Counter(signum → occurrences), "annat": Counter(...)}} over every
    Viking-age inscription with a normalization in Rundata (descriptive counts; the stone itself is left out when
    they are shown). Runestones and other objects are counted apart (the app's rule)."""
    with _index_lock:
        if k in _index:
            return _index[k]
    idx: dict = defaultdict(lambda: {"runsten": Counter(), "annat": Counter()})
    for r in tm._records()["V"]:
        kind = "runsten" if rl.object_kind(r) == "runsten" else "annat"
        for _, p in rl.sections(r["normalization"]):
            for w in rl.norm_words(p):
                idx[m.lemma(rl.normtok(w))][kind][r["signum"]] += 1
    idx = dict(idx)
    with _index_lock:
        _index[k] = idx
        while len(_index) > tm.K:
            _index.pop(next(iter(_index)))
    return idx


def _prefix(signum: str) -> str:
    return signum.split(" ")[0]


def _corpus(idx: dict, lemma, signum: str) -> dict:
    """How often the word is written in the corpus, on how many stones, and a few examples (signa) – the stone itself
    left out; runestones first, other objects apart. Examples from the stone's own landscape come first."""
    e = idx.get(lemma) or {"runsten": Counter(), "annat": Counter()}
    rs = {s: c for s, c in e["runsten"].items() if s != signum}
    ot = {s: c for s, c in e["annat"].items() if s != signum}
    pre = _prefix(signum)
    ex = sorted(rs, key=lambda s: (_prefix(s) != pre, -rs[s], s))[:EXAMPLES]
    return {"count": sum(rs.values()), "stones": len(rs), "examples": ex,
            "other_count": sum(ot.values()), "other_stones": len(ot)}


def _target(reading: dict, groups: list, kind: str, number: int):
    """The gap's span (group, start, end) and its lost runes. kind 'gap': the reading's gaps (1–4 lost runes, which the
    app fills); 'open': the longer gaps the app leaves open."""
    every = [(gi, x.start(), x.end()) for gi, g in enumerate(groups) for x in re.finditer(r"\?+", g)]
    _, runs, _, _ = rl.merge_runs(groups, every)
    lost = {sp: [i for i in range(sp[1], sp[2]) if groups[sp[0]][i] == "?"] for sp in runs}
    fillable = [sp for sp in runs if len(lost[sp]) <= tm.MAX_GAP]
    opens = [sp for sp in runs if sp not in fillable]
    pool, listed = (fillable, reading.get("gaps") or []) if kind == "gap" else (opens, reading.get("open_gaps") or [])
    if not (0 <= number < len(pool)):
        raise ValueError(f"Inskriften har ingen sådan lucka (nummer {number}).")
    sp = pool[number]
    # the reading numbers its gaps in the same order; check that they are the same spans
    if number < len(listed) and (listed[number]["group"], listed[number]["start"], listed[number]["end"]) != sp:
        raise ValueError("Luckan stämmer inte med den sparade läsningen.")
    return sp, lost, fillable


def overview(signum: str, gap: int, n: int | None = None, kind: str = "gap", limit: int = LIMIT) -> dict:
    """Every candidate the model tries in one gap of an inscription, with its probability in the context.
    gap: the gap's number (the reading's 'gaps', or with kind='open' its 'open_gaps'); n: the number of lost runes to
    assume (default: Rundata's). Raises KeyError for an unknown signum and ValueError for a gap or length that cannot
    be tried."""
    if kind not in ("gap", "open"):
        raise ValueError("Okänd sorts lucka.")
    d = tm._records()
    r = d["by"].get(signum)
    if r is None:
        raise KeyError(signum)
    base = {"signum": signum, "version": tm.VERSION, "validation": tm.VALIDATION}
    if not (rl.viking(r) and r.get("transliteration")):
        return {**base, "available": False,
                "reason": "Modellen är byggd för vikingatida inskrifter med en translitterering i Rundata."}
    reading = tm.analyze(signum)  # the app's reading (cached): the other gaps are filled with its choices
    if not reading.get("available"):
        return {**base, "available": False, "reason": reading.get("reason")}
    groups, breaks = tm.text_groups(r["transliteration"])
    sp, lost, fillable = _target(reading, groups, kind, gap)
    gi, a, e = sp
    n_rd = len(lost[sp])
    all_lost = (e - a) == n_rd  # no preserved rune inside the gap
    if n is None:
        n = n_rd
    if not all_lost and n != n_rd:
        raise ValueError("Luckan har bevarade runor inne i sig, så antalet förlorade runor kan inte ändras.")
    if not (MIN_N <= n <= MAX_N):
        raise ValueError(f"Antalet förlorade runor måste vara mellan {MIN_N} och {MAX_N}"
                         + (f" (Rundata anger {n_rd})." if n_rd > MAX_N else "."))
    limit = max(1, min(int(limit), LIMIT))
    path = os.path.join(CACHE, f"{_safe(signum)}__{kind}{gap}_n{n}.json")
    if os.path.exists(path):
        try:
            return _cut({**json.load(open(path, encoding="utf-8")), "validation": tm.VALIDATION, "cached": True}, limit)
        except ValueError:
            pass
    t0 = time.time()
    k = tm.fold_of(signum)
    m = tm.bundle(k)["model"]
    # the text as the app fills it: every fillable gap lost, then the other gaps filled with the reading's choices
    work = list(groups)
    for g_, a_, e_ in fillable:
        work[g_] = work[g_][:a_] + "?" * (e_ - a_) + work[g_][e_:]
    best = {(x["group"], x["start"], x["end"]): x.get("best") for x in reading.get("gaps") or []}
    context = []
    filled = list(work)
    for num, (g_, a_, e_) in enumerate(fillable):
        f_ = best.get((g_, a_, e_))
        if (g_, a_, e_) != sp and f_ and len(f_) == e_ - a_:
            filled[g_] = filled[g_][:a_] + f_ + filled[g_][e_:]
            context.append({"number": num, "fill": f_})
    cons = [None if groups[gi][i] == "?" else groups[gi][i] for i in range(a, e)]
    width = n if all_lost else e - a
    filled[gi] = filled[gi][:a] + "?" * width + filled[gi][e:]
    allowed = cons if any(c is not None for c in cons) else None
    hard = [i for i, c in enumerate(cons) if c is not None] if allowed else None
    site = (float(r["lat"]), float(r["lon"])) if r.get("lat") is not None and r.get("lon") is not None else None
    near = [(la, lo, nm, ck) for sg, la, lo, nm, ck in d["sites"] if sg != signum]
    wd, seg, orig, wr = {}, {}, {}, {}
    with tm._compute:  # the model's caches are shared with the readings
        dr = rl.stone_divider_rate(m, work, breaks) if tm.OWN_D else None
        res = rl.restore(m, filled, (gi, a, a + width), signs=breaks, words=wd, segments=seg, allowed=allowed, hard=hard,
                         site=site, near_sites=near, div_rate=dr, origins=orig, word_runes=wr, **tm.FILL)
    out = _summarize(signum, m, res, wd, orig, wr, d, n_lost=n if all_lost else n_rd, k=k)
    out.update(base)
    out.update({
        "available": True, "computed_at": datetime.now(timezone.utc).isoformat(), "seconds": round(time.time() - t0, 1),
        "gap": {"number": gap, "kind": kind, "group": gi, "start": a, "end": e, "carved": groups[gi],
                "rundata_n": n_rd, "n": n, "adjustable": all_lost, "tested": n <= tm.MAX_GAP,
                "min_n": MIN_N, "max_n": MAX_N},
        "context": context})
    os.makedirs(CACHE, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=CACHE, suffix=".tmp", delete=False) as fh:
        json.dump(out, fh, ensure_ascii=False)
    os.replace(fh.name, path)
    return _cut({**out, "cached": False}, limit)


def _cut(out: dict, limit: int) -> dict:
    if not out.get("available"):
        return out
    return {**out, "limit": limit, "candidates": out["candidates"][:limit], "words": out["words"][:limit],
            "truncated": len(out["candidates"]) > limit or len(out["words"]) > limit}


def _summarize(signum, m, res, wd, orig, wr, d, n_lost, k) -> dict:
    """The candidates (fillings) and the words they give, with probabilities calibrated as in the app."""
    GL = d.get("GL")
    top, names = (GL[3], GL[4]) if GL else ((d["G"][1], d["G"][2]) if d.get("G") else (set(), set()))
    word_of = {f: (wd.get(f) or "<unk>") for f, _ in res}
    lk = {f: (m.lemma(w) if w != "<unk>" else ("<unk>", w)) for f, w in word_of.items()}
    wdist = rl._by_lemma(m, [(word_of[f], p) for f, p in res])  # as restore_all: the forms of a word together
    rep = {}
    for f, _ in res:
        rep.setdefault(lk[f], word_of[f])
    best_f = res[0][0] if res else None
    whole = bool(best_f) and wr.get(best_f, ("", "")) == ("", "")
    cal = tm.calibrate_words(wdist, n_lost, GL, whole) if GL else None
    kmax = GL[2] if GL else 0
    ranked_known = [w for w in wdist if w != "<unk>"][:kmax]
    pcal = {w: cal.get(w, 0.0) for w in ranked_known} if cal else {}
    idx = corpus_index(k, m)

    def info(w):
        c = tm.gap_class(w, top, names, composed=True) if w != "<unk>" else None
        return c, (c in (2, 3))
    cands = []
    for f, p in res:
        w = word_of[f]
        c, is_name = info(w)
        left, right = wr.get(f, ("", ""))
        cands.append({"fill": f, "p_model": round(p, 5), "word": w.lstrip("§") if w != "<unk>" else None,
                      "unknown": w == "<unk>", "composed": w.startswith("§"), "name": is_name,
                      "p_word": (round(pcal[rep[lk[f]]], 4) if rep[lk[f]] in pcal else None),
                      "origins": orig.get(f, []), "left": left, "right": right})
    by_word = defaultdict(list)
    for x in cands:
        by_word[rep[lk[x["fill"]]]].append(x)
    words = []
    for w, pm in wdist.items():
        xs = by_word[w]
        c, is_name = info(w)
        words.append({
            "word": w.lstrip("§") if w != "<unk>" else None, "unknown": w == "<unk>", "composed": w.startswith("§"),
            "name": is_name, "class": CLASS.get(c) if c is not None else None,
            "p": round(pcal[w], 4) if w in pcal else None, "p_model": round(pm, 5),
            "fills": [{"fill": x["fill"], "p_model": x["p_model"], "left": x["left"], "right": x["right"]} for x in xs[:12]],
            "n_fills": len(xs),
            "origins": sorted({o for x in xs for o in x["origins"]}),
            "corpus": _corpus(idx, m.lemma(w), signum) if w != "<unk>" else None})
    # the calibrated words first (as in the app, by calibrated probability), then the rest by the model's share
    words.sort(key=lambda x: (x["p"] is None, -(x["p"] or 0.0), -x["p_model"]))
    assigned = sum(pcal.values())
    first = words[0] if words and words[0]["p"] is not None else None
    return {
        "calibrated": bool(cal), "kmax": kmax, "candidates": cands, "words": words,
        "n_tried": len(res), "n_words": sum(1 for w in wdist if w != "<unk>"),
        "n_unknown_fills": sum(1 for f in word_of.values() if f == "<unk>"),
        "unassigned": round(max(0.0, 1.0 - assigned), 4) if cal else None,
        "top_unsure": bool(first is None or first["p"] < UNSURE),
        "whole_word": whole}


def locate(signum: str, gap: int, n: int | None = None, kind: str = "gap") -> dict:
    """Where a gap is, without filling it: for storing a filling of it (src/vitki_fills.py). The same numbering and
    the same rules for the number of lost runes as overview()."""
    if kind not in ("gap", "open"):
        raise ValueError("Okänd sorts lucka.")
    d = tm._records()
    r = d["by"].get(signum)
    if r is None:
        raise KeyError(signum)
    reading = tm.analyze(signum)
    if not reading.get("available"):
        raise ValueError(reading.get("reason") or "Modellen kan inte läsa inskriften.")
    groups, _ = tm.text_groups(r["transliteration"])
    sp, lost, _ = _target(reading, groups, kind, gap)
    gi, a, e = sp
    n_rd = len(lost[sp])
    all_lost = (e - a) == n_rd
    n = n_rd if n is None else n
    if (not all_lost and n != n_rd) or not (MIN_N <= n <= MAX_N):
        raise ValueError("Antalet förlorade runor kan inte prövas för den här luckan.")
    cons = [None if groups[gi][i] == "?" else groups[gi][i] for i in range(a, e)]
    return {"kind": kind, "number": gap, "group": gi, "start": a, "end": e, "carved": groups[gi], "rundata_n": n_rd,
            "n": n, "width": n if all_lost else e - a, "preserved_inside": cons, "key": f"{gi}:{a}:{e}"}


def candidate(signum: str, gap: int, fill: str, n: int | None = None, kind: str = "gap") -> dict | None:
    """The overview's row for one filling (its word and probabilities), or None when the model did not try it."""
    out = overview(signum, gap, n=n, kind=kind, limit=LIMIT)
    path = os.path.join(CACHE, f"{_safe(signum)}__{kind}{gap}_n{out['gap']['n']}.json")
    full = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else out
    return next((c for c in full.get("candidates", []) if c["fill"] == fill), None)
