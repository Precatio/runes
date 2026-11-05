"""Kontroll efter granskningen 2026-11-05 (rapporten ristningen-vand-mot-vagen, rapportversion 3): gon-tilläggen.

Registret anger ofta en bäring som ett väderstreck plus ett tillägg i gon (centesimalgrader, 400 på ett varv), till
exempel "4,5 m V 40cg S om landsväg" = 40 gon (36 grader) från väster mot söder. Den låsta analysen (analys.py, planen
2026-10-29) läser bara ett väderstreck: för vägen det som står närmast före "om väg" (här S), för ristningen det som står
direkt efter "vetter mot" (i "vetter mot S 20cg V" alltså S). Skriptet ändrar inte den låsta analysen eller dess filer.
Det gör om urvalet med samma regler, kontrollerar att det ger exakt stenar.csv, läser tilläggen rätt för samma poster och
räknar om:
- beskrivande mått (medel-cos, andel inom 45 grader) för alla stenar med väg, vägar ur registrets text, halvorna;
- samma omblandningstest som planen (9 999 inom landskapet, ensidigt) – en kontroll i efterhand, inte en del av planen;
- samma sak när varje sten räknas en gång (fem stenar har två poster var i registret; vid två poster väljs, som i
  planen, i första hand den med väg ur registrets text);
- alla känslighetsanalyser i tilläggsplanen 2026-10-31 med samma kod som trappa.py och samma slumpfrö; koden prövas
  först på de lästa riktningarna och måste då ge trappan.json exakt, också p-värdena.
Dessutom antecknas när indata hämtades (för rapportens avsnitt Data och kod).
    .venv/bin/python utdata/riktning/gon_kontroll.py      Skriver gon_kontroll.json."""
import datetime as dt
import hashlib
import json
import os
import re

import numpy as np
import pandas as pd

OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(OUT, "..", ".."))
NPERM = 9999
rng = np.random.default_rng(2026)
STRECK = ["N", "NNÖ", "NÖ", "ÖNÖ", "Ö", "ÖSÖ", "SÖ", "SSÖ", "S", "SSV", "SV", "VSV", "V", "VNV", "NV", "NNV"]
DEG = {s: i * 22.5 for i, s in enumerate(STRECK)}
D = "(" + "|".join(sorted(STRECK, key=len, reverse=True)) + ")"
NUM = r"(\d+(?:[,.]\d+)?)\s*(cg|gon|g|°|grader)\b\.?"
KMR = os.path.join(ROOT, "data", "raa", "kmr_runstenar.json")
CORPUS = os.path.join(ROOT, "data", "cache", "r", "corpus", "3f58e9339191761e", "corpus.csv")


def qualified(base: str, value: str, unit: str, toward: str) -> float:
    """Bäringen för 'base value unit toward', t.ex. V 40 cg S = 270 − 36 = 234 grader."""
    b0, q = DEG[base], DEG[toward]
    delta = (q - b0 + 180) % 360 - 180
    assert abs(delta) == 90, (base, toward)  # tillägget går alltid vinkelrätt från ett huvudväderstreck
    ang = float(value.replace(",", ".")) * (0.9 if unit in ("cg", "gon", "g") else 1.0)
    assert 0 < ang <= 45, (base, value, unit, toward)
    return (b0 + np.sign(delta) * ang) % 360


# ---- samma urval som analys.py, rad för rad ------------------------------------------------------------------------------
c = pd.read_csv(CORPUS, low_memory=False).set_index("signum")
kmr = json.load(open(KMR, encoding="utf-8"))
rows = []
for r in kmr["records"]:
    b = " ".join(r["fields"].get("Beskrivning", []))
    o = " ".join(r["fields"].get("Orientering", []))
    f = re.findall(r"vetter? mot " + D + r"\b", b)
    sig = [s for s in r["signa"] if s in c.index]
    if len(sig) != 1 or len(set(f)) != 1:
        continue
    s = sig[0]
    if c.loc[s, "moved"] != 0 or c.loc[s, "lost"] != 0 or pd.isna(c.loc[s, "lat"]):
        continue
    t = b + " " + o
    m = re.search(r"\b" + D + r" om (?:lands|by|gång|skogs|gammal |gamla )?väg", t)
    # ristningen: ett tillägg direkt efter "vetter mot X"
    fr = []
    for mm in re.finditer(r"vetter? mot " + D + r"\b", b):
        q = re.match(r"\s*" + NUM + r"\s*" + D + r"\b", b[mm.end():])
        fr.append((qualified(mm.group(1), q.group(1), q.group(2), q.group(3)), b[mm.start():mm.end() + q.end()]) if q else
                  (DEG[mm.group(1)], None))
    assert len({x for x, _ in fr}) == 1, (s, fr)
    # vägen: ett tillägg direkt före det väderstreck som den låsta regeln läste
    vt, vtxt = np.nan, None
    if m:
        vt = (DEG[m.group(1)] + 180) % 360
        q = re.search(r"\b" + D + r"\s*" + NUM + r"\s*$", t[:m.start()])
        if q:
            vt, vtxt = (qualified(q.group(1), q.group(2), q.group(3), m.group(1)) + 180) % 360, t[q.start():m.end()]
    rows.append({"signum": s, "kmr_id": r["kmr_id"], "streck": f[0], "riktning_las": DEG[f[0]], "riktning": fr[0][0],
                 "riktning_text": fr[0][1], "vag_text_las": (DEG[m.group(1)] + 180) % 360 if m else np.nan, "vag_text": vt,
                 "vag_text_kalla": vtxt})
g = pd.DataFrame(rows)
st = pd.read_csv(os.path.join(OUT, "stenar.csv"))
assert len(g) == len(st) == 219 and (g.signum.to_numpy() == st.signum.to_numpy()).all()
assert (g.streck.to_numpy() == st.streck.to_numpy()).all() and np.allclose(g.riktning_las, st.riktning)
assert np.allclose(g.vag_text_las.fillna(-1), st.vag_text.fillna(-1))  # urvalet och läsningen är exakt den låsta

d = st.copy()
d["riktning_r"] = g.riktning.to_numpy()
d["vag_text_r"] = g.vag_text.to_numpy()
d["vag_r"] = d.vag_text_r.fillna(d.vag_reg)
d["kmr_id"] = g.kmr_id.to_numpy()


def ang_diff(a, b):
    return np.abs((a - b + 180) % 360 - 180)


def describe(x, fcol, tcol):
    x = x[x[tcol].notna()]
    f, t = x[fcol].to_numpy(float), x[tcol].to_numpy(float)
    return {"n": int(len(x)), "medel_cos": float(np.cos(np.radians(f - t)).mean()),
            "andel_inom_45": float((ang_diff(f, t) <= 45 + 1e-9).mean())}


def perm_test(x, fcol, tcol):
    """Samma nollmodell som planens H2/H3: riktningarna blandas om inom landskapet, ensidigt."""
    x = x[x[tcol].notna()].reset_index(drop=True)
    f, t = x[fcol].to_numpy(float), x[tcol].to_numpy(float)
    groups = list(x.groupby("province").indices.values())
    stat = lambda ff: np.cos(np.radians(ff - t)).mean()  # noqa: E731
    obs = stat(f)
    sims = np.empty(NPERM)
    for i in range(NPERM):
        idx = np.arange(len(x))
        for gi in groups:
            idx[gi] = rng.permutation(gi)
        sims[i] = stat(f[idx])
    return {**describe(x, fcol, tcol), "vantat": float(sims.mean()), "p": float((1 + (sims >= obs).sum()) / (NPERM + 1))}


def rayleigh(deg):
    a = np.radians(np.asarray(deg, float)); n = len(a)
    R = np.hypot(np.cos(a).sum(), np.sin(a).sum())
    return {"n": n, "R": float(R / n), "p": float(min(1, np.exp(np.sqrt(1 + 4 * n + 4 * (n ** 2 - R ** 2)) - (1 + 2 * n))))}


# en sten en gång: vid två poster i första hand den med väg ur registrets text (planens ordning), annars den första
d["_pri"] = d.vag_text_r.isna().astype(int)
u = d.sort_values(["signum", "_pri"], kind="stable").drop_duplicates("signum").sort_index()
dups = sorted(d.signum[d.signum.duplicated()].unique())

# ---- känslighetsanalyserna (trappa.py, tilläggsplanen 2026-10-31) med samma kod och samma slumpfrö --------------------------
import sys  # noqa: E402
sys.path.insert(0, ROOT)
from src import robustness  # noqa: E402

c2 = pd.read_csv(os.path.join(ROOT, "data", "cache", "r", "corpus", "e83202e01a5e6d27", "corpus.csv"), low_memory=False).set_index("signum")
RUNOR = robustness._runor_moved()
REERECT = re.compile(r"återrest|återupprest|rest upp|restes upp|uppsatt|uppställd|lagad|lagades|lagats|reparerad", re.I)
kmr_t = {}
for r in kmr["records"]:
    t = " ".join(" ".join(r["fields"].get(k, [])) for k in ("Beskrivning", "Placering", "Skadestatus", "Orientering"))
    for s in r["signa"]:
        kmr_t[s] = kmr_t.get(s, "") + " " + t
rd = {r["signum"]: f"{r.get('placement') or ''} {r.get('other') or ''}"
      for r in json.load(open(os.path.join(ROOT, "data", "rundata.json")))["inscriptions"]}


def ladder(dd, rcol, vcol, tcol, rcol_reg="vag_reg"):
    """trappa.py rad för rad, med valbara kolumner för ristningens riktning och vägen; eget slumpfrö 2026 i samma ordning."""
    lrng = np.random.default_rng(2026)
    v = dd[dd[vcol].notna()].reset_index(drop=True).copy()
    v["riktning"], v["vag"], v["vag_text"], v["vag_reg"] = v[rcol], v[vcol], v[tcol], v[rcol_reg]
    v["parish"] = v.signum.map(lambda s: c2.parish.get(s)).fillna("_" + v.signum)
    v["carver"] = v.signum.map(lambda s: c2.carver.get(s) if c2.carvers_uncertain.get(s) == 0 else None)
    v["moved_now"] = v.signum.map(lambda s: int(c2.moved.get(s, 1) != 0 or c2.lost.get(s, 1) != 0))
    v["moved_runor"] = v.signum.isin(RUNOR).astype(int)
    v["reerected"] = v.signum.map(lambda s: int(bool(REERECT.search(kmr_t.get(s, "") + " " + rd.get(s, "")))))

    def perm_idx(x):
        out_ = np.arange(len(x))
        for _, gi in x.groupby("province").indices.items():
            out_[gi] = lrng.permutation(gi)
        return out_

    def test(x, by_parish=False):
        x = x.reset_index(drop=True)
        f, t = x.riktning.to_numpy(), x.vag.to_numpy()
        groups = x.parish.to_numpy() if by_parish else None

        def stat(ff):
            cs = np.cos(np.radians(ff - t))
            return pd.Series(cs).groupby(groups).mean().mean() if by_parish else cs.mean()
        obs = stat(f)
        sims = np.array([stat(f[perm_idx(x)]) for _ in range(NPERM)])
        return {"n": len(x), "medel_cos": float(obs), "vantat": float(sims.mean()),
                "p": float((1 + (sims >= obs).sum()) / (NPERM + 1)),
                "andel_inom_45": float((np.abs((f - t + 180) % 360 - 180) <= 45 + 1e-9).mean())}

    rungs = {"huvud": test(v), "halva_A": test(v[v.half == "A"]), "halva_B": test(v[v.half == "B"])}
    lopo = {}
    for pv in [p for p, n in v.province.value_counts().items() if n >= 10]:
        r = test(v[v.province != pv]); r["andel_kvar"] = r["n"] / len(v); lopo[pv] = r
    rungs["socken"] = test(v, by_parish=True)
    first = v[v.carver.notna()].sort_values("signum").drop_duplicates("carver")
    rungs["en_per_ristare"] = test(pd.concat([first, v[v.carver.isna()]]))
    rungs["utan_aterresta"] = test(v[v.reerected == 0])
    rungs["utan_flyttade_runor"] = test(v[v.moved_runor == 0])
    rungs["dagens_flyttregel"] = test(v[v.moved_now == 0])
    rungs["bara_text"] = test(v.assign(vag=v.vag_text)[v.vag_text.notna()])
    rungs["bara_registrerad"] = test(v.assign(vag=v.vag_reg)[v.vag_reg.notna()])
    for r in rungs.values():
        r["holds"] = bool(r["medel_cos"] > r["vantat"] and r["p"] < 0.05)
    lopo_ok = all(r["medel_cos"] > r["vantat"] and (r["andel_kvar"] < 2 / 3 or r["p"] < 0.05) for r in lopo.values())
    return {"rungs": rungs, "lopo": lopo, "lopo_holds": bool(lopo_ok),
            "all_hold": bool(all(r["holds"] for r in rungs.values()) and lopo_ok)}


# kontroll: med de lästa (låsta) riktningarna ger koden exakt trappan.json, också p-värdena
TR = json.load(open(os.path.join(OUT, "trappan.json"), encoding="utf-8"))
rep = ladder(d, "riktning", "vag", "vag_text")
for k, r in TR["rungs"].items():
    assert all(abs(rep["rungs"][k][a] - r[a]) < 1e-9 for a in ("n", "medel_cos", "vantat", "p")), k
for k, r in TR["lopo"].items():
    assert all(abs(rep["lopo"][k][a] - r[a]) < 1e-9 for a in ("n", "medel_cos", "p")), k
lad_r = ladder(d, "riktning_r", "vag_r", "vag_text_r")
lad_u = ladder(u, "riktning_r", "vag_r", "vag_text_r")

corr_insk = g[g.riktning_text.notna()]
corr_vag = g[g.vag_text_kalla.notna()]
out = {
    "syfte": "kontroll efter granskningen 2026-11-05; den låsta analysen är oförändrad",
    "enhet": "cg = gon (centesimalgrader, 400 per varv, 1 gon = 0,9 grader); grader och ° läses som grader",
    "rattade_ristningar": [{"signum": r.signum, "text": r.riktning_text, "last": r.riktning_las, "ratt": round(r.riktning, 1),
                            "fel_grader": round(float(ang_diff(r.riktning, r.riktning_las)), 1)} for r in corr_insk.itertuples()],
    "rattade_vagar": [{"signum": r.signum, "text": r.vag_text_kalla, "last": r.vag_text_las, "ratt": round(r.vag_text, 1),
                       "fel_grader": round(float(ang_diff(r.vag_text, r.vag_text_las)), 1)} for r in corr_vag.itertuples()],
    "dubbletter": {"stenar": dups, "n_stenar": int(d.signum.nunique()), "n_poster": int(len(d)),
                   "n_stenar_med_vag": int(d[d.vag_r.notna()].signum.nunique()), "n_poster_med_vag": int(d.vag_r.notna().sum())},
    "last": {"alla": describe(d, "riktning", "vag"), "bara_text": describe(d, "riktning", "vag_text")},
    "rattad": {"alla": perm_test(d, "riktning_r", "vag_r"), "bara_text": perm_test(d, "riktning_r", "vag_text_r"),
               "halva_A": perm_test(d[d.half == "A"], "riktning_r", "vag_r"),
               "halva_B": perm_test(d[d.half == "B"], "riktning_r", "vag_r"),
               "H1_rayleigh": rayleigh(d.riktning_r), "H3_gard": perm_test(d, "riktning_r", "gard")},
    "rattad_en_per_sten": {"alla": perm_test(u, "riktning_r", "vag_r"), "bara_text": perm_test(u, "riktning_r", "vag_text_r"),
                           "halva_A": perm_test(u[u.half == "A"], "riktning_r", "vag_r"),
                           "halva_B": perm_test(u[u.half == "B"], "riktning_r", "vag_r"),
                           "H1_rayleigh": rayleigh(u.riktning_r)},
}
out["trappan_last_reproducerad"] = True  # assert ovan: koden ger trappan.json exakt med de lästa riktningarna
out["trappan_rattad"] = lad_r
out["trappan_rattad_en_per_sten"] = lad_u
out["n_rattade_ristningar"], out["n_rattade_vagar"] = len(out["rattade_ristningar"]), len(out["rattade_vagar"])
out["n_rattade_vagar_bland_text"] = int(corr_vag.vag_text.notna().sum())


def mdate(p):
    return dt.datetime.fromtimestamp(os.path.getmtime(p)).strftime("%Y-%m-%d")


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


runor = json.load(open(os.path.join(ROOT, "data", "raa", "runor_2020.json"), encoding="utf-8"))
lam = os.path.join(ROOT, "data", "raa", "lamningar.csv")
vm = os.path.join(ROOT, "data", "raa", "lamningar_extra", "vägmärke.csv")
by = os.path.join(ROOT, "data", "raa", "lamningar_extra", "bytomt_gårdstomt.csv")
out["indata"] = {
    "kmr_runstenar": {"kalla": kmr["source"], "hamtad": kmr["fetched"], "skript": "scripts/fetch_kmr_runstenar.py", "sha256_16": sha16(KMR)},
    "lamningar_fardvagar": {"hamtad_filtid": mdate(lam), "skript": "scripts/fetch_raa_remains.py", "sha256_16": sha16(lam)},
    "lamningar_vagmarke": {"hamtad_filtid": mdate(vm), "skript": "scripts/fetch_raa_extra.sh", "sha256_16": sha16(vm)},
    "lamningar_bytomt": {"hamtad_filtid": mdate(by), "skript": "scripts/fetch_raa_extra.sh", "sha256_16": sha16(by)},
    "runor_2020": {"kalla": runor["source"], "hamtad": runor["fetched"], "skript": "scripts/fetch_runor.py"},
    "korpus": {"huvud": "3f58e9339191761e", "flyttregel_steget": "e83202e01a5e6d27", "huvud_skapad": mdate(CORPUS),
               "sha256_16_huvud": sha16(CORPUS),
               "sha256_16_flyttregel_steget": sha16(os.path.join(ROOT, "data", "cache", "r", "corpus", "e83202e01a5e6d27", "corpus.csv"))},
}
out["indata"]["korpus"]["identiska"] = out["indata"]["korpus"]["sha256_16_huvud"] == out["indata"]["korpus"]["sha256_16_flyttregel_steget"]
json.dump(out, open(os.path.join(OUT, "gon_kontroll.json"), "w"), ensure_ascii=False, indent=1, default=float)

print("rättade ristningar", out["n_rattade_ristningar"], [(x["signum"], x["fel_grader"]) for x in out["rattade_ristningar"]])
print("rättade vägar", out["n_rattade_vagar"], [(x["signum"], x["fel_grader"]) for x in out["rattade_vagar"]])
print("dubbletter", out["dubbletter"])
for k in ("last", "rattad", "rattad_en_per_sten"):
    for kk, r in out[k].items():
        print(f"{k:20s} {kk:12s}", {a: (round(b, 4) if isinstance(b, float) else b) for a, b in r.items()})
for k in ("trappan_rattad", "trappan_rattad_en_per_sten"):
    L = out[k]
    print(k, "ALLA HÅLLER" if L["all_hold"] else "NÅGOT STEG FALLER")
    for kk, r in {**L["rungs"], **{"utan " + p: r for p, r in L["lopo"].items()}}.items():
        print(f"   {kk:22s} n {r['n']:4d} cos {r['medel_cos']:.3f} mot {r['vantat']:.3f} inom45 {r['andel_inom_45']:.3f} p {r['p']:.4f}")
print(out["indata"])
