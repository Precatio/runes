"""Hávamáls ordförråd mot runstenarnas, land för land.

Artikelns korsning byggde topp-200 ur HELA Rundatas vikingatida runstensbestånd (alla länder).
Här delas korpusen upp i Sverige, Danmark (DR) och Norge (N) och mäts separat, med en
storlekskontroll: topp-200 ur en liten korpus når djupare ner i vardagsorden, så råa medianer
jämförs bara efter stickprov med lika många löpord. Resultat → havamal_runkorpus_per_land.json.
"""
import csv, re, json, random, statistics
from collections import Counter
from src import runlm as rl

ROT = "utdata/Edda"
TOPP = 200
MIN_TYPER = 8  # samma strofgräns som i djupmönster-körningen

rows = list(csv.DictReader(open(f"{ROT}/havamal_strofer.csv")))
tok = lambda t: re.findall(r"[a-zþðæöøáéíóúýœå]+", t.lower())
strofer = []
for r in rows:
    types = {rl.key(w) for w in tok(r["text"])}
    if len(types) >= MIN_TYPER:
        strofer.append((r["del"], int(r["nr"]), types))

recs = [r for r in rl.load_rundata() if rl.viking(r) and rl.object_kind(r) == "runsten"]
def land(sig):
    p = sig.split(" ")[0]
    if p.startswith("DR"): return "Danmark"
    if p == "N": return "Norge"
    if p in ("IS", "GR", "IM", "IR", "E", "Or", "Sc", "Sh", "F", "By",
             "RU", "FI", "Fær", "NL", "PL", "UA", "LV"): return "övriga"
    return "Sverige"
korpusar = {}
for r in recs:
    korpusar.setdefault(land(r["signum"]), []).append(r)

def ordlista(rs):
    """Nyckel-normaliserade löpord per sten (stæinn=sten=steinn räknas lika)."""
    ut = []
    for r in rs:
        ut.append([rl.key(rl.normtok(w)) for w in rl.norm_words(r.get("normalization") or "")])
    return ut

ORD = {k: ordlista(v) for k, v in korpusar.items() if k != "övriga"}
TOKENS = {k: sum(len(s) for s in v) for k, v in ORD.items()}

def toppset(stenord, n=TOPP):
    c = Counter(w for s in stenord for w in s)
    return set(w for w, _ in c.most_common(n)), len(c)

def median_traff(ts):
    return statistics.median(sum(1 for t in typer if t in ts) / len(typer)
                             for _, _, typer in strofer)

resultat = {"metod": {"topp": TOPP, "min_typer": MIN_TYPER, "strofer": len(strofer)}, "rå": {}, "kontroll": {}}

# 1) Råa korpusar: median totalt + per del, och ordtypstäckning
for namn, stenord in ORD.items():
    ts, vocab = toppset(stenord)
    per_del = {}
    for d in "I II III IV V VI".split():
        dv = [sum(1 for t in typer if t in ts) / len(typer) for dd, _, typer in strofer if dd == d]
        per_del[d] = round(statistics.median(dv), 3)
    resultat["rå"][namn] = {"stenar": len(stenord), "löpord": TOKENS[namn], "ordtyper": vocab,
                            "median": round(median_traff(ts), 3), "per_del": per_del}

# 2) Storlekskontroll: stickprov med Norges löpordsmängd ur Sverige och Danmark (Norge = facit som den är)
rng = random.Random(1)
budget = TOKENS["Norge"]
ITER = 300
for namn in ("Sverige", "Danmark"):
    medianer = []
    for _ in range(ITER):
        ix = list(range(len(ORD[namn]))); rng.shuffle(ix)
        prov, n = [], 0
        for i in ix:
            prov.append(ORD[namn][i]); n += len(ORD[namn][i])
            if n >= budget: break
        medianer.append(median_traff(toppset(prov)[0]))
    resultat["kontroll"][namn] = {"budget_löpord": budget, "iterationer": ITER,
                                  "median_medel": round(statistics.mean(medianer), 3),
                                  "median_sd": round(statistics.stdev(medianer), 4),
                                  "_medianer": medianer}
resultat["kontroll"]["Norge"] = {"budget_löpord": budget,
                                 "median_medel": resultat["rå"]["Norge"]["median"], "median_sd": 0.0}
# Hur ofta når ett stickprov upp till Norges fasta värde?
for namn in ("Sverige", "Danmark"):
    over = sum(1 for m in resultat["kontroll"][namn]["_medianer"] if m >= resultat["rå"]["Norge"]["median"])
    resultat["kontroll"][namn]["andel_minst_norge"] = round(over / ITER, 3)

# 2b) Parvis Sverige mot Danmark på dansk korpusstorlek (stabilare än 560-ordsbudgeten)
medianer = []
for _ in range(ITER):
    ix = list(range(len(ORD["Sverige"]))); rng.shuffle(ix)
    prov, n = [], 0
    for i in ix:
        prov.append(ORD["Sverige"][i]); n += len(ORD["Sverige"][i])
        if n >= TOKENS["Danmark"]: break
    medianer.append(median_traff(toppset(prov)[0]))
resultat["kontroll_dansk_budget"] = {
    "budget_löpord": TOKENS["Danmark"], "iterationer": ITER,
    "sverige_median_medel": round(statistics.mean(medianer), 3),
    "sverige_median_sd": round(statistics.stdev(medianer), 4),
    "danmark_median": resultat["rå"]["Danmark"]["median"],
    "andel_sverige_minst_danmark": round(sum(1 for m in medianer if m >= resultat["rå"]["Danmark"]["median"]) / ITER, 3)}

# 3) Vilka ord gör skillnaden: Hávamál-typer som topp-200 fångar i ett land men inte ett annat
hav_typer = Counter(t for _, _, typer in strofer for t in typer)
tsets = {k: toppset(v)[0] for k, v in ORD.items()}
def diff(a, b):
    d = [(hav_typer[t], t) for t in tsets[a] - tsets[b] if t in hav_typer]
    return [t for _, t in sorted(d, reverse=True)]
resultat["ord_diff"] = {"dansk_ej_svensk": diff("Danmark", "Sverige")[:25],
                        "svensk_ej_dansk": diff("Sverige", "Danmark")[:25],
                        "norsk_ej_svensk": diff("Norge", "Sverige")[:25]}

for namn in ("Sverige", "Danmark"):
    del resultat["kontroll"][namn]["_medianer"]
json.dump(resultat, open(f"{ROT}/havamal_runkorpus_per_land.json", "w"), ensure_ascii=False, indent=1)
for namn, d in resultat["rå"].items():
    print(f"{namn}: {d['stenar']} stenar, {d['löpord']} löpord → median {d['median']:.3f}  per del {d['per_del']}")
print("kontroll (lika löpord):", {k: v["median_medel"] for k, v in resultat["kontroll"].items()})
print("dansk-ej-svensk:", resultat["ord_diff"]["dansk_ej_svensk"][:15])
print("norsk-ej-svensk:", resultat["ord_diff"]["norsk_ej_svensk"][:15])
