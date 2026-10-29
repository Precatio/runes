"""Namnen som levde kvar: prövar H1–H4 enligt den låsta planen analysplaner/2026-10-29-namnen-som-levde-kvar.md
med det låsta lexikonet lexikon.csv. H1 och H4 (logistisk regression med brevet som kluster) körs i R (modeller.R).
    .venv/bin/python utdata/namnarv/analys.py      Skriver namn_belagg.csv, personer.csv och namnarv.json."""
import hashlib
import json
import os
import re
import subprocess

import numpy as np
import pandas as pd
from scipy.stats import binomtest, fisher_exact

OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(OUT, "..", ".."))
assert hashlib.sha256(open(os.path.join(OUT, "lexikon.csv"), "rb").read()).hexdigest() == \
    open(os.path.join(OUT, "lexikon.sha256")).read().split()[0], "lexikonet har ändrats efter låsningen"
lex = pd.read_csv(os.path.join(OUT, "lexikon.csv"), keep_default_na=False)
lex = lex[lex.ursprung.isin(["N", "K"])]
L = lex.set_index("ord")
THEO = ("thor", "as", "frey", "ing", "gud")

# ---- förnamnsbelägg ---------------------------------------------------------------------------------------------------
o = pd.read_csv(os.path.join(OUT, "ord.csv"), keep_default_na=False)
o = o[o.ord.isin(L.index)].copy()
o["n"] = np.where(L.loc[o.ord, "tvetydig"].to_numpy() == 1, o.antal_inne_i_mening, o.antal)
o = o[o.n > 0]
o["ar"] = pd.to_numeric(o.datum.astype(str).str[:4], errors="coerce")
for k in ("normalform", "kon", "ursprung", "runsten"):
    o[k] = L.loc[o.ord, k].to_numpy()
o["nordiskt"] = (o.ursprung == "N").astype(int)
o["halva"] = np.where(o.brev.astype(int) % 2 == 0, "A", "B")
o.to_csv(os.path.join(OUT, "namn_belagg.csv"), index=False)

# ---- fader–barn-par -------------------------------------------------------------------------------------------------
SUF = re.compile(r"(son|sson|sun|ssun|søn|sone|soni|dotter|dottir|dotir|dottor|dotor|dottur|döttir|dotr)$")


def father(p):
    stem = SUF.sub("", p)
    for c in (stem, stem[:-1] if stem[-1:] in "sxz" else None, stem + "s" if stem else None):
        if c and c in L.index:
            return c
    return None


p = pd.read_csv(os.path.join(OUT, "par.csv"), keep_default_na=False)
p = p[p.fornamn.isin(L.index)].copy()
p["fader_ord"] = p.patronymikon.map(father)
p = p[p.fader_ord.notna()]
p["barn"] = L.loc[p.fornamn, "normalform"].to_numpy()
p["fader"] = L.loc[p.fader_ord, "normalform"].to_numpy()
p["barn_N"] = (L.loc[p.fornamn, "ursprung"].to_numpy() == "N").astype(int)
p["fader_N"] = (L.loc[p.fader_ord, "ursprung"].to_numpy() == "N").astype(int)
p["kon"] = np.where(p.patronymikon.str.contains("dot|döt"), "k", L.loc[p.fornamn, "kon"].to_numpy())
p["ar"] = pd.to_numeric(p.datum.astype(str).str[:4], errors="coerce")
# En person = barnets och faderns namn; tidigaste brevet avgör år och halva
pers = p.sort_values(["ar", "brev"]).groupby(["barn", "fader"], as_index=False).first()
pers["halva"] = np.where(pers.brev.astype(int) % 2 == 0, "A", "B")
pers.to_csv(os.path.join(OUT, "personer.csv"), index=False)


def mcnemar(d):
    b = int(((d.barn_N == 1) & (d.fader_N == 0)).sum())  # barnet nordiskt, fadern inte
    c = int(((d.barn_N == 0) & (d.fader_N == 1)).sum())  # fadern nordisk, barnet inte
    t = binomtest(c, b + c, 0.5) if b + c else None
    return {"personer": len(d), "andel_barn_N": float(d.barn_N.mean()), "andel_fader_N": float(d.fader_N.mean()),
            "barn_N_fader_K": b, "barn_K_fader_N": c, "p": float(t.pvalue) if t else None}


H2 = {"alla": mcnemar(pers), "A": mcnemar(pers[pers.halva == "A"]), "B": mcnemar(pers[pers.halva == "B"]),
      "per_period": {str(k): mcnemar(g) for k, g in pers.groupby(pd.cut(pers.ar, [1200, 1350, 1400, 1450, 1600]))},
      "forekomster": mcnemar(p.loc[p.index.repeat(p.antal)])}

# ---- H3: vilka runstensnamn överlevde --------------------------------------------------------------------------------
rn = json.load(open(os.path.join(OUT, "runnamn.json"), encoding="utf-8"))
men = [(k, n) for k, n in sorted(rn["counts"].items(), key=lambda x: -x[1]) if rn["female"].get(k) is False
       and not k.endswith("-")][:100]
found_keys = {k for ks in lex.runsten for k in ks.split(",") if k}
belagg_per_key = {}
for _, r in o[o.runsten != ""].iterrows():
    for k in r.runsten.split(","):
        belagg_per_key[k] = belagg_per_key.get(k, 0) + int(r.n)
top = pd.DataFrame(men, columns=["nyckel", "runstenar"])
top["i_breven"] = top.nyckel.isin(found_keys).astype(int)
top["belagg_i_breven"] = top.nyckel.map(belagg_per_key).fillna(0).astype(int)
top["gudanamn"] = top.nyckel.str.startswith(THEO).astype(int)
tab = pd.crosstab(top.gudanamn, top.i_breven).reindex(index=[0, 1], columns=[0, 1], fill_value=0)
odds, p3 = fisher_exact(tab.to_numpy())
H3 = {"overlevde_gudanamn": f"{tab.loc[1, 1]}/{tab.loc[1].sum()}", "overlevde_ovriga": f"{tab.loc[0, 1]}/{tab.loc[0].sum()}",
      "odds_ratio": float(odds), "p": float(p3), "namn": top.to_dict("records")}

# ---- H1 och H4 i R ---------------------------------------------------------------------------------------------------
subprocess.run(["Rscript", os.path.join(OUT, "modeller.R"), OUT], check=True)
R = json.load(open(os.path.join(OUT, "modeller.json"), encoding="utf-8"))

ps = {"H1": R["H1"]["alla"]["p"], "H2": H2["alla"]["p"], "H3": H3["p"], "H4": R["H4"]["alla"]["p"]}
order = sorted(ps, key=ps.get)
holm, run = {}, 0.0
for i, k in enumerate(order):
    run = max(run, min(1.0, (len(ps) - i) * ps[k]))
    holm[k] = run


def status(k, both):
    if holm[k] < 0.05 and both:
        return "håller"
    return "antydan" if holm[k] < 0.05 or ps[k] < 0.05 else "ingen skillnad påvisad"


def same(a, b, key):
    return all(x["p"] is not None and x["p"] < 0.05 for x in (a, b)) and \
        (np.sign(np.log(a[key])) == np.sign(np.log(b[key])) if key == "or" else True)


st = {"H1": status("H1", same(R["H1"]["A"], R["H1"]["B"], "or") and R["H1"]["A"]["or"] < 1),
      "H2": status("H2", all(H2[h]["p"] is not None and H2[h]["p"] < 0.05 and
                             H2[h]["barn_K_fader_N"] > H2[h]["barn_N_fader_K"] for h in "AB")),
      "H3": status("H3", True), "H4": status("H4", same(R["H4"]["A"], R["H4"]["B"], "or"))}
desc = {"per_halvsekel": o.groupby((o.ar // 50) * 50).apply(lambda g: {"belagg": int(g.n.sum()),
        "andel_N": float((g.n * g.nordiskt).sum() / g.n.sum())}).to_dict(),
        "per_kon": o.groupby("kon").apply(lambda g: float((g.n * g.nordiskt).sum() / g.n.sum())).to_dict(),
        "vanligaste": {str(int(k)): g.groupby("normalform").n.sum().sort_values(ascending=False).head(15).to_dict()
                       for k, g in o.groupby((o.ar // 50) * 50) if k >= 1300},
        "ort": o.groupby("ort").apply(lambda g: {"belagg": int(g.n.sum()),
               "andel_N": float((g.n * g.nordiskt).sum() / g.n.sum())}).to_dict()}
res = {"plan": "analysplaner/2026-10-29-namnen-som-levde-kvar.md", "belagg": int(o.n.sum()), "brev": int(o.brev.nunique()),
       "H1": R["H1"], "H2": H2, "H3": H3, "H4": R["H4"], "holm": holm, "status": st, "robusthet": R["robusthet"],
       "beskrivning": desc}
json.dump(res, open(os.path.join(OUT, "namnarv.json"), "w"), ensure_ascii=False, indent=1, default=str)
print("belägg", res["belagg"], "brev", res["brev"], "personer", len(pers))
for k in ("H1", "H2", "H3", "H4"):
    print(k, st[k], "p", ps[k], "holm", holm[k])
print("H1", {h: (round(R["H1"][h]["or"], 3), R["H1"][h]["p"]) for h in ("alla", "A", "B")})
print("H2", {h: {kk: (round(v, 3) if isinstance(v, float) else v) for kk, v in H2[h].items()} for h in ("alla", "A", "B", "forekomster")})
print("H2 per period", H2["per_period"])
print("H3", {k: v for k, v in H3.items() if k != "namn"})
print("H4", {h: (round(R["H4"][h]["or"], 3), R["H4"][h]["p"]) for h in ("alla", "A", "B")})
print("robusthet", R["robusthet"])
print("per halvsekel", desc["per_halvsekel"]); print("per kön", desc["per_kon"])
