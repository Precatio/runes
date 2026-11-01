"""Maltstenens runrad och dubblering (låst plan analysplaner/2026-11-01-malt-runrad-dubblering.md, sha 0d9e7e19).
Beskrivande: (A) vikingatida inskrifter med yngre runrad och vad som står bredvid; (B) direkta upprepningar XX i
runkorpusen och dubbleringar i Eddan och sagorna. Rättad huvudläsning: allt efter ett fristående §Q tas bort, och
Rundatas sidor skiljs med ett brott. Inga läsningar av Malt. Skriver runrad_dubblering.json.
    PYTHONPATH=. .venv/bin/python utdata/Malt/runrad_dubblering.py"""
import glob
import json
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
from src import runlm as rl  # noqa: E402
import scripts.runlm_sprakprov as S  # noqa: E402

FUT = S.FUTHARK
NXT = {a: b for a, b in zip(FUT, FUT[1:])}


def sides(translit):
    """The main reading's sides: text after a standalone §Q is dropped, a/b → a, each section kept apart."""
    t = translit or ""
    m = re.search(r"§Q(?![A-Z])", t)
    if m:
        t = t[:m.start()]
    return [re.sub(r"(\S+)/\S+", r"\1", p) for _, p in rl.sections(t)]


def stretches(translit):
    """Per side, unbroken stretches as lists of carved groups (dividers bound groups, editors' spaces do not)."""
    out = []
    for p in sides(translit):
        t = rl.clean_translit(p)
        t = re.sub(rl.DIV, "|", t)
        t = re.sub(r"\s+", "", t)
        for st in re.split(r"[^a-zþæøR|]+", t):
            g = [x for x in st.split("|") if x]
            if g:
                out.append(g)
    return out


def tandems(st, k=3):
    """Every direct repeat XX (|X| ≥ k, X not one rune repeated) inside a carved group: (X, group)."""
    out = []
    for s in st:
        for g in s:
            for L in range(len(g) // 2, k - 1, -1):
                hit = next((g[i:i + L] for i in range(len(g) - 2 * L + 1)
                            if g[i:i + L] == g[i + L:i + 2 * L] and len(set(g[i:i + L])) > 1), None)
                if hit:
                    out.append((hit, g))
                    break
    return out


def futhark_spans(st):
    """(stretch index, start group, end group, length) for runs of ≥ 6 runes in futhark order, across dividers."""
    out = []
    for si, s in enumerate(st):
        t = "".join(s)
        owner = [gi for gi, g in enumerate(s) for _ in g]
        i = 0
        while i < len(t):
            j = i
            while j + 1 < len(t) and NXT.get(t[j]) == t[j + 1]:
                j += 1
            if j - i + 1 >= 6:
                out.append((si, owner[i], owner[j], j - i + 1))
            i = j + 1
    return out


def main():
    rows = rl.load_rundata()
    res = {"plan": "analysplaner/2026-11-01-malt-runrad-dubblering.md", "plan_sha": "0d9e7e19"}

    # ---- A: futhark rows -------------------------------------------------------------------------------------------------
    A, med = [], Counter()
    for r in rows:
        st = stretches(r.get("transliteration"))
        sp = futhark_spans(st)
        if not sp:
            continue
        kind = rl.object_kind(r)
        if not rl.viking(r):
            other = sum(len(g) for s in st for g in s) - sum(x[3] for x in sp)
            med[(r.get("period") or "?")[:1], kind, "annan text" if other >= 6 else "bara raden"] += 1
            continue
        si, g0, g1, n = sp[0]
        s = st[si]
        rest = sum(len(g) for s_ in st for g in s_) - sum(x[3] for x in sp)
        A.append({"signum": r["signum"], "kind": kind, "object": r.get("object"), "row_len": n,
                  "before": s[max(0, g0 - 2):g0], "after": s[g1 + 1:g1 + 3], "runes_besides_row": rest,
                  "tandem_any": [x for x, _ in tandems(st)],
                  "translit": (r.get("transliteration") or "")[:300], "normalization": (r.get("normalization") or "")[:300],
                  "translation_en": (r.get("translation_en") or "")[:300]})
    res["A"] = A
    res["A_counts"] = dict(Counter(a["kind"] for a in A))
    res["A_medieval"] = {" | ".join(k): v for k, v in sorted(med.items())}

    # ---- B1: direct repeats in the runic corpus -------------------------------------------------------------------------
    B1, cnt = [], Counter()
    for r in rows:
        st = stretches(r.get("transliteration"))
        if sum(len(g) for s in st for g in s) < 10:
            continue
        per = "V" if rl.viking(r) else "M" if (r.get("period") or "").startswith("M") else "övr"
        kind = rl.object_kind(r)
        cnt[(per, kind, "n")] += 1
        tz = tandems(st)
        if tz:
            cnt[(per, kind, "XX")] += 1
            if per == "V" and r["signum"] != "DR NOR1988;5":
                B1.append({"signum": r["signum"], "kind": kind, "X": [x for x, _ in tz], "group": [g for _, g in tz],
                           "normalization": (r.get("normalization") or "")[:260], "translation_en": (r.get("translation_en") or "")[:200]})
    res["B1_counts"] = {" | ".join(k): v for k, v in sorted(cnt.items())}
    res["B1_viking"] = B1

    # ---- B2: Edda and sagas ---------------------------------------------------------------------------------------------
    WORD = r"[A-Za-zÀ-ÿĀ-žǫę]+"


    def edda_works():
        for work, text in json.load(open(rl.EDDA)).items():          # same boilerplate cut as runlm.edda_tokens
            i = text.find("prentunar")
            text = text[i + 9:] if i >= 0 else " ".join(text.split()[60:])
            yield work, [w.lower() for w in re.findall(WORD, text)]


    def saga_works():
        for f in sorted(glob.glob(os.path.join(ROOT, "utdata", "varlden", "korpus", "*", "*.txt"))):
            yield os.path.basename(f), [w.lower() for w in re.findall(WORD, open(f, encoding="utf-8").read())]


    def redup(w):
        for L in range(len(w) // 2, 1, -1):
            for i in range(len(w) - 2 * L + 1):
                if w[i:i + L] == w[i + L:i + 2 * L] and len(set(w[i:i + L])) > 1:
                    return w[i:i + L]
        return None


    B2 = {}
    for name, works in (("edda", edda_works()), ("sagor", saga_works())):
        n, ww, rd = 0, [], []
        for work, toks in works:
            n += len(toks)
            for i in range(1, len(toks)):
                if toks[i] == toks[i - 1] and len(toks[i]) > 1:
                    ww.append({"work": work, "word": toks[i], "context": " ".join(toks[max(0, i - 5):i + 4])})
            for i, w in enumerate(toks):
                x = redup(w)
                if x:
                    rd.append({"work": work, "word": w, "X": x, "context": " ".join(toks[max(0, i - 4):i + 4])})
        B2[name] = {"words": n, "ww": len(ww), "ww_per_10k": 1e4 * len(ww) / n, "ww_top": Counter(x["word"] for x in ww).most_common(25),
                    "redup": len(rd), "redup_top": Counter(x["word"] for x in rd).most_common(40),
                    "ww_list": ww if name == "edda" else ww[:40], "redup_list": rd if name == "edda" else rd[:60]}
    assert B2["edda"]["words"] == 90852
    res["B2"] = B2
    json.dump(res, open(os.path.join(HERE, "runrad_dubblering.json"), "w"), ensure_ascii=False, indent=1)

    print("A:", res["A_counts"], "| medeltid:", res["A_medieval"])
    for a in A:
        print(f"\n{a['signum']} [{a['kind']}, {a['object']}] rad {a['row_len']}, övrigt {a['runes_besides_row']} runor; före {a['before']} efter {a['after']}; XX {a['tandem_any']}")
        print("   T:", a["translit"][:200]); print("   N:", a["normalization"][:200]); print("   E:", a["translation_en"][:160])
    print("\nB1:", res["B1_counts"])
    for b in B1:
        print(f"{b['signum']:18} {b['kind']:12} {b['X']} {b['group']} | {b['normalization'][:110]}")
    for k in ("edda", "sagor"):
        v = B2[k]
        print(f"\n{k}: {v['words']} ord; w w {v['ww']} ({v['ww_per_10k']:.2f}/10k) {v['ww_top'][:15]}; redup {v['redup']} {v['redup_top'][:30]}")
    for x in B2["edda"]["ww_list"]:
        print("  EDDA ww:", x["work"][:30], "|", x["context"])
    for x in B2["edda"]["redup_list"]:
        print("  EDDA redup:", x["work"][:30], "|", x["word"], "|", x["context"])


if __name__ == "__main__":
    main()
