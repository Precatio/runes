"""Alverna – fördjupning 2 i serien Nordiska väsen, enligt analysplaner/2026-11-21-alverna.md (låst 5d305b6).

Samma korpusar som den första väsenstudien (utdata/vasen/analys.texts). Träffarna med sammanhang och handklassningen
ligger i data/cache/alverna/ (git-ignorerad: textutdrag); här skrivs bara summor.

    .venv/bin/python utdata/alverna/analys.py --samla      # alla träffar → data/cache/alverna/traffar.csv (att klassa)
    .venv/bin/python utdata/alverna/analys.py --kontroll   # 40 slumpade för blind omklassning
    .venv/bin/python utdata/alverna/analys.py              # A1–A6, T1 → utdata/alverna/matt.json
"""
import csv
import glob
import hashlib
import html
import json
import os
import random
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "utdata", "vasen"))
import analys as vasen  # noqa: E402

PLAN = os.path.join(ROOT, "analysplaner", "2026-11-21-alverna.md")
assert hashlib.sha256(open(PLAN, "rb").read()).hexdigest().startswith("529f2940"), "planen är ändrad efter låsningen"
CACHE = os.path.join(ROOT, "data", "cache", "alverna")
SEED = 20261121
B = 10000

LOW = re.compile(r"\b(?:ljós|dökk|døkk|svart|myrk)?[aá]lf(?!t)\w*")
CAP = re.compile(r"\b(?:Ljós|Dökk|Svart)?[AÁ]lf(?!t)\w*|\bÆlf\w*")
COMP = re.compile(r"\b(?:Ljós|Dökk|Døkk|Svart|Myrk)[aá]lf\w*")  # tillägg 1 (1b50c3d): Ljósálfar, Dökkálfar
GODS = re.compile(r"\b(?:æsir|ásir|æsi|ása|ásum|ásu|goð|goðin|goða|goðum|goðanna|vanir|vana|vönum|tívar|tíva|regin|rögn)\b")
MONST = re.compile(r"\b(?:tröll\w*|troll\w*|jötun\w*|jötn\w*|þurs\w*|risa\w*|risi|risar|óvætt\w*|meinvætt\w*|flagð\w*|flögð\w*|illþýði\w*)\b")
DWARF = re.compile(r"\bdverg\w*")
CLASSES = {"väsen", "kenning", "personnamn", "ortnamn", "Völundr", "världsdel", "annat"}


def texts():
    return [(c, n, t) for c, n, t in vasen.texts()]


def hits(t):
    out = []
    for rx in (LOW, CAP, COMP):
        for m in rx.finditer(t):
            out.append((m.start(), m.end(), m.group(0)))
    return sorted(set(out))


def samla():
    os.makedirs(CACHE, exist_ok=True)
    rows = []
    for c, n, t in texts():
        for i, (s, e, w) in enumerate(hits(t)):
            rows.append({"id": f"{c}|{n}|{s}", "korpus": c, "text": n, "pos": s, "ord": w,
                         "kwic": t[max(0, s - 90): e + 90].replace("\n", " ")})
    with open(os.path.join(CACHE, "traffar.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(len(rows), "träffar;", Counter(r["korpus"] for r in rows))


def kontroll():
    rows = list(csv.DictReader(open(os.path.join(CACHE, "traffar.csv"), encoding="utf-8")))
    s = random.Random(SEED).sample(rows, 40)
    with open(os.path.join(CACHE, "kontroll_blind.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "ord", "kwic"])
        w.writeheader()
        for r in s:
            w.writerow({"id": r["id"], "ord": r["ord"], "kwic": r["kwic"]})


# ---- bootstrap över texter ----
def boot_diff(units_a, units_b, stat, rnd):
    out = []
    for _ in range(B):
        a = [units_a[rnd.randrange(len(units_a))] for _ in units_a]
        b = [units_b[rnd.randrange(len(units_b))] for _ in units_b]
        sa, sb = stat(a), stat(b)
        if sa is not None and sb is not None:
            out.append(sa - sb)
    return out


def ci(xs):
    s = sorted(xs)
    return [round(s[int(0.025 * len(s))], 1), round(s[int(0.975 * len(s)) - 1], 1)]


def p_two(xs, null=0.0):
    lo = sum(1 for x in xs if x <= null) / len(xs)
    hi = sum(1 for x in xs if x >= null) / len(xs)
    return min(1.0, 2 * min(lo, hi))


def main():
    rows = list(csv.DictReader(open(os.path.join(CACHE, "traffar.csv"), encoding="utf-8")))
    cls = {r["id"]: r for r in csv.DictReader(open(os.path.join(CACHE, "klassning.csv"), encoding="utf-8"))}
    assert set(cls) == {r["id"] for r in rows}, "varje träff ska vara klassad"
    assert all(c["klass"] in CLASSES for c in cls.values())
    T = {(c, n): t for c, n, t in texts()}
    words = {k: len(t.split()) for k, t in T.items()}
    for r in rows:
        r["klass"] = cls[r["id"]]["klass"]
    res = {"träffar": len(rows)}

    # A1, A2
    corpora = list(dict.fromkeys(c for c, _ in T))
    res["A1"] = {c: {k: sum(1 for r in rows if r["korpus"] == c and r["klass"] == k) for k in sorted(CLASSES)} for c in corpora}
    res["A1_texter_med_väsen"] = {c: len({r["text"] for r in rows if r["korpus"] == c and r["klass"] in ("väsen", "Völundr")}) for c in corpora}
    res["A1_former"] = Counter(r["ord"] for r in rows if r["klass"] in ("väsen", "Völundr")).most_common(40)
    res["A2_per_10000"] = {c: round(1e4 * sum(1 for r in rows if r["korpus"] == c and r["klass"] in ("väsen", "Völundr"))
                                    / sum(n for (cc, _), n in words.items() if cc == c), 2) for c in corpora}
    # A3 kulten, A4 ljus/dökk
    res["A3_kult"] = [(r["korpus"], r["text"], r["ord"]) for r in rows if r["klass"] == "väsen" and re.search(r"blót|veisl|fórn", r["kwic"])]
    res["A4_ljus_dokk"] = [(r["korpus"], r["text"], r["ord"]) for r in rows if re.match(r"(?:ljós|dökk|døkk|svart|myrk|Ljós|Dökk|Svart)", r["ord"])]
    res["Völundr"] = [(r["korpus"], r["text"], r["ord"]) for r in rows if r["klass"] == "Völundr"]
    res["annat"] = [(r["korpus"], r["text"], r["ord"]) for r in rows if r["klass"] == "annat"]

    # A5 namnen
    sag = [r for r in rows if r["klass"] == "personnamn" and not r["korpus"].startswith("runstenar")]
    res["A5_sagor_namn"] = Counter(r["ord"] for r in sag).most_common(25)
    res["A5_sagor_namn_antal"] = len(sag)
    from api.rundata import store
    from src.research_gaps import PROVINCE_NAMES, is_runestone
    stones = [r for r in store().inscriptions if is_runestone(r)]

    def names(r):
        return re.findall(r'"([^\s,.;:()\[\]"]+)', (r.get("normalization_ows") or "").replace("[", "").replace("]", ""))

    def with_elem(rx):
        hit = [r for r in stones if any(rx.match(n) for n in names(r))]
        forms = Counter(n for r in hit for n in names(r) if rx.match(n))
        return hit, forms
    alf, alf_forms = with_elem(re.compile(r"(?:Alf|Álf|Ælf)"))
    tor, _ = with_elem(re.compile(r"(?:Þór|Þor|Þur)"))
    asn, _ = with_elem(re.compile(r"(?:Ás|As)(?!t)"))
    n_st = len(stones)
    res["A5_runstenar"] = {"stenar": n_st, "alf_stenar": len(alf), "alf_andel": round(100 * len(alf) / n_st, 1),
                           "alf_former": alf_forms.most_common(), "alf_landskap": Counter(PROVINCE_NAMES.get(r["signum"].split()[0], "?") for r in alf).most_common(),
                           "alf_signa": [r["signum"] for r in alf],
                           "tor_stenar": len(tor), "tor_andel": round(100 * len(tor) / n_st, 1),
                           "as_stenar": len(asn), "as_andel": round(100 * len(asn) / n_st, 1)}

    # A6 ortnamnen i SOL (förklaringen, inte namnet)
    res["A6"] = {"kandidater": len(sol_alv()), "läsning": json.load(open(os.path.join(HERE, "a6_lasning.json"), encoding="utf-8"))}

    # T1
    def window(r, k):
        t = T[(r["korpus"], r["text"])]
        pos = int(r["pos"])
        before = t[:pos].split()[-k:]
        after = t[pos:].split()[1:k + 1]
        return " ".join(before + after)
    el = [r for r in rows if r["klass"] in ("väsen", "Völundr")]

    def group(r):
        if r["korpus"] == "eddadikter" or r["korpus"].startswith("snorra_edda"):
            return "Eddan"
        if r["korpus"].startswith("runstenar"):
            return None
        return "sagorna"

    def t1(k=25, skip=()):
        out = {}
        units = {"Eddan": defaultdict(list), "sagorna": defaultdict(list)}
        for r in el:
            g = group(r)
            if g is None or r["text"] in skip:
                continue
            w = window(r, k)
            units[g][r["text"] + "|" + r["korpus"]].append((bool(GODS.search(w)), bool(MONST.search(w)), bool(DWARF.search(w))))
        E, S = list(units["Eddan"].values()), list(units["sagorna"].values())
        nE, nS = sum(map(len, E)), sum(map(len, S))
        out["underlag"] = {"Eddan_träffar": nE, "Eddan_texter": len(E), "sagorna_träffar": nS, "sagorna_texter": len(S)}
        if nE < 10 or nS < 10 or len(S) < 5:
            out["obestämt"] = True
            return out

        def share(i):
            return lambda us: (100 * sum(x[i] for u in us for x in u) / sum(map(len, us))) if sum(map(len, us)) else None
        rnd = random.Random(SEED)
        for name, i in (("T1a_gudar", 0), ("T1b_vidunder", 1), ("dvärgar", 2)):
            d = boot_diff(E, S, share(i), rnd)
            out[name] = {"Eddan_%": round(share(i)(E), 1), "sagorna_%": round(share(i)(S), 1),
                         "skillnad_pe": round(share(i)(E) - share(i)(S), 1), "intervall": ci(d), "p": p_two(d)}
        ps = sorted((out[t]["p"], t) for t in ("T1a_gudar", "T1b_vidunder"))
        prev = 0.0
        for j, (p, t) in enumerate(ps):
            adj = max(prev, min(1.0, (2 - j) * p))
            prev = adj
            lo, hi = out[t]["intervall"]
            out[t]["p_holm"] = round(adj, 4)
            out[t]["håller"] = adj < 0.05 and not (lo <= 0 <= hi)
        return out

    res["T1"] = {"huvud": t1(), "utan_Alvíssmál": t1(skip=("Alvíssmál",)), "fönster_10": t1(k=10)}
    json.dump(res, open(os.path.join(HERE, "matt.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: res[k] for k in ("A2_per_10000", "T1", "A5_runstenar")}, ensure_ascii=False, indent=1)[:4000])


def sol_alv():
    """SOL-artiklar vars förklaring nämner alver (planen A6). Returnerar kandidaterna; läsningen sker för hand."""
    rx = re.compile(r"\balv(?:er|erna|ernas|a)?\b|’alv’|\balf(?:er)?\b", re.I)
    out = []
    for f in sorted(glob.glob("/Volumes/2TB/Antigrvity/Runes/downloads/asatro/isof_sol/_namn_ortnamn_sol_ortnamnslexikon_*.html")):
        raw = open(f, encoding="utf-8").read()
        txt = html.unescape(re.sub(r"<[^>]+>", "\n", raw))
        for para in re.split(r"\n\s*\n", txt):
            p = " ".join(para.split())
            if rx.search(p) and len(p) > 40:
                out.append(p[:60])
    return out


if __name__ == "__main__":
    samla() if "--samla" in sys.argv else kontroll() if "--kontroll" in sys.argv else main()
