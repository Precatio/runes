"""Del A i analysplan_kallor.md: formar den som stavar lika sina runor lika? RuneS-DB:s graftyper (runformer position
för position) mot Vitkis stavningsavstånd på Skånes runstenar, Mantel och partiell Mantel mot det geografiska avståndet.
Underlag: data/raa/kallor/runes_records.json och runes_html/ (hämtade 2026-10-21 från runesdb.de, CC BY-SA 4.0).
Skriver utdata/kallor/skane_runformer.json.
    PYTHONPATH=. .venv/bin/python utdata/kallor/skane_runformer.py"""
import html
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
from api.rundata import store  # noqa: E402
from api.routers.orthography import model as orthography_model  # noqa: E402

KALLOR = os.path.join(ROOT, "data", "raa", "kallor")
PERMS, SEED = 10_000, 2026
MIN_POSITIONS, MIN_SHARED = 5, 3

recs = json.load(open(os.path.join(KALLOR, "runes_records.json"), encoding="utf-8"))
skane_ids = {fid for fid, _ in json.load(open(os.path.join(KALLOR, "runes_skane_rows.json"), encoding="utf-8"))}
by = {r["signum"]: r for r in store().inscriptions}
m = orthography_model()


def positions(fid: str) -> list[tuple[str, int]]:
    """(translittereringstecken, graftyp) för varje position i inskriften, ur postens Graphtypen-vy."""
    s = open(os.path.join(KALLOR, "runes_html", f"find_{fid}.html"), encoding="utf-8", errors="replace").read()
    i = s.find('id="pills-gts-inscription"')
    seg = s[i:s.find('id="pills-gts-attested"', i)] if i >= 0 else ""
    out = []
    for a in re.findall(r'<a [^>]*href="/find/\d+/inscription\?sign=\d+"[^>]*>(.*?)</a>', seg, re.S):
        gt = re.search(r'alt="Graphtyp (\d+)"', a)
        sign = re.search(r'title="Transliteration">\s*<b>(.*?)</b>', a, re.S)
        if gt and sign:
            out.append((html.unescape(re.sub(r"<[^>]+>", "", sign.group(1))).replace("‌", "").strip(), int(gt.group(1))))
    return out


# ---- the sample ------------------------------------------------------------------------------------------------
stones = []
for fid, r in recs.items():
    if fid not in skane_ids or not (r.get("runenreihe") or "").startswith("jüngeres") or not r.get("dr"):
        continue
    pos = positions(fid)
    if pos and r["dr"] in by and r["dr"] in m.index and by[r["dr"]].get("lat") is not None:
        stones.append({"id": fid, "signum": r["dr"], "sigle": r["sigla"][0], "place": by[r["dr"]]["place"], "positions": pos})
stones.sort(key=lambda x: x["signum"])
n = len(stones)
print("stenar i urvalet:", n)

# ---- variable signs and the rune-form distance --------------------------------------------------------------------
pool = Counter((s, g) for st in stones for s, g in st["positions"])
per_sign = defaultdict(Counter)
for (s, g), c in pool.items():
    per_sign[s][g] += c
variable = sorted(s for s, cnt in per_sign.items() if sum(c >= MIN_POSITIONS for c in cnt.values()) >= 2)
print("varierande tecken:", variable)
profile = []
for st in stones:
    cnt = defaultdict(Counter)
    for s, g in st["positions"]:
        cnt[s][g] += 1
    profile.append({s: {g: c / sum(cnt[s].values()) for g, c in cnt[s].items()} for s in cnt})
D_form = np.full((n, n), np.nan)
shared = np.zeros((n, n), dtype=int)
for i in range(n):
    for j in range(n):
        if i == j:
            D_form[i, j] = 0.0
            continue
        common = [s for s in variable if s in profile[i] and s in profile[j]]
        shared[i, j] = len(common)
        if len(common) >= MIN_SHARED:
            tv = []
            for s in common:
                gs = set(profile[i][s]) | set(profile[j][s])
                tv.append(0.5 * sum(abs(profile[i][s].get(g, 0) - profile[j][s].get(g, 0)) for g in gs))
            D_form[i, j] = float(np.mean(tv))

# ---- the spelling distance and the geographic distance ----------------------------------------------------------------
V = np.array([m.vectorize(m.feats[m.index[st["signum"]]]) for st in stones])
norm = np.linalg.norm(V, axis=1, keepdims=True)
cos = (V @ V.T) / (norm @ norm.T)
D_spell = 1 - cos
np.fill_diagonal(D_spell, 0.0)


def km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


xy = [(by[st["signum"]]["lat"], by[st["signum"]]["lon"]) for st in stones]
D_geo = np.array([[km(xy[i], xy[j]) for j in range(n)] for i in range(n)])
iu = np.triu_indices(n, 1)


def spearman(a, b):
    from scipy.stats import spearmanr
    return float(spearmanr(a, b).statistic)


def mantel(A, B, perms=PERMS, seed=SEED):
    """Spearman över de par som har värde i båda; permutationerna flyttar B:s rader och kolumner (och dess saknade
    värden) med stenarna. Ensidigt p för positiv korrelation."""
    rng = np.random.default_rng(seed)
    a, b = A[iu], B[iu]
    ok = ~np.isnan(a) & ~np.isnan(b)
    r = spearman(a[ok], b[ok])
    hits = 0
    for _ in range(perms):
        p = rng.permutation(n)
        bp = B[np.ix_(p, p)][iu]
        okp = ~np.isnan(a) & ~np.isnan(bp)
        if spearman(a[okp], bp[okp]) >= r:
            hits += 1
    return r, (hits + 1) / (perms + 1), int(ok.sum())


def residual(D, G):
    """D rensat från log-avståndet i km (linjär regression på de par som har värde); en avståndsmatris igen."""
    d, g = D[iu], np.log1p(G[iu])
    ok = ~np.isnan(d)
    beta = np.polyfit(g[ok], d[ok], 1)
    R = np.full_like(D, np.nan)
    R[iu] = d - np.polyval(beta, g)
    R = np.where(np.isnan(R), R.T, R)
    np.fill_diagonal(R, 0.0)
    return R


r_main, p_main, pairs = mantel(D_spell, D_form)
r_geo_form, p_geo_form, _ = mantel(D_geo, D_form)
r_geo_spell, p_geo_spell, _ = mantel(D_geo, D_spell)
r_part, p_part, pairs_part = mantel(residual(D_spell, D_geo), residual(D_form, D_geo))
out = {
    "plan_sha256": open(os.path.join(ROOT, "utdata", "kallor", "analysis_plan_kallor.sha256")).read().split()[0],
    "n_stones": n, "stones": [{k: v for k, v in st.items() if k != "positions"} | {"n_positions": len(st["positions"])} for st in stones],
    "n_positions": sum(len(st["positions"]) for st in stones),
    "signs": {s: {"n_positions": sum(cnt.values()), "n_graphtypes": len(cnt), "graphtypes": dict(cnt.most_common())}
              for s, cnt in sorted(per_sign.items(), key=lambda kv: -sum(kv[1].values()))},
    "variable_signs": variable, "min_positions": MIN_POSITIONS, "min_shared": MIN_SHARED,
    "pairs_with_value": pairs, "pairs_total": int(n * (n - 1) / 2),
    "mantel": {"r": r_main, "p": p_main, "perms": PERMS},
    "mantel_geo_form": {"r": r_geo_form, "p": p_geo_form}, "mantel_geo_spell": {"r": r_geo_spell, "p": p_geo_spell},
    "partial_mantel": {"r": r_part, "p": p_part, "pairs": pairs_part},
    "answer": bool(r_main > 0 and p_main < 0.05 and r_part > 0 and p_part < 0.05),
    "pairs": [[stones[i]["signum"], stones[j]["signum"], round(float(D_spell[i, j]), 4), None if np.isnan(D_form[i, j]) else round(float(D_form[i, j]), 4), round(float(D_geo[i, j]), 1)]
              for i, j in zip(*iu)],
}
json.dump(out, open(os.path.join(ROOT, "utdata", "kallor", "skane_runformer.json"), "w"), ensure_ascii=False, indent=1)
print(f"Mantel stavning~runform: r {r_main:.3f} p {p_main:.4f} ({pairs} par av {out['pairs_total']})")
print(f"geografi~runform r {r_geo_form:.3f} p {p_geo_form:.4f}; geografi~stavning r {r_geo_spell:.3f} p {p_geo_spell:.4f}")
print(f"partiell Mantel: r {r_part:.3f} p {p_part:.4f} | svar: {'ja' if out['answer'] else 'nej'}")
print("tecken med flest graftyper:", [(s, v["n_graphtypes"], v["n_positions"]) for s, v in list(out["signs"].items())[:12]])
