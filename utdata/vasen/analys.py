"""Väsen som inte är gudar i den fornnordiska litteraturen – enligt analysplaner/2026-11-21-vasen.md (låst 2076615) med
den frysta ordlistan utdata/vasen/ordlista.csv (sha256 e064e87d…).

Korpusarna (utanför git): utdata/varlden/korpus/ (sagorna) och utdata/Malt/kallor/edda.json (Eddan, Snorres Edda).
Träffarna med sammanhang skrivs till data/cache/vasen/ (git-ignorerad, innehåller korta textutdrag); här bara summor.

    .venv/bin/python utdata/vasen/analys.py --grind    # stickprovet till kvalitetsgrinden
    .venv/bin/python utdata/vasen/analys.py            # V1–V5, T1–T3 → utdata/vasen/matt.json
"""
import csv
import hashlib
import json
import os
import random
import re
import sys
import unicodedata
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "utdata", "varlden"))
from rakna_platser import split_verse  # noqa: E402
from src.research_gaps import is_runestone  # noqa: E402

# Ordlista v2 enligt tillägg 1 (c56f36f): vättar och nattväsen reviderade efter grinden
LEX = os.path.join(HERE, "ordlista_v2.csv")
assert hashlib.sha256(open(LEX, "rb").read()).hexdigest().startswith("7a636ce4"), "ordlistan är ändrad efter låsningen"
TERMS = [dict(r, rx=re.compile(r["regex"]), fore=re.compile(r["utom_fore"]) if r["utom_fore"] else None)
         for r in csv.DictReader(open(LEX, encoding="utf-8"))]
CLASSES = list(dict.fromkeys(t["klass"] for t in TERMS))
CACHE = os.path.join(ROOT, "data", "cache", "vasen")
KORPUS = os.path.join(ROOT, "utdata", "varlden", "korpus")
EDDA_JSON = os.path.join(ROOT, "utdata", "Malt", "kallor", "edda.json")
EDDA_CSV = os.path.join(ROOT, "utdata", "Edda", "edda_karta_texter.csv")
SEED = 20261121
B = 10000


def nfc(s):
    return unicodedata.normalize("NFC", s)


def strip_header(t, title):
    m = re.search(r"bjó til prentunar\s+", t)
    return t[m.end():] if m else t


def texts():
    """(korpus, namn, text) för varje text."""
    edda = json.load(open(EDDA_JSON, encoding="utf-8"))
    poems = []
    for row in csv.DictReader(open(EDDA_CSV, encoding="utf-8")):
        n = row["namn"].split("_")[0] if row["namn"].startswith("Hávamál") else row["namn"]
        # the 34 poems: Snorri's Edda has its own corpus (tillägg 1: the CSV also holds Gylfaginning and Skáldskaparmál)
        if n not in poems and n not in ("Hugsvinnsmál", "Sólarljóð", "Gylfaginning", "Skáldskaparmál"):
            poems.append(n)
    for n in poems:
        key = n if n in edda else n.replace(" ", "_")
        yield "eddadikter", n, nfc(strip_header(edda[key], n))
    for n in ("Gylfaginning", "Skáldskaparmál"):
        yield f"snorra_edda_{n.lower()}", n, nfc(strip_header(edda[n], n))
    sagas = [("islanningasagor", "islendingasogur", ".is.txt", True), ("heimskringla", "heimskringla", ".txt", False),
             ("fornaldarsagor", "fornaldarsogur", ".txt", False), ("samtidssagor", "samtidssagor", ".txt", False)]
    for corpus, folder, suffix, tabbed in sagas:
        d = os.path.join(KORPUS, folder)
        for f in sorted(os.listdir(d)):
            if not f.endswith(suffix):
                continue
            name = f[: -len(suffix)].replace("_", " ")
            prose, stanzas = split_verse(open(os.path.join(d, f), encoding="utf-8").read(), tabbed)
            yield corpus, name, nfc(prose)
            if stanzas:
                yield f"{corpus}_vers", name, nfc("\n".join(stanzas))
    from api.rundata import store
    for r in store().inscriptions:
        if is_runestone(r) and (r.get("normalization_ows") or "").strip():
            yield "runstenar_SE", r["signum"], nfc(r["normalization_ows"].replace('"', ""))


def hits(text):
    out = []
    for t in TERMS:
        for m in t["rx"].finditer(text):
            if t["fore"] and t["fore"].search(text[max(0, m.start() - 20): m.start()]):
                continue  # verbet vætta (tillägg 1)
            out.append((t["klass"], t["term"], m.group(0), m.start()))
    # one hit per position: a stretch matched by two terms counts once (first term in the list)
    seen, uniq = set(), []
    for h in sorted(out, key=lambda x: (x[3], [t["term"] for t in TERMS].index(x[1]))):
        if h[3] not in seen:
            seen.add(h[3])
            uniq.append(h)
    return uniq


def collect():
    rows, words = [], {}
    for corpus, name, t in texts():
        words[(corpus, name)] = len(t.split())
        for k, term, w, pos in hits(t):
            kwic = t[max(0, pos - 60): pos + 60].replace("\n", " ")
            rows.append({"korpus": corpus, "text": name, "klass": k, "term": term, "ord": w, "kwic": kwic})
    return rows, words


def grind2():
    """Tillägg 1: nytt stickprov för de reviderade klasserna (seed 20261122)."""
    rows, _ = collect()
    rnd = random.Random(20261122)
    with open(os.path.join(CACHE, "grind2.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["nr", "klass", "term", "korpus", "text", "ord", "kwic"])
        w.writeheader()
        i = 0
        for k in ("vättar", "nattväsen"):
            by = [r for r in rows if r["klass"] == k]
            print(k, len(by))
            for r in (rnd.sample(by, 15) if len(by) > 15 else by):
                i += 1
                w.writerow({"nr": i, **{c: r[c] for c in ("klass", "term", "korpus", "text", "ord", "kwic")}})


def grind():
    rows, _ = collect()
    os.makedirs(CACHE, exist_ok=True)
    rnd = random.Random(SEED)
    by = defaultdict(list)
    for r in rows:
        by[r["klass"]].append(r)
    with open(os.path.join(CACHE, "grind.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["nr", "klass", "term", "korpus", "text", "ord", "kwic"])
        w.writeheader()
        i = 0
        for k in CLASSES:
            for r in (rnd.sample(by[k], 15) if len(by[k]) > 15 else by[k]):
                i += 1
                w.writerow({"nr": i, **{c: r[c] for c in ("klass", "term", "korpus", "text", "ord", "kwic")}})
    print({k: len(by[k]) for k in CLASSES}, "träffar totalt", len(rows))


# --- bootstrap över texter ---
def pooled(sample, rate_of):
    return rate_of(sample)


def boot(units, stat, rnd):
    return [stat([units[rnd.randrange(len(units))] for _ in units]) for _ in range(B)]


def ci(xs):
    s = sorted(x for x in xs if x is not None)
    return [round(s[int(0.025 * len(s))], 3), round(s[int(0.975 * len(s)) - 1], 3)]


def p_two(xs, null):
    xs = [x for x in xs if x is not None]
    lo = sum(1 for x in xs if x <= null) / len(xs)
    hi = sum(1 for x in xs if x >= null) / len(xs)
    return min(1.0, 2 * min(lo, hi))


def main():
    rows, words = collect()
    os.makedirs(CACHE, exist_ok=True)
    with open(os.path.join(CACHE, "traffar.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    gp = os.path.join(HERE, "grind_resultat.json")
    grind_res = json.load(open(gp, encoding="utf-8")) if os.path.exists(gp) else {}
    dropped = set(grind_res.get("klasser_utan_test", []))
    corpora = list(dict.fromkeys(c for c, _ in words))
    per_text = defaultdict(Counter)  # (corpus, text) → Counter(klass)
    per_term = defaultdict(Counter)
    for r in rows:
        per_text[(r["korpus"], r["text"])][r["klass"]] += 1
        per_term[r["korpus"]][r["term"]] += 1
    res = {"ord_per_korpus": {c: sum(n for (k, _), n in words.items() if k == c) for c in corpora},
           "texter_per_korpus": {c: sum(1 for (k, _) in words if k == c) for c in corpora}, "grind": grind_res}

    # V1, V2
    rnd = random.Random(SEED)
    res["V1"], res["V2"] = {}, {}
    for c in corpora:
        keys = [k for k in words if k[0] == c]
        res["V1"][c] = {"träffar": {k: sum(per_text[t][k] for t in keys) for k in CLASSES},
                        "texter_med_träff": {k: sum(1 for t in keys if per_text[t][k]) for k in CLASSES},
                        "vanligaste_termer": per_term[c].most_common(12)}
        n_words = sum(words[k] for k in keys)
        tot = sum(sum(per_text[t].values()) for t in keys)
        rate = lambda s: 1e4 * sum(sum(per_text[t].values()) for t in s) / max(1, sum(words[t] for t in s))  # noqa: E731
        res["V2"][c] = {"per_10000_ord": round(1e4 * tot / max(1, n_words), 2),
                        "intervall": ci(boot(keys, rate, rnd)) if len(keys) > 1 and c != "runstenar_SE" else None,
                        "per_klass": {k: round(1e4 * sum(per_text[t][k] for t in keys) / max(1, n_words), 2) for k in CLASSES}}
    # V5: the ten texts with the highest density (at least 2 000 words; runestones excluded)
    dens = [(c, n, round(1e4 * sum(per_text[(c, n)].values()) / words[(c, n)], 1), sum(per_text[(c, n)].values()))
            for (c, n) in words if words[(c, n)] >= 2000 and not c.startswith("runstenar")]
    res["V5"] = sorted(dens, key=lambda x: -x[2])[:10]
    # V4 runestones
    res["V4"] = [{"sten": r["text"], "term": r["term"], "ord": r["ord"]} for r in rows if r["korpus"] == "runstenar_SE"]

    # T1–T3
    def units(c, skip_troll=False, drop_largest=False):
        keys = [k for k in words if k[0] == c]
        if drop_largest:
            keys.remove(max(keys, key=lambda k: words[k]))
        cnt = {}
        for k in keys:
            cc = Counter({kl: n for kl, n in per_text[k].items() if kl not in dropped})
            if skip_troll:
                cc["jättar"] -= sum(1 for r in rows if (r["korpus"], r["text"]) == k and r["term"] == "tröll")
            cnt[k] = cc
        return [(cnt[k], words[k]) for k in keys]

    def rate(s):
        return 1e4 * sum(sum(c.values()) for c, _ in s) / sum(n for _, n in s)

    def dead_share(s):
        tot = sum(sum(c.values()) for c, _ in s)
        return 100 * sum(c["de döda"] for c, _ in s) / tot if tot else None

    def tests(variant, **kw):
        r = random.Random(SEED)
        F, I, S = units("fornaldarsagor", **kw), units("islanningasagor", **kw), units("samtidssagor", **kw)
        out = {}
        bf, bi = boot(F, rate, r), boot(I, rate, r)
        ratio = [a / b for a, b in zip(bf, bi)]
        out["T1"] = {"fornaldar": round(rate(F), 2), "islänninga": round(rate(I), 2), "kvot": round(rate(F) / rate(I), 2),
                     "intervall": ci(ratio), "p": p_two(ratio, 1.0)}
        df, di = boot(F, dead_share, r), boot(I, dead_share, r)
        diff = [b - a for a, b in zip(df, di) if a is not None and b is not None]
        out["T2"] = {"islänninga_%": round(dead_share(I), 1), "fornaldar_%": round(dead_share(F), 1),
                     "skillnad_pe": round(dead_share(I) - dead_share(F), 1), "intervall": ci(diff), "p": p_two(diff, 0.0)}
        n_s = sum(sum(c.values()) for c, _ in S)
        if n_s >= 20:
            bs = boot(S, rate, r)
            ratio3 = [a / b for a, b in zip(bs, bi)]
            out["T3"] = {"samtid": round(rate(S), 2), "islänninga": round(rate(I), 2), "kvot": round(rate(S) / rate(I), 2),
                         "intervall": ci(ratio3), "p": p_two(ratio3, 1.0), "träffar_samtid": n_s}
        else:
            out["T3"] = {"obestämt": True, "träffar_samtid": n_s}
        ps = sorted((out[t]["p"], t) for t in ("T1", "T2", "T3") if "p" in out[t])
        m = len(ps)
        prev = 0.0
        for i, (p, t) in enumerate(ps):
            adj = max(prev, min(1.0, (m - i) * p))
            prev = adj
            out[t]["p_holm"] = round(adj, 4)
            null = 0.0 if t == "T2" else 1.0
            lo, hi = out[t]["intervall"]
            out[t]["håller"] = adj < 0.05 and not (lo <= null <= hi)
        return out

    res["tester"] = {"huvud": tests("huvud"), "utan_tröll": tests("utan tröll", skip_troll=True),
                     "utan_största_sagan": tests("utan största", drop_largest=True)}
    json.dump(res, open(os.path.join(HERE, "matt.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"V2": {c: res["V2"][c]["per_10000_ord"] for c in corpora}, "tester": res["tester"]}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    grind() if "--grind" in sys.argv else grind2() if "--grind2" in sys.argv else main()
