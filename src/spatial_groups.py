"""Grupper som enhet i rumsliga närhetsprov (METHODS.md, rumslig statistik; lärdomen från gravhögarna 2026-11-18).

Ett prov av formen "står stenen nära X?" räknar varje sten för sig. Men runstenar står ofta i grupper – två, fem, tio
stenar vid samma gravfält eller gård – och stenarna i en grupp delar samma X och liknar varandra i det mesta annat
(samma familj, ofta samma ristare och tid). Då är femtio stenar inte femtio oberoende iakttagelser, och p-värdet blir
för litet. 2026-11-18 föll "runstenar står oftare vid stora gravhögar" när högarna i grupper räknades som en enhet:
47 stora högar var bara 21 grupper.

Grupperna: stenar (eller andra punkter) som ligger närmare varandra än länkavståndet hör till samma grupp, med enkel
länkning – A och B är i samma grupp om det finns en kedja av punkter mellan dem där varje steg är kortare än
länkavståndet. Länkavståndet är 2 × provets radie, som i utdata/hogar/grupper.py: två stenar inom radien från samma
plats X ligger högst 2 × radien från varandra och hamnar alltid i samma grupp. Men enkel länkning kedjar ihop täta
trakter: bland de 1 097 runstenarna på ursprunglig plats i Sverige ger 4 km (radien 2 km) en enda grupp på 424 stenar
genom halva Uppland, och 10 km en på 674. Länkavståndet stannar därför vid 2 km, och stenar som har samma närmaste
plats X inom radien länkas uttryckligen – så att det som 2 × radien skulle garantera, att stenar som delar samma X
räknas som en grupp, gäller också för större radier (största gruppen 38–98 stenar i stället för 424–674). För
radier upp till 1 km är regeln exakt 2 × radien. För mönster utan radie och utan plats (hot spots) används 1 km, den
skala där stenarna i en grupp står vid samma gravfält eller gård (Familjens plats, 2026-10-29).

Provet: Mantel–Haenszel som förut (samma oddskvot, sten för sten, med landskapet konstant), men variansen räknas med
grupperna som de oberoende enheterna. CMH-provets täljare är en summa över stenarna, U = Σ (x − x̄)(y − ȳ) inom varje
landskap. Är stenarna oberoende räcker den vanliga (hypergeometriska) variansen; är de det inte summeras bidragen per
grupp först (en klusterrobust "sandwich"-varians, G/(G − 1) Σ_g (Σ_{i∈g} u_i)²). Kvoten mellan den variansen och samma
skattning med varje sten som sin egen grupp är designeffekten (DE): hur många gånger större osäkerheten är när man
tar hänsyn till grupperna. χ² delas med DE (Rao–Scotts korrektion; Donald & Donner 1987 för just Mantel–Haenszel med
klustrade data), och p läses mot F(1, G − 1) i stället för χ²(1), så att få grupper ger ett försiktigare prov.
DE sätts aldrig under 1: grupperna kan bara göra provet försiktigare, aldrig djärvare. Med varje sten i en egen grupp
blir svaret detsamma som det vanliga provet. Oddskvotens intervall vidgas med √DE. Frihetsgraderna är antalet grupper
på den mindre sidan (med stenar nära, eller utan) minus ett: det är de grupperna som bär jämförelsen.

Varför inte hela grupper som enheter (gruppen "nära" om någon sten är nära, "med mönstret" om någon har det)? Då byts
frågan: stora grupper får oftare både en sten nära och en sten med mönstret, så gruppens storlek blir en ny störfaktor
(grupper.py fick skikta efter storleksklass). Med den klusterrobusta variansen står frågan kvar – samma oddskvot som
förut – och det enda som ändras är hur säker den är. Skillnaden mellan sten- och gruppnivå beror då bara på att
stenarna inte är oberoende. Blandmodellen (gruppen som slumpeffekt) ger en annan sorts oddskvot (inom gruppen), går
inte att räkna utan R och konvergerar dåligt när de flesta grupper är en enda sten; den lämnas åt robusthetstrappan,
som redan har socknen som slumpeffekt.
"""
from __future__ import annotations

import math
from collections import defaultdict

LINK_FACTOR = 2.0   # länkavståndet = 2 × provets radie …
CAP_KM = 2.0        # … men högst 2 km; över det länkas stenar med samma närmaste plats inom radien
LOCAL_KM = 0.5      # radien för mönster utan egen radie: stenar inom 1 km länkas
MIN_GROUPS = 5      # minst så många grupper med stenar nära, och utan, för att gruppnivån ska kunna prövas
ALPHA = 0.05


def link_km(radius_km: float | None) -> float:
    """Länkavståndet för ett prov med radien radius_km (None: den lokala skalan, 1 km)."""
    return min(CAP_KM, LINK_FACTOR * (LOCAL_KM if radius_km is None else float(radius_km)))


def link(xy, link_m: float, shared=None) -> list[int]:
    """Gruppnummer (0, 1, …) för punkter i meter (n × 2), enkel länkning vid link_m som i grupper.py. shared: för
    varje punkt en nyckel (närmaste plats inom radien) eller None; punkter med samma nyckel länkas också."""
    import numpy as np
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    from scipy.spatial import cKDTree
    xy = np.asarray(xy, dtype=float).reshape(-1, 2)
    n = len(xy)
    if n == 0:
        return []
    pairs = cKDTree(xy).query_pairs(link_m, output_type="ndarray")
    rows, cols = [int(v) for v in pairs[:, 0]], [int(v) for v in pairs[:, 1]]
    first: dict = {}
    for i, key in enumerate(shared or []):
        if key is None:
            continue
        if key in first:
            rows.append(first[key])
            cols.append(i)
        else:
            first[key] = i
    g = coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n))
    _, lab = connected_components(g, directed=False)
    # numbered in order of first appearance, so that the labels do not depend on scipy's numbering
    seen: dict[int, int] = {}
    return [seen.setdefault(int(v), len(seen)) for v in lab]


def groups_latlon(lats, lons, radius_km: float | None = None, kind: str | None = None) -> list[int]:
    """Gruppnummer för punkter i lat/lon (WGS 84), länkade i SWEREF 99 TM vid link_km(radius_km); med kind (en sorts
    plats i src/places.py) länkas också punkter vars närmaste plats av sorten är densamma och ligger inom radien.
    Punkter utan läge får var sin grupp."""
    from src import places
    idx = [i for i, (a, b) in enumerate(zip(lats, lons)) if a is not None and b is not None]
    out = [-1] * len(lats)
    if idx:
        la, lo = [lats[i] for i in idx], [lons[i] for i in idx]
        shared = None
        if kind and radius_km is not None:
            d, near = places.nearest(kind, la, lo)
            shared = [p if (km is not None and km < radius_km) else None for km, p in zip(d, near)]
        lab = link(places._xy(la, lo), link_km(radius_km) * 1000, shared)
        for i, v in zip(idx, lab):
            out[i] = v
    nxt = max(out) + 1 if out else 0
    for i, v in enumerate(out):
        if v < 0:
            out[i], nxt = nxt, nxt + 1
    return out


def cluster_cmh(items) -> dict:
    """Mantel–Haenszel sten för sten och med grupperna som enheter. items: (skikt, x 0/1, y 0/1, grupp).

    Svaret: oddskvoten (Mantel–Haenszel), p sten för sten (CMH med kontinuitetskorrektion), designeffekten, p med
    grupperna som enheter, antalet grupper (alla, med någon sten där x = 1, med någon där x = 0) och det effektiva
    antalet stenar (stenarna / DE). p_group läses mot F(1, df), df = grupperna på den mindre sidan − 1, och är None
    när grupperna är för få (MIN_GROUPS på var sida)."""
    from scipy.stats import chi2, f as fdist
    cells: dict = defaultdict(lambda: [0, 0, 0, 0])
    for s, x, y, _ in items:
        cells[s][(1 - x) * 2 + (1 - y)] += 1
    # strata with both groups and both values: the others say nothing about the association (as the CMH test)
    used = {s for s, (a, b, c, d) in cells.items() if a + b and c + d and a + c and b + d and a + b + c + d >= 2}
    sr = ss = spr = sps_qr = sqs = va = 0.0
    xbar, ybar = {}, {}
    for s in used:
        a, b, c, d = cells[s]
        n = a + b + c + d
        sr += a * d / n
        ss += b * c / n
        p_, q_ = (a + d) / n, (b + c) / n
        spr += p_ * a * d / n
        sps_qr += p_ * b * c / n + q_ * a * d / n
        sqs += q_ * b * c / n
        m1, m0, k1 = a + b, c + d, a + c
        va += m1 * m0 * k1 * (n - k1) / (n * n * (n - 1))
        xbar[s], ybar[s] = m1 / n, k1 / n
    inf = [(s, x, y, g) for s, x, y, g in items if s in used]
    g_all = {g for *_, g in inf}
    g_near = {g for _, x, _, g in inf if x == 1}
    g_far = {g for _, x, _, g in inf if x == 0}
    out = {"n": len(inf), "groups": len(g_all), "groups_near": len(g_near), "groups_far": len(g_far),
           "strata": len(used), "or": None, "ci": None, "p_stone": None, "design_effect": None, "p_group": None,
           "ci_group": None, "effective_n": None, "df": None, "direction": 0}
    if not used or va <= 0:
        return out
    u_by_g: dict = defaultdict(float)
    s1 = 0.0
    U = 0.0
    for s, x, y, g in inf:
        u = (x - xbar[s]) * (y - ybar[s])
        U += u
        s1 += u * u
        u_by_g[g] += u
    n_, G = len(inf), len(g_all)
    chi_stone = max(0.0, abs(U) - 0.5) ** 2 / va
    out["p_stone"] = float(chi2.sf(chi_stone, 1))
    out["direction"] = 1 if U > 1e-12 else (-1 if U < -1e-12 else 0)
    se = None
    if sr > 0 and ss > 0:
        out["or"] = sr / ss
        se = math.sqrt(spr / (2 * sr * sr) + sps_qr / (2 * sr * ss) + sqs / (2 * ss * ss))
        out["ci"] = [out["or"] * math.exp(-1.96 * se), out["or"] * math.exp(1.96 * se)]
    v1 = n_ / (n_ - 1) * s1 if n_ > 1 else 0.0
    vg = G / (G - 1) * sum(v * v for v in u_by_g.values()) if G > 1 else 0.0
    de = max(1.0, vg / v1) if v1 > 0 else 1.0
    out["design_effect"] = de
    out["effective_n"] = n_ / de
    if len(g_near) >= MIN_GROUPS and len(g_far) >= MIN_GROUPS and G > 2:
        out["df"] = min(len(g_near), len(g_far)) - 1
        out["p_group"] = float(fdist.sf(chi_stone / de, 1, out["df"]))
        if se is not None:
            w = 1.96 * se * math.sqrt(de)
            out["ci_group"] = [out["or"] * math.exp(-w), out["or"] * math.exp(w)]
    return out


def verdict(res: dict, alpha: float = ALPHA) -> str:
    """'båda' (håller sten för sten och i grupper), 'bara stenar' (håller sten för sten men inte i grupper),
    'ingen' (håller inte sten för sten), 'för få grupper' eller 'saknas'."""
    if res.get("p_stone") is None:
        return "saknas"
    if res["p_stone"] >= alpha:
        return "ingen"
    if res.get("p_group") is None:
        return "för få grupper"
    return "båda" if res["p_group"] < alpha else "bara stenar"
