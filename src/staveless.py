"""Stavlöst läge i den automatiska spåranalysen (2026-10-26).

Stavlösa runor (hälsingerunor, och r/u på en del medelpadska stenar) har ingen huvudstav: en runa är ett eller några
korta streck, ofta bara halva slinghöjden, som står fritt i slingan. Den vanliga runindelningen bygger runor av streck
som sitter ihop (src/auto_grooves.classify_strokes) och kräver minst 12 mm långa streck, så på stavlösa stenar fick
nästan inga snitt någon runa: studie 0b fann median 20 % av textens runor (utdata/forskningsplan/s0_stavlosa_filter.txt).

Här delas runorna i stället efter var strecken står längs slingan:
  1. Varje slinga får en koordinat längs sig själv: avståndet i mm längs slingans mittlinje (skelett) från dess ena
     ände, och varje cell i slingan får värdet från närmaste punkt på mittlinjen – så att koordinaten inte ändras tvärs
     över slingan. Ritade slingor behåller var sitt nummer (rune_bands.drawn_labels), så att slingor som ritats sida
     vid sida inte flyter ihop där de möts; modellens slingor delas i sammanhängande fält. Slingans riktning i en punkt
     är riktningen där koordinaten ökar, och slinghöjden räknas för varje slinga för sig.
  2. Ett runstreck är en gren av spårets mittlinje som till minst hälften ligger i slingan, inte går längs den (mer än
     ALONG_DEG från slingans riktning, om den är längre än en fjärdedel av slinghöjden) och är högst 1,5 slinghöjder
     långt (så att långkvistrunornas stavar på blandade stenar också kommer med). Det täcker ett intervall av
     koordinaten.
  3. Intervallen ordnas längs slingan. Ett streck hör till föregående runa om luckan dit är högst GAP_BANDS
     slinghöjder och runan då blir högst MAX_WIDTH_BANDS slinghöjder bred längs slingan (taket hindrar att tätt
     ristade runor kedjas ihop). Två förhandsbestämda regler för gränsen – den största relativa luckan i stenens egna
     avstånd, och runornas takt ur autokorrelationen – var instabila; de fasta värdena valdes efter provet
     (METHODS.md 2c, utdata/stavlosa/). Indelningen är ett ungefärligt förslag; den exakta görs med Markera runorna.

Utan slingor finns ingen koordinat längs slingan; då används streckklassningen med kortare minsta längd
(STAVELESS_MIN_MM) och ett större grannavstånd (se auto_grooves.classify_strokes)."""
from __future__ import annotations

import math

import numpy as np
from scipy import ndimage

ALONG_DEG = 25.0         # a stroke within this angle of the band's direction runs along it (a band edge)
STAVELESS_MIN_MM = 5.0   # the shortest rune stroke without bands (12 mm in the ordinary classification)
COORD_CELL_MM = 2.0      # the along-band coordinate is computed on a grid this coarse, then spread back
MIN_BAND_MM2 = 400.0     # a band piece smaller than this (20 × 20 mm) gets no coordinate
GAP_BANDS = 0.15         # the limit between two runes along the band, in band heights
MAX_WIDTH_BANDS = 0.45   # a rune is at most this wide along the band (so that close-set runes do not chain)
MAX_ALONG_BANDS = 0.4    # a stroke that reaches further than this along the band is not a rune stroke


def band_coordinate(mask: np.ndarray, res: float, pieces: np.ndarray | None = None) -> dict:
    """Per cell: which band piece it belongs to (0 = none), its distance in mm along that piece from one end (measured
    along the piece's centre line and taken from the nearest point on it), the direction along the piece (unit vector
    (row, col) where the coordinate grows), and per piece its height in mm. pieces: the drawn bands' own numbers
    (rune_bands.drawn_labels); without them the mask's connected parts are the pieces. Computed on a coarser grid
    (COORD_CELL_MM) and spread back to the cells."""
    from skimage.graph import MCP_Geometric
    from skimage.morphology import skeletonize
    k = max(1, int(round(COORD_CELL_MM / res)))
    H, W = mask.shape
    hc, wc = -(-H // k), -(-W // k)
    pad = np.zeros((hc * k, wc * k), bool)
    pad[:H, :W] = mask
    small = pad.reshape(hc, k, wc, k).mean(axis=(1, 3)) >= 0.5
    if pieces is not None:
        padl = np.zeros((hc * k, wc * k), np.int32)
        padl[:H, :W] = pieces
        given = padl[k // 2::k, k // 2::k][:hc, :wc] * small
    else:
        given = small.astype(np.int32)
    lab = np.zeros(small.shape, np.int32)
    n = 0
    for v in np.unique(given[given > 0]):  # each drawn band (or the whole mask) in its connected parts
        part, m = ndimage.label(given == v, structure=np.ones((3, 3)))
        lab[part > 0] = part[part > 0] + n
        n += m
    s_small = np.full(small.shape, np.nan, np.float32)
    cell = k * res
    height = {}
    for c in range(1, n + 1):
        sub = lab == c
        if sub.sum() * cell * cell < MIN_BAND_MM2:
            lab[sub] = 0
            continue
        sk = skeletonize(sub)
        if sk.sum() < 2:
            sk = sub
        cost = np.where(sk, 1.0, np.inf)
        start = tuple(np.argwhere(sk)[0])
        d0, _ = MCP_Geometric(cost).find_costs([start])
        d0 = np.where(sk & np.isfinite(d0), d0, -1)
        end = tuple(np.unravel_index(int(np.argmax(d0)), d0.shape))  # the far end from an arbitrary point
        d1, _ = MCP_Geometric(cost).find_costs([end])
        d1 = np.where(sk & np.isfinite(d1), d1, np.nan)
        # every cell of the piece takes the coordinate of the nearest centre-line point
        _, (iy, ix) = ndimage.distance_transform_edt(~(sk & np.isfinite(d1)), return_indices=True)
        s_small[sub] = (d1[iy[sub], ix[sub]] * cell).astype(np.float32)
        dist = ndimage.distance_transform_edt(np.pad(sub, 1))[1:-1, 1:-1][sub] * cell
        height[c] = float(2.0 * np.percentile(dist, 90))
    # the direction along the band: where the coordinate grows (smoothed over a few cells)
    filled = np.where(np.isfinite(s_small), s_small, 0.0)
    w = np.isfinite(s_small).astype(np.float32)
    sm = ndimage.gaussian_filter(filled, 1.5) / np.maximum(ndimage.gaussian_filter(w, 1.5), 1e-6)
    gy, gx = np.gradient(sm)
    norm = np.hypot(gy, gx)
    ty, tx = np.where(norm > 0, gy / np.maximum(norm, 1e-9), 0.0), np.where(norm > 0, gx / np.maximum(norm, 1e-9), 0.0)
    up = lambda a: np.repeat(np.repeat(a, k, axis=0), k, axis=1)[:H, :W]  # noqa: E731
    piece = np.where(mask, up(lab), 0)
    s = np.where(mask & (piece > 0), up(s_small), np.nan)
    return {"piece": piece, "s": s, "ty": up(ty).astype(np.float32), "tx": up(tx).astype(np.float32), "height": height}


def band_height_mm(mask: np.ndarray, res: float) -> float:
    """The band's typical height: twice the 90th percentile of the distance from inside to its edge."""
    if not mask.any():
        return 0.0
    d = ndimage.distance_transform_edt(mask)[mask] * res
    return float(2.0 * np.percentile(d, 90))


def group_runes(branch_labels: np.ndarray, field: dict, res: float) -> dict:
    """Runes along the bands: {"branch_rune": {branch: rune}, "runes": [{id, piece, branches, extent, s0, s1}],
    "strokes": {branch: {p0, p1, length_mm}} (grid cells), "gap_mm" (the limit in the median band's mm),
    "gap_bands" (the limit in band heights), "band_height_mm" (median over the pieces), "items" and "heights" (the
    strokes along the bands, for utdata/stavlosa/)}. field is the band field of
    src/rune_bands (mask, and pieces when the bands were drawn)."""
    mask = field["mask"]
    co = band_coordinate(mask, res, field.get("pieces"))
    piece, s, heights = co["piece"], co["s"], co["height"]
    objs = ndimage.find_objects(branch_labels)
    cos_along = math.cos(math.radians(ALONG_DEG))
    items, strokes = [], {}  # items: (piece, s0, s1, branch, extent)
    for b, sl in enumerate(objs, start=1):
        if sl is None:
            continue
        yy, xx = np.nonzero(branch_labels[sl] == b)
        if len(yy) < 2:
            continue
        yy, xx = yy + sl[0].start, xx + sl[1].start
        inside = mask[yy, xx]
        if inside.mean() < 0.5:
            continue
        pc = piece[yy[inside], xx[inside]]
        sv = s[yy[inside], xx[inside]]
        ok = (pc > 0) & np.isfinite(sv)
        if not ok.any():
            continue
        p_main = int(np.bincount(pc[ok]).argmax())
        band_h = heights.get(p_main, 0.0)
        P = np.column_stack([yy, xx]).astype(float)
        c = P - P.mean(axis=0)
        ax = np.linalg.eigh(c.T @ c)[1][:, -1]
        t = c @ ax
        length = float(np.ptp(t) * res)
        if length > max(1.5 * band_h, 1.0):
            continue  # far longer than the band is high: not a rune stroke
        cy = min(max(int(round(P[:, 0].mean())), 0), mask.shape[0] - 1)
        cx = min(max(int(round(P[:, 1].mean())), 0), mask.shape[1] - 1)
        if abs(ax[0] * co["ty"][cy, cx] + ax[1] * co["tx"][cy, cx]) >= cos_along and length > 0.25 * band_h:
            continue  # runs along the band: a piece of its edge
        sv = sv[ok & (pc == p_main)]
        if float(sv.max() - sv.min()) > MAX_ALONG_BANDS * band_h:
            continue  # reaches far along the band: an edge or ornament, not a rune stroke
        mid = P.mean(axis=0)
        strokes[b] = {"p0": mid + ax * t.min(), "p1": mid + ax * t.max(), "length_mm": length}
        items.append((p_main, float(sv.min()), float(sv.max()), b,
                      (float(yy.min()), float(xx.min()), float(yy.max()), float(xx.max()))))
    items.sort()
    limit = GAP_BANDS
    runes, branch_rune = [], {}
    cur = None
    for p, a, e, b, ext in items:
        h = heights.get(p, 0.0)
        if (cur is not None and p == cur["piece"] and a - cur["s1"] <= limit * h
                and max(cur["s1"], e) - cur["s0"] <= MAX_WIDTH_BANDS * h):
            cur["branches"].append(b)
            cur["s1"] = max(cur["s1"], e)
            x = cur["extent"]
            cur["extent"] = (min(x[0], ext[0]), min(x[1], ext[1]), max(x[2], ext[2]), max(x[3], ext[3]))
        else:
            cur = {"id": len(runes) + 1, "piece": p, "s0": a, "s1": e, "branches": [b], "extent": ext}
            runes.append(cur)
        branch_rune[b] = cur["id"]
    med_h = float(np.median(list(heights.values()))) if heights else 0.0
    return {"branch_rune": branch_rune, "runes": runes, "strokes": strokes, "gap_mm": limit * med_h,
            "gap_bands": limit, "band_height_mm": med_h,
            "items": [(int(p), round(a, 2), round(e, 2)) for p, a, e, _b, _x in items], "heights": heights}
