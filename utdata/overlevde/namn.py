"""Del A i analysplaner/2026-10-30-namnen-och-orden-som-overlevde.md: lever runstenarnas personnamn i Sverige i dag?
    .venv/bin/python utdata/overlevde/namn.py      Skriver namn.csv, matchningar.csv och namn.json."""
import csv
import json
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict

from scipy.stats import fisher_exact

OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(OUT, "..", ".."))
sys.path.insert(0, ROOT)
from api.rundata import store  # noqa: E402
from src import entities, people  # noqa: E402
from src.research_gaps import is_runestone  # noqa: E402

MIN_STONES = 3
# Sensitivity (not in the locked plan; added after the review found Ástríðr → Åstrid but not Astrid, Halfdan not
# Halvdan): EXTRA_RULES=1 adds å→a, Å→A and f→v, and leaves out name fragments ("Þor-", "Guð-")
EXTRA = os.environ.get("EXTRA_RULES") == "1"
MIN_BEARERS = 10
THEO = re.compile(r"^(Þór|Þor|Thor|Ás|Ôs|Os|As|Frey|Frø|Ingi|Yngv|Guð|Gud)", re.I)
ROYAL = {"Eiríkr", "Óláfr", "Knútr", "Sveinn", "Haraldr", "Hákon", "Ingi", "Magnús", "Bjôrn", "Emundr", "Anundr",
         "Steinkell"}
TITLE = re.compile(r"\b(þegn\w*|dræng\w*|drængi\w*|styrimann\w*|skipari\w*|landmann\w*|huskarl\w*|konung\w*|jarl\w*)",
                   re.I)

s = store()
recs = [r for r in s.inscriptions if is_runestone(r)]
lex = people.lexicon(s.inscriptions)

# ---- names on the runestones: stones per name, sex, and whether a bearer is called by a title -----------------------
stones, sexes, titled = defaultdict(set), defaultdict(Counter), defaultdict(bool)
for r in recs:
    try:
        x = entities.extract(r)
    except Exception:  # noqa: BLE001
        continue
    text = people._text_genders(r)
    norm = r.get("normalization") or ""
    for p in x["persons"]:
        if p.get("uncertain") or not p.get("name"):
            continue
        n = p["name"]
        stones[n].add(r["signum"])
        g = ("k" if p.get("rel") in entities.FEMALE else people.gender(n, text, lex))
        sexes[n][g] += 1
        # a title right after the name in the normalization ("Fót, harða goðan þegn"): within the same clause
        m = re.search(re.escape(n.split()[0]).replace("\\ ", " ") + r"[^.;]{0,40}?" + TITLE.pattern, norm, re.I)
        if m:
            titled[n] = True
names = {n: len(v) for n, v in stones.items() if len(v) >= MIN_STONES
         and not (EXTRA and (n.endswith("-") or len(n) <= 3 and not n[-1].isalpha() or n in ("Ásl",)))}


def sex_of(n):
    c = sexes[n]
    return "k" if c["k"] > c["m"] else ("m" if c["m"] > 0 or c["k"] == 0 else "?")


# ---- modern forms ---------------------------------------------------------------------------------------------------
lexrows = list(csv.DictReader(open(os.path.join(ROOT, "utdata", "namnarv", "lexikon.csv"), encoding="utf-8")))
by_key = defaultdict(set)
for x in lexrows:
    if x["runsten"]:
        by_key[x["runsten"]].add(x["normalform"])


def fold(n):
    s_ = unicodedata.normalize("NFKD", n.replace("Þ", "Th").replace("þ", "th").replace("ð", "d").replace("ô", "o")
                               .replace("æ", "ae").replace("ø", "o"))
    return re.sub(r"[^a-z]", "", "".join(ch for ch in s_ if not unicodedata.combining(ch)).lower())


def _translit(n, a_long="å"):
    t = n
    for a, b in (("Þ", "T"), ("þ", "t"), ("ð", "d"), ("ô", "å"), ("Ó", "O"), ("ó", "o"), ("Á", a_long.upper()),
                 ("á", a_long), ("Æ", "Ä"), ("æ", "ä"), ("ø", "ö"), ("ey", "ö"), ("Ey", "Ö"), ("ei", "e"), ("Ei", "E"),
                 ("au", "ö"), ("Au", "Ö"), ("í", "i"), ("Í", "I"), ("ú", "u"), ("Ú", "U"), ("ý", "y"), ("é", "e"),
                 ("É", "E")):
        t = t.replace(a, b)
    t = re.sub(r"rr$", "r", t)
    t = re.sub(r"([^aeiouyåäöAEIOUYÅÄÖr])r$", r"\1", t)
    return re.sub(r"nn$", "n", t)


def rules(n, sex="?"):
    t = _translit(n)
    out = {t}
    # Old Norse weak masculines end in -i where Swedish has -e (Helgi → Helge, Áki → Åke, Kári → Kåre). Added
    # 2026-10-30 after Viktor asked about Helge; not in the locked plan (resultat.md, Avvikelser). Men only: for women
    # -a → -e gives men's names (Helga → Helge, Þóra → Tore).
    if sex == "m" and t.endswith("i"):
        out.add(t[:-1] + "e")
    for a, b in (("ä", "e"), ("å", "o"), ("o", "å")):
        out |= {x.replace(a, b) for x in list(out)}
    if EXTRA:  # á as a (Ástríðr → Astrid) and f as v (Tófa → Tova), on the name itself, not chained
        alt = _translit(n, "a")
        out |= {alt, alt.replace("f", "v"), t.replace("f", "v")}
    return {x[:1].upper() + x[1:] for x in out if x}


scb = json.load(open(os.path.join(ROOT, "data", "namn", "scb_tilltalsnamn.json"), encoding="utf-8"))["names"]
alive = defaultdict(int)
for x in scb:
    if x["n2020"]:
        alive[(x["name"], x["sex"])] += x["n2020"]
alive_any = Counter()
for (nm, sx), v in alive.items():
    alive_any[nm] += v

# False hits found in the review of matchningar.csv (2026-10-30): the modern form is another name
FALSE = {"Danr": "Dan i dag är främst bibliskt (Daniel/Dan), inte runstenens Danr",
         "Eilífr": "Elif är ett turkiskt kvinnonamn",
         "Hæra": "Hera är den grekiska gudinnan",
         "Kali": "Kali i dag är ett indiskt eller finskt namn",
         "Uni": "Uni i dag är ett utländskt kort namn, inte runstenens Uni",
         "Veðr": "Ved i dag är inte runstenens Veðr",
         # from the -i → -e rule (2026-10-30): forms whose modern use has another origin
         "Ási": "Åse bärs i dag bara av kvinnor (det norska kvinnonamnet), inte runstenens mansnamn Ási",
         "Viði": "Vide är ett nytt naturnamn (89 bärare 1999, 1 665 år 2020), inte runstenens Viði",
         "Manni": "Manne är i dag en kortform av Emanuel eller Herman",
         "Tobbi": "Tobbe är i dag ett smeknamn för Tobias eller Torbjörn",
         "Soni": "Sone har oklart ursprung i dag",
         **({"Áli": "Ali i dag är det arabiska namnet, inte runstenens Áli",
             "Káti": "Kati i dag är ett finskt kvinnonamn", "Sylfa": "Sylva är latinets Silvia",
             "Óleifr": "Olev är estniskt; Óleifr bör motsvara Olof, som regeln inte når",
             } if EXTRA else {})}
# False modern forms of a name that otherwise has a true descendant: only that form is left out
FALSE_FORMS = {("Kári", "Kari"): "Kari i dag är finskt eller norskt och tvetydigt; Kåre är ättlingen"}
CHRISTIAN = {"Jóhan", "Jón", "Kristr", "Pétr", "Andreas", "Nikulás"}  # Christian names already on the runestones

rows, matches = [], []
for n, k in sorted(names.items(), key=lambda x: -x[1]):
    sx = sex_of(n)
    cands = sorted(by_key.get(fold(n), set()) | rules(n, sx))
    hits = {} if n in FALSE else {c: alive_any[c] for c in cands
                                  if alive_any[c] >= MIN_BEARERS and (n, c) not in FALSE_FORMS}
    best = max(hits, key=hits.get) if hits else ""
    rows.append({"name": n, "stones": k, "sex": sx, "theophoric": int(bool(THEO.match(n))), "royal": int(n in ROYAL),
                 "titled": int(titled[n]), "in_medieval_lexicon": int(bool(by_key.get(fold(n)))),
                 "christian": int(n in CHRISTIAN), "false_hit": FALSE.get(n, ""),
                 "candidates": "|".join(cands), "modern": best, "bearers_2020": hits.get(best, 0),
                 "alive": int(bool(hits))})
    for c, v in hits.items():
        matches.append({"name": n, "modern": c, "bearers_2020": v,
                        "source": "lexikon" if c in by_key.get(fold(n), set()) else "regel"})
with open(os.path.join(OUT, "namn_extra.csv" if EXTRA else "namn.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
with open(os.path.join(OUT, "matchningar_extra.csv" if EXTRA else "matchningar.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(matches[0]))
    w.writeheader()
    w.writerows(matches)
print(len(rows), "namn på minst", MIN_STONES, "stenar;", sum(r["alive"] for r in rows), "lever")


# ---- tests (Holm over N1–N3) and description -------------------------------------------------------------------------
def share(xs):
    return sum(r["alive"] for r in xs) / len(xs) if xs else None


def fisher(a, b, alt):
    t = [[sum(r["alive"] for r in a), len(a) - sum(r["alive"] for r in a)],
         [sum(r["alive"] for r in b), len(b) - sum(r["alive"] for r in b)]]
    odds, p = fisher_exact(t, alternative=alt)
    return {"a": t[0], "b": t[1], "share_a": share(a), "share_b": share(b), "or": odds, "p": p}


known = [r for r in rows if r["sex"] in ("m", "k")]
res = {"n_names": len(rows), "alive": sum(r["alive"] for r in rows), "share": share(rows),
       "bearer_weighted": sum(r["stones"] * r["alive"] for r in rows) / sum(r["stones"] for r in rows),
       "false_hits": FALSE}
res["N1"] = fisher([r for r in known if r["sex"] == "k"], [r for r in known if r["sex"] == "m"], "less")
res["N2"] = fisher([r for r in rows if r["theophoric"]], [r for r in rows if not r["theophoric"]], "two-sided")
tit = [r for r in rows if r["titled"]]
res["N3"] = (fisher(tit, [r for r in rows if not r["titled"]], "less") if len(tit) >= 15
             else {"too_few": len(tit), "names": [r["name"] for r in tit]})
ps = {k: res[k]["p"] for k in ("N1", "N2", "N3") if "p" in res[k]}
order = sorted(ps, key=ps.get)
run = 0
for i, k in enumerate(order):
    run = max(run, min(1, ps[k] * (len(ps) - i)))
    res[k]["holm"] = run
res["royal"] = [{"name": r["name"], "modern": r["modern"], "bearers": r["bearers_2020"]} for r in rows if r["royal"]]
res["christian"] = [{"name": r["name"], "alive": r["alive"]} for r in rows if r["christian"]]
res["without_christian_share"] = share([r for r in rows if not r["christian"]])
med = [r for r in rows if r["in_medieval_lexicon"]]
res["chain"] = {"in_letters": len(med), "in_letters_alive": sum(r["alive"] for r in med),
                "not_in_letters": len(rows) - len(med), "not_in_letters_alive": sum(r["alive"] for r in rows if not r["in_medieval_lexicon"])}
res["top_alive"] = [{"name": r["name"], "modern": r["modern"], "stones": r["stones"], "bearers": r["bearers_2020"]}
                    for r in sorted(rows, key=lambda r: -r["stones"]) if r["alive"]][:25]
res["top_dead"] = [{"name": r["name"], "stones": r["stones"], "sex": r["sex"]}
                   for r in sorted(rows, key=lambda r: -r["stones"]) if not r["alive"]][:25]
json.dump(res, open(os.path.join(OUT, "namn_extra.json" if EXTRA else "namn.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1, default=float)
print(json.dumps({k: res[k] for k in ("n_names", "alive", "share", "bearer_weighted", "N1", "N2", "N3", "chain",
                                      "without_christian_share")}, ensure_ascii=False, default=float, indent=0)[:2500])
