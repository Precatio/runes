"""Illustrationer till fyra publicerade forskningsrapporter (Viktor 2026-11-01: "lägg till i samtliga 4"; varje bild
säger att Vitki har gjort den). Bilderna visar måttet eller ett exempel; inga nya prov, och varje tal kontrolleras mot
rapportens egna resultatfiler. Exemplen väljs efter en regel som står i bildtexten, aldrig för hand.
    .venv/bin/python utdata/rapporter/figurer/rapportfigurer.py [vag] [seriation] [familj] [spar]
Skriver <namn>_sv.png och <namn>_en.png här och figurer.json med de tal som bildtexterna använder."""
import json
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import matplotlib.patches  # noqa: E402
from matplotlib.patches import FancyArrowPatch, Polygon, Arc  # noqa: E402

OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(OUT, "..", "..", ".."))
sys.path.insert(0, ROOT)
INK, MUTED, GRID, ACCENT, BLUE, LAND = "#1e293b", "#64748b", "#e2e8f0", "#b7410e", "#2a78d6", "#f4f1ea"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "text.color": INK, "axes.labelcolor": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.edgecolor": GRID})
RES = json.load(open(os.path.join(OUT, "figurer.json"))) if os.path.exists(os.path.join(OUT, "figurer.json")) else {}


def T(lang, sv, en):
    return sv if lang == "sv" else en


def save(fig, name, lang, credit):
    fig.text(0.01, 0.01, credit, ha="left", va="bottom", fontsize=7.5, color=MUTED, wrap=True)
    path = os.path.join(OUT, f"{name}_{lang}.png")
    fig.savefig(path, dpi=200, facecolor="white")
    plt.close(fig)
    return path


# ---- 1. Vägen: måttet och rosen ----------------------------------------------------------------------------------------
def vag():
    v = pd.read_csv(os.path.join(ROOT, "utdata", "riktning", "stenar.csv"))
    v = v[v.vag.notna()]
    assert len(v) == 123
    d = ((v.riktning - v.vag + 180) % 360) - 180
    within = float((d.abs() <= 45).mean())
    assert round(100 * within) == 50
    k = np.round(d / 22.5).astype(int) % 16          # sektor 0 = rakt mot vägen
    counts = np.bincount(k, minlength=16)
    RES["vag"] = {"n": int(len(v)), "within45": within, "toward": int(counts[0]), "away": int(counts[8]),
                  "expected": len(v) / 16}
    for lang in ("sv", "en"):
        fig = plt.figure(figsize=(10, 5.2))
        fig.suptitle(T(lang, "Måttet och vad det gav", "The measure and what it gave"), x=0.01, ha="left", fontsize=13,
                     fontweight="bold")
        # (a) the schematic, seen from above
        ax = fig.add_axes([0.02, 0.06, 0.44, 0.84])
        ax.set_aspect("equal"); ax.axis("off"); ax.set_xlim(-3.2, 3.2); ax.set_ylim(-2.2, 3.6)
        ax.add_patch(Polygon([[-3.2, -0.45], [3.2, -0.15], [3.2, 0.35], [-3.2, 0.05]], closed=True, color="#cbd5e1"))
        ax.text(2.6, 0.55, T(lang, "vägen", "the road"), color=MUTED, fontsize=10, ha="center")
        sx, sy = 0.0, 2.3
        face = math.radians(-35)                       # the inscription faces down-right
        road = math.radians(-90)                       # the road lies straight below
        w, h = 0.95, 0.26
        ux, uy = math.cos(face + math.pi / 2), math.sin(face + math.pi / 2)
        cx, cy = math.cos(face), math.sin(face)
        corners = [(sx + a * w / 2 * ux + b * h / 2 * cx, sy + a * w / 2 * uy + b * h / 2 * cy) for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        ax.add_patch(Polygon(corners, closed=True, color=ACCENT))
        ax.add_patch(FancyArrowPatch((sx + 0.2 * cx, sy + 0.2 * cy), (sx + 1.9 * cx, sy + 1.9 * cy), arrowstyle="-|>",
                                     mutation_scale=16, color=ACCENT, linewidth=2))
        ax.add_patch(FancyArrowPatch((sx, sy - 0.2), (sx, 0.25), arrowstyle="-|>", mutation_scale=14, color=INK,
                                     linewidth=1.4, linestyle=(0, (4, 3))))
        ax.add_patch(Arc((sx, sy), 1.5, 1.5, theta1=-90, theta2=-35, color=INK, linewidth=1))
        ax.text(sx + 0.42, sy - 0.98, "v", fontsize=12, style="italic")
        ax.text(sx + 1.75 * cx + 0.12, sy + 1.75 * cy + 0.05, T(lang, "ristningen\nvetter hit", "the inscription\nfaces here"),
                fontsize=9.5, color=ACCENT, va="center")
        ax.text(sx - 0.15, 1.1, T(lang, "riktningen\ntill vägen", "direction\nto the road"), fontsize=9.5, ha="right", va="center")
        ax.text(sx - 0.55, sy + 0.55, T(lang, "runstenen,\nsedd ovanifrån", "the runestone,\nseen from above"), fontsize=9,
                color=MUTED, ha="right", va="center")
        ax.text(-3.1, -0.9, T(lang, "Måttet är cosinus för vinkeln v:\n1 rakt mot vägen, 0 åt sidan, −1 bort från vägen.",
                              "The measure is the cosine of the angle v:\n1 straight at the road, 0 sideways, −1 away from the road."),
                fontsize=9.5, va="top")
        # (b) the rose
        ax = fig.add_axes([0.55, 0.07, 0.40, 0.70], projection="polar")
        ax.set_theta_zero_location("N"); ax.set_theta_direction(-1)
        th = np.radians(np.arange(16) * 22.5)
        ax.bar(th, counts, width=np.radians(22.5) * 0.88, color=ACCENT, edgecolor="white", linewidth=1)
        tt = np.linspace(0, 2 * np.pi, 200)
        ax.plot(tt, np.full_like(tt, len(v) / 16), color=INK, linestyle=(0, (3, 3)), linewidth=1)
        ax.set_xticks(np.radians([0, 90, 180, 270]))
        ax.set_xticklabels([T(lang, "mot vägen", "towards\nthe road"), T(lang, "åt sidan", "sideways"),
                            T(lang, "bort från vägen", "away from\nthe road"), T(lang, "åt sidan", "sideways")], fontsize=9, color=INK)
        ax.set_yticks([10, 20, 30]); ax.set_yticklabels(["10", "20", "30"], fontsize=7)
        ax.set_rlabel_position(112); ax.grid(color=GRID)
        fig.text(0.75, 0.9, T(lang, f"Hur {len(v)} ristningar vetter i förhållande till vägen\n(antal stenar per väderstreck; streckad: om det vore slumpvis)",
                              f"How {len(v)} inscriptions face relative to the road\n(stones per compass point; dashed: if it were random)"),
                 fontsize=9.5, ha="center", va="top")
        save(fig, "vag", lang, T(lang, "Illustration och diagram: Vitki, ur Riksantikvarieämbetets kulturmiljöregister och Rundata.",
                                 "Illustration and chart: Vitki, from the Swedish register of ancient monuments and Rundata."))


# ---- 2. Seriationen: varje sten ------------------------------------------------------------------------------------------
def seriation():
    FP = "e83202e01a5e6d27"
    D = os.path.join(ROOT, "data", "cache", "r", "corpus", FP)
    ch = json.load(open(os.path.join(D, "chronology.json"), encoding="utf-8"))
    s = pd.read_csv(os.path.join(D, "chronology_stones.csv"))
    c = pd.read_csv(os.path.join(D, "corpus.csv"), low_memory=False, usecols=["signum", "style"]).set_index("signum")
    s = s[s.dated_by_style].copy()
    s["style"] = s.signum.map(c["style"])
    order = [r["style"] for r in ch["per_style"]]
    assert order == ["RAK", "Fp", "Pr1", "Pr2", "Pr3", "Pr4", "Pr5"] and len(s) == ch["validation"].get("n", 501) == 501
    assert s["style"].value_counts().to_dict() == {r["style"]: r["n"] for r in ch["per_style"]}
    rho = ch["validation"]["rho"]
    assert f"{rho:.2f}" == "0.54"
    med = s.groupby("style").score.median()
    RES["seriation"] = {"n": int(len(s)), "rho": rho, "medians": {k: float(med[k]) for k in order}}
    rng = np.random.default_rng(2026)
    for lang in ("sv", "en"):
        fig, ax = plt.subplots(figsize=(8.5, 5.4))
        fig.subplots_adjust(left=0.1, right=0.98, top=0.82, bottom=0.18)
        for i, st in enumerate(order):
            y = s.score[s["style"] == st].to_numpy()
            ax.scatter(i + rng.uniform(-0.28, 0.28, len(y)), y, s=9, color=BLUE, alpha=0.45, linewidths=0)
            ax.plot([i - 0.34, i + 0.34], [med[st]] * 2, color=ACCENT, linewidth=3, solid_capstyle="butt")
        ax.set_xticks(range(len(order)))
        ax.set_xticklabels([f"{st}\n({(s['style'] == st).sum()})" for st in order])
        ax.set_xlabel(T(lang, "Stilgrupp efter ornamentiken (Gräslund), äldst till vänster; antal stenar inom parentes",
                        "Style group by the ornament (Gräslund), oldest on the left; number of stones in brackets"), fontsize=9)
        ax.set_ylabel(T(lang, "Plats i ordningen efter språk och innehåll\n(tidiga drag nederst)",
                        "Place in the order by language and content\n(early traits at the bottom)"), fontsize=9)
        ax.grid(axis="y", color=GRID); ax.set_axisbelow(True)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        fig.text(0.01, 0.95, T(lang, f"Upplands {len(s)} stildaterade runstenar, ordnade bara efter språk och innehåll",
                               f"Uppland's {len(s)} style-dated runestones, ordered by language and content alone"),
                 fontsize=12.5, fontweight="bold", va="top")
        fig.text(0.01, 0.885, T(lang, f"Varje punkt är en sten; det röda strecket är mittvärdet i stilgruppen. Ornamentiken ingick inte i ordningen. Rangkorrelation {rho:.2f}.".replace(".54", ",54"),
                               f"Each dot is a stone; the red bar is the middle value of the style group. The ornament was not part of the order. Rank correlation {rho:.2f}."),
                 fontsize=9, color=MUTED, va="top")
        save(fig, "seriation", lang, T(lang, "Diagram: Vitki, ur Rundata; stilgrupperna efter Gräslund (2006).",
                                       "Chart: Vitki, from Rundata; the style groups after Gräslund (2006)."))


# ---- 3. Familjegrupperna: en verklig grupp vid gravfält -----------------------------------------------------------------
def familj():
    from collections import Counter
    from pyproj import Transformer
    from src import entities
    D = os.path.join(ROOT, "data", "cache", "r", "corpus", "3f58e9339191761e")   # samma korpus som rapporten
    c = pd.read_csv(os.path.join(D, "corpus.csv"), low_memory=False)
    recs = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json")))["inscriptions"]}
    names, shown = {}, {}
    for sg in c.signum:
        ps = [p for p in entities.extract(recs[sg])["persons"] if p["role"] in ("resare", "minnes")]
        names[sg] = {p["key"] for p in ps}
        shown.update({p["key"]: p["name"] for p in ps})
    common = {k for k, _ in Counter(k for v in names.values() for k in v).most_common(20)}   # som i grannstudien
    st = c[c.province.isin(["U", "Sö"]) & (c.moved == 0) & (c.lost == 0) & c.lat.notna()].reset_index(drop=True)
    tr = Transformer.from_crs("EPSG:4326", "EPSG:3006", always_xy=True)
    st["x"], st["y"] = tr.transform(st.lon.to_numpy(dtype=float), st.lat.to_numpy(dtype=float))
    xy = st[["x", "y"]].to_numpy()
    pairs = []
    for i in range(len(st)):
        dd = np.hypot(*(xy[i + 1:] - xy[i]).T)
        for j in np.nonzero((dd > 25) & (dd <= 500))[0] + i + 1:   # nära par som i grannstudien: 25–500 m
            if st.province[i] != st.province[j]:
                continue
            sh = (names[st.signum[i]] & names[st.signum[j]]) - common
            if sh:
                pairs.append((i, j, sorted(sh)))
    # the groups: stones linked by such pairs; the one with most pairs (then most stones) is shown
    parent = list(range(len(st)))
    def root(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    for i, j, _ in pairs:
        parent[root(i)] = root(j)
    groups = Counter(root(i) for i, _, _ in pairs)
    size = lambda g: len({k for i, j, _ in pairs if root(i) == g for k in (i, j)})  # noqa: E731
    first = lambda g: min(st.signum[k] for i, j, _ in pairs if root(i) == g for k in (i, j))  # noqa: E731
    best = sorted(groups, key=lambda g: (-groups[g], -size(g), first(g)))[0]   # flest par, sedan flest stenar
    RES.setdefault("familj", {})
    ties = sum(1 for g in groups if (groups[g], size(g)) == (groups[best], size(best)))
    gp = [(i, j, sh) for i, j, sh in pairs if root(i) == best]
    members = sorted({k for i, j, _ in gp for k in (i, j)})
    x0, x1 = xy[members, 0].min() - 700, xy[members, 0].max() + 700
    y0, y1 = xy[members, 1].min() - 700, xy[members, 1].max() + 700
    side = max(x1 - x0, y1 - y0); cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    x0, x1, y0, y1 = cx - side / 2, cx + side / 2, cy - side / 2, cy + side / 2
    rem = pd.read_csv(os.path.join(ROOT, "data", "raa", "lamningar.csv"), low_memory=False)
    gf = rem[(rem.type == "gravfält") & rem.lat.notna()]
    gx, gy = tr.transform(gf.lon.to_numpy(dtype=float), gf.lat.to_numpy(dtype=float))
    ing = (gx > x0) & (gx < x1) & (gy > y0) & (gy < y1)
    ins = (st.x > x0) & (st.x < x1) & (st.y > y0) & (st.y < y1)
    parishes = Counter(st.parish[members]).most_common(2)
    RES["familj"] = {"n_pairs_total": len(pairs), "group_pairs": len(gp), "group_stones": len(members),
                     "stones": [st.signum[k] for k in members], "names": sorted({shown[n] for _, _, sh in gp for n in sh}),
                     "parishes": [p for p, _ in parishes], "n_gravfalt_in_window": int(ing.sum()),
                     "n_stones_in_window": int(ins.sum()), "side_m": round(side), "ties": ties,
                     "pairs": [[st.signum[i], st.signum[j], [shown[n] for n in sh], round(float(np.hypot(*(xy[i] - xy[j]))))] for i, j, sh in gp]}
    for lang in ("sv", "en"):
        fig, ax = plt.subplots(figsize=(7.6, 8.2))
        fig.subplots_adjust(left=0.02, right=0.98, top=0.86, bottom=0.12)
        ax.set_facecolor(LAND)
        ax.scatter(gx[ing], gy[ing], s=900, marker="o", color="#94a3b8", alpha=0.35, linewidths=0,
                   label=T(lang, "registrerat gravfält", "registered grave field"))
        for i, j, sh in gp:
            ax.plot([xy[i, 0], xy[j, 0]], [xy[i, 1], xy[j, 1]], color=INK, linewidth=1.3, zorder=2)
            ax.text((xy[i, 0] + xy[j, 0]) / 2, (xy[i, 1] + xy[j, 1]) / 2, ", ".join(shown[n] for n in sh), fontsize=7.5,
                    ha="center", va="center", color=INK, zorder=4,
                    bbox={"boxstyle": "round,pad=0.15", "facecolor": "white", "edgecolor": "none", "alpha": 0.85})
        other = [k for k in np.nonzero(ins.to_numpy())[0] if k not in members]
        ax.scatter(xy[other, 0], xy[other, 1], s=34, color="white", edgecolors=ACCENT, linewidths=1.2, zorder=3,
                   label=T(lang, "annan runsten som står kvar", "other runestone still in place"))
        ax.scatter(xy[members, 0], xy[members, 1], s=60, color=ACCENT, edgecolors="white", linewidths=0.8, zorder=3,
                   label=T(lang, "runsten i gruppen", "runestone in the group"))
        for k in members:
            ax.annotate(st.signum[k], (xy[k, 0], xy[k, 1]), xytext=(5, 5), textcoords="offset points", fontsize=8.5,
                        color=ACCENT, fontweight="bold", zorder=5)
        ax.plot([x0 + 0.05 * side, x0 + 0.05 * side + 500], [y0 + 0.05 * side] * 2, color=INK, linewidth=2)
        ax.text(x0 + 0.05 * side + 250, y0 + 0.05 * side + 0.015 * side, "500 m", ha="center", fontsize=8.5)
        ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
        ax.plot([], [], color=INK, linewidth=1.3, label=T(lang, "stenarna delar ett personnamn (namnet står på strecket)",
                                                           "the stones share a personal name (the name is on the line)"))
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.01), ncol=2, fontsize=8, frameon=False)
        place = " och ".join(p.replace(" sn", "") for p, _ in parishes) if lang == "sv" else " and ".join(p.replace(" sn", "") for p, _ in parishes)
        fig.text(0.02, 0.965, T(lang, f"En familjegrupp: {place}", f"A family group: {place}"), fontsize=13, fontweight="bold", va="top")
        fig.text(0.02, 0.925, T(lang, "Den grupp i Uppland och Södermanland med flest stenpar 25–500 meter från varandra som delar ett personnamn\n(de 20 vanligaste namnen räknas inte).",
                                "The group in Uppland and Södermanland with the most pairs of stones 25–500 metres apart\nthat share a personal name (the 20 most common names are not counted)."),
                 fontsize=9, color=MUTED, va="top")
        save(fig, "familj", lang, T(lang, "Karta: Vitki, ur Rundata och Riksantikvarieämbetets kulturmiljöregister (gravfälten som punkter).",
                                    "Map: Vitki, from Rundata and the Swedish register of ancient monuments (grave fields as points)."))


# ---- 4. Spårläsaren: vad skannern såg i två provord ---------------------------------------------------------------------
def spar():
    import glob
    SD = os.path.join(ROOT, "utdata", "sparlasare")
    sys.path.insert(0, SD)
    import led_e
    from led_a import BASE, FUT
    from led_f import gold, locate, scan_sets
    from src.runlm import load_rundata, viking
    rows = []
    for p in sorted(glob.glob(os.path.join(SD, "led_f_*.json"))):
        d = json.load(open(p))
        if isinstance(d, dict) and "rows" in d:
            rows += [x for x in d["rows"] if all(x.get(c) for c in ("utan", "skanner", "omflyttad"))]
    assert len(rows) == 157 and len({x["sig"] for x in rows}) == 17      # samma 157 ord som rapporten
    gain = max((x for x in rows if x["skanner"]["word_ok"] and not x["utan"]["word_ok"]),
               key=lambda x: x["skanner"]["p_truth"] - x["utan"]["p_truth"])
    n_up = sum(x["skanner"]["word_ok"] and not x["utan"]["word_ok"] for x in rows)
    n_down = sum(x["utan"]["word_ok"] and not x["skanner"]["word_ok"] for x in rows)
    assert (n_up, n_down) == (10, 0)    # spåren gjorde tio fel ord rätt och inget rätt ord fel
    loss = min(rows, key=lambda x: x["skanner"]["p_truth"] - x["utan"]["p_truth"])   # där sannolikheten sjönk mest
    by = {r["signum"]: r for r in load_rundata() if viking(r)}
    ORDER = "fuþorkhniastbmlR"                   # den yngre runraden, som spåren läses i
    assert set(ORDER) == set(FUT) and len(ORDER) == 16

    def positions(row):
        """Per runa i det dolda ordet: vilka av de 16 runorna spårmängden tillåter (samma mängder som provet, led_f.scan_sets)."""
        r = by[row["sig"]]
        groups, gw = gold(r)
        full = "".join(groups)
        span = next((i, j) for i, j, _, w in gw
                    if w == row["word"] and (lambda L: L and groups[L[0]][L[1]:L[2]] == row["truth"])(locate(groups, i, j)))
        sets, _ = scan_sets(row["sig"], full)
        out = []
        for pos in range(*span):
            S = sets.get(pos)
            allowed = None if S is None else {BASE.get(c, c) for c in S} & set(ORDER)
            out.append({"truth": BASE.get(full[pos], full[pos]), "allowed": allowed})
        return out

    ex = [("gain", gain, positions(gain)), ("loss", loss, positions(loss))]
    RES["spar"] = {k: {"sig": x["sig"], "truth": x["truth"], "word": x["word"], "utan": x["utan"]["top"],
                       "skanner": x["skanner"]["top"], "p_utan": x["utan"]["p_truth"], "p_skanner": x["skanner"]["p_truth"],
                       "allowed": [None if p["allowed"] is None else len(p["allowed"]) for p in ps],
                       "truth_allowed": [None if p["allowed"] is None else p["truth"] in p["allowed"] for p in ps]}
                   for k, x, ps in ex}
    for lang in ("sv", "en"):
        fig = plt.figure(figsize=(10, 4.2))
        fig.text(0.01, 0.97, T(lang, "Vad spåren säger om ett dolt ord: två exempel", "What the traces say about a hidden word: two examples"),
                 fontsize=13, fontweight="bold", va="top")
        fig.text(0.01, 0.89, T(lang, "För varje runa i det dolda ordet visar rutan vilka av runradens 16 runor skanningen tillåter (mörka) och vilka den utesluter (ljusa).\nRätt runa har en ring. Av de 157 provorden: det där spåren hjälpte mest, och det där de sänkte sannolikheten för rätt svar mest.",
                                "For each rune of the hidden word the box shows which of the 16 runes of the futhark the scan allows (dark) and which it rules out (light).\nThe right rune is circled. Of the 157 test words: the one where the traces helped most, and the one where they lowered the probability of the right answer most."),
                 fontsize=8.6, color=MUTED, va="top")
        for col, (kind, x, ps) in enumerate(ex):
            x0 = 0.03 + col * 0.5
            for k, p in enumerate(ps):
                ax = fig.add_axes([x0 + k * 0.088, 0.42, 0.08, 0.38])
                ax.set_xlim(0, 4); ax.set_ylim(0, 4.9); ax.axis("off"); ax.set_aspect("equal", adjustable="box", anchor="S")
                ax.add_patch(matplotlib.patches.Rectangle((0, 0), 4, 4, facecolor="#f8fafc", edgecolor=GRID))
                for n_, ch in enumerate(ORDER):
                    cx, cy = n_ % 4 + 0.5, 3.5 - n_ // 4
                    on = p["allowed"] is None or ch in p["allowed"]
                    ax.text(cx, cy, ch, ha="center", va="center", fontsize=10, color=INK if on else "#cbd5e1",
                            fontweight="bold" if on else "normal")
                    if ch == p["truth"]:
                        ax.add_patch(matplotlib.patches.Circle((cx, cy), 0.42, fill=False, edgecolor=ACCENT, linewidth=1.8))
                n_ok = 16 if p["allowed"] is None else len(p["allowed"])
                ax.text(2, 4.45, T(lang, f"{n_ok} av 16", f"{n_ok} of 16"), ha="center", fontsize=8, color=MUTED)
            ok = lambda b: T(lang, "rätt", "right") if b else T(lang, "fel", "wrong")  # noqa: E731
            pc_ = lambda v: f"{round(100 * v)} %"  # noqa: E731
            head = T(lang, "Spåren hjälpte mest", "The traces helped most") if kind == "gain" else T(lang, "Spåren sänkte mest", "The traces lowered most")
            txt = (f"{head} – {x['sig']}\n"
                   + T(lang, f"Dolt: {x['truth']} (ordet {x['word']})\n", f"Hidden: {x['truth']} (the word {x['word']})\n")
                   + T(lang, f"Utan spåren: {x['utan']['top']} – {ok(x['utan']['word_ok'])} (rätt svar {pc_(x['utan']['p_truth'])})\n",
                       f"Without the traces: {x['utan']['top']} – {ok(x['utan']['word_ok'])} (right answer {pc_(x['utan']['p_truth'])})\n")
                   + T(lang, f"Med spåren: {x['skanner']['top']} – {ok(x['skanner']['word_ok'])} (rätt svar {pc_(x['skanner']['p_truth'])})",
                       f"With the traces: {x['skanner']['top']} – {ok(x['skanner']['word_ok'])} (right answer {pc_(x['skanner']['p_truth'])})"))
            fig.text(x0 + 0.005, 0.38, txt, fontsize=9.8, va="top", linespacing=1.6)
        save(fig, "spar", lang, T(lang, "Illustration: Vitki, ur Laila Kitzler Åhfeldts 3D-skanningar (Riksantikvarieämbetet, projektet Runristandets dynamik; Zenodo, doi:10.5281/zenodo.11951255, CC BY 4.0) och Rundata.",
                                  "Illustration: Vitki, from Laila Kitzler Åhfeldt's 3D scans (Swedish National Heritage Board, project Runristandets dynamik; Zenodo, doi:10.5281/zenodo.11951255, CC BY 4.0) and Rundata."))


if __name__ == "__main__":
    want = set(sys.argv[1:]) or {"vag", "seriation", "familj", "spar"}
    for name, fn in (("vag", vag), ("seriation", seriation), ("familj", familj), ("spar", spar)):
        if name in want:
            fn()
    json.dump(RES, open(os.path.join(OUT, "figurer.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(RES, ensure_ascii=False)[:600])
