"""Automatisk spåranalys och automatisk snittriktning för 3D-skanningar av runstenar.

Flöde för automatisk analys (se METHODS.md):
  1. Höjdfält: skanningen projiceras på ett plan vinkelrätt mot den ristade ytans normal.
  2. Referensyta: en utjämnad yta som "fyller igen" fördjupningar (iterativ övre envelopp).
  3. Spår: punkter som ligger tydligt under referensytan (tröskel = k · robust brusnivå).
  4. Mittlinjer: spåren tunnas ut till ett skelett; korsningar och ändar utesluts.
  5. Mätning: tvärsnitt med jämna mellanrum längs mittlinjerna, mätta med samma
     calculate_v_angle som den manuella analysen, och kvalitetsgranskade.
"""
from __future__ import annotations

import base64
import io
import math

import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree
from skimage.morphology import remove_small_objects, skeletonize

from src.slice_analysis import calculate_v_angle, extract_2d_profile_from_mesh, raw_profile
from src.stats import METRICS

ANGLE_COLOR_RANGE = (30.0, 130.0)


def _unit(v) -> np.ndarray:
    v = np.asarray(v, dtype=float)
    n = np.linalg.norm(v)
    if n == 0:
        raise ValueError("Normalvektorn får inte vara noll.")
    return v / n


def basis(normal, up=None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Ortonormal bas (u, v, n) där n är ytans normal. Med `up` (t.ex. kamerans upp-riktning)
    pekar v uppåt och u åt höger, så att höjdfältet ser ut som stenen gör på skärmen."""
    n = _unit(normal)
    if up is not None:
        up = np.asarray(up, dtype=float)
        v_raw = up - np.dot(up, n) * n
        if np.linalg.norm(v_raw) > 1e-6:
            v = _unit(v_raw)
            return np.cross(v, n), v, n
    helper = np.array([1.0, 0.0, 0.0]) if abs(n[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    u = _unit(np.cross(helper, n))
    v = np.cross(n, u)
    return u, v, n


class Heightfield:
    """Höjdfält över den ristade ytan. Rader = v-axeln, kolumner = u-axeln, värde = höjd längs n."""

    def __init__(self, points: np.ndarray, normal, resolution: float, up=None):
        self.u, self.v, self.n = basis(normal, up)
        a, b, h = points @ self.u, points @ self.v, points @ self.n
        self.res = float(resolution)
        self.a0, self.b0 = float(a.min()), float(b.min())
        nx = int((a.max() - self.a0) / self.res) + 1
        ny = int((b.max() - self.b0) / self.res) + 1
        ix = ((a - self.a0) / self.res).astype(np.int64)
        iy = ((b - self.b0) / self.res).astype(np.int64)
        H = np.full((ny, nx), -np.inf)
        # Sorted assignment: the highest point per cell wins (the surface facing the normal)
        order = np.argsort(h)
        H[iy[order], ix[order]] = h[order]
        self.valid = np.isfinite(H)
        self.region = ndimage.binary_fill_holes(ndimage.binary_closing(self.valid, iterations=2))
        idx = ndimage.distance_transform_edt(~self.valid, return_distances=False, return_indices=True)
        self.H = H[tuple(idx)]

    @classmethod
    def from_mesh(cls, mesh, normal, max_cells: int = 6_000_000, resolution: float | None = None, up=None):
        pts = np.vstack([mesh.vertices, mesh.triangles_center])
        u, v, _ = basis(normal, up)
        a, b = pts @ u, pts @ v
        edges = mesh.edges_unique_length
        edge = float(np.median(edges)) if len(edges) else 1.0
        area = float((a.max() - a.min()) * (b.max() - b.min()))
        res = resolution or max(edge, math.sqrt(area / max_cells))
        return cls(pts, normal, res, up)

    def to_world(self, iy: float, ix: float, h: float) -> np.ndarray:
        a = self.a0 + ix * self.res
        b = self.b0 + iy * self.res
        return a * self.u + b * self.v + h * self.n

    def sample(self, ys: np.ndarray, xs: np.ndarray) -> np.ndarray:
        return ndimage.map_coordinates(self.H, [ys, xs], order=1, mode="nearest")


def reference_surface(hf: Heightfield, scale_mm: float = 20.0, smooth_mm: float = 1.0) -> np.ndarray:
    """Stenytan utan ristningar, via morfologisk stängning (dilatation följd av erosion).

    Fördjupningar smalare än scale_mm fylls igen, medan plana, lutande och svagt välvda ytor
    bevaras. En lätt gaussisk utjämning (smooth_mm) dämpar mätbruset i referensen."""
    size = max(3, int(round(scale_mm / hf.res)) | 1)
    closed = ndimage.minimum_filter(ndimage.maximum_filter(hf.H, size=size), size=size)
    return ndimage.gaussian_filter(closed, smooth_mm / hf.res)


def trace_direction(hf: Heightfield, cy: float, cx: float, along: tuple[float, float],
                    half_width_mm: float, length_mm: float) -> tuple[tuple[float, float], tuple[float, float]]:
    """Förfinar spårets riktning genom att följa botten: på flera avstånd längs den preliminära
    riktningen letas lägsta punkten tvärs över spåret upp, och en linje anpassas genom dem.
    Returnerar (riktning, bottenpunkt vid centrum) i pixelkoordinater (rad, kolumn)."""
    ay, ax = along
    cr_y, cr_x = -ax, ay
    res = hf.res
    s = np.arange(-1.5 * half_width_mm, 1.5 * half_width_mm + 1e-9, res / 2)
    pts = []
    for o in np.arange(-length_mm, length_mm + 1e-9, max(res, length_mm / 6)):
        ys = cy + (o * ay + s * cr_y) / res
        xs = cx + (o * ax + s * cr_x) / res
        prof = ndimage.gaussian_filter1d(hf.sample(ys, xs), 2)
        k = int(np.argmin(prof))
        if 0 < k < len(s) - 1:  # a real minimum inside the window
            pts.append((ys[k], xs[k]))
    if len(pts) < 4:
        return along, (cy, cx)
    P = np.array(pts)
    c = P - P.mean(axis=0)
    _, vecs = np.linalg.eigh(c.T @ c)
    dy, dx = vecs[:, -1]
    if dy * ay + dx * ax < 0:
        dy, dx = -dy, -dx
    # Bottom point on the fitted line closest to the original centre
    t = (cy - P[:, 0].mean()) * dy + (cx - P[:, 1].mean()) * dx
    return (dy, dx), (P[:, 0].mean() + t * dy, P[:, 1].mean() + t * dx)


def _neighbour_count(skel: np.ndarray) -> np.ndarray:
    k = np.ones((3, 3), dtype=int)
    return ndimage.convolve(skel.astype(int), k, mode="constant") - skel.astype(int)


def _greedy_spacing(coords: np.ndarray, spacing_px: float) -> np.ndarray:
    """Väljer punkter med minst spacing_px avstånd (deterministiskt)."""
    if len(coords) == 0:
        return coords
    cell = spacing_px
    grid: dict[tuple[int, int], list[np.ndarray]] = {}
    chosen = []
    for p in coords:
        key = (int(p[0] // cell), int(p[1] // cell))
        ok = True
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                for q in grid.get((key[0] + dy, key[1] + dx), ()):
                    if (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 < spacing_px ** 2:
                        ok = False
                        break
                if not ok:
                    break
            if not ok:
                break
        if ok:
            grid.setdefault(key, []).append(p)
            chosen.append(p)
    return np.array(chosen)


def _end_direction(P: np.ndarray, end: np.ndarray, reach_px: float):
    """Riktning från en gren ut mot en ände (pixelkoordinater), skattad på grenens sista bit."""
    near = P[np.hypot(*(P - end).T) <= reach_px]
    if len(near) < 3:
        return None
    c = near - near.mean(axis=0)
    _, vecs = np.linalg.eigh(c.T @ c)
    d = vecs[:, -1]
    return d if np.dot(end - near.mean(axis=0), d) >= 0 else -d


def _ordered_path(P: np.ndarray) -> np.ndarray:
    """Ordnar en grens pixlar (8-grannar) från ena änden till den andra."""
    if len(P) < 3:
        return P
    tree = cKDTree(P)
    nbrs = tree.query_ball_point(P, 1.5)
    deg = np.array([len(n) - 1 for n in nbrs])
    start = int(np.argmin(deg))
    order, seen = [start], {start}
    while True:
        nxt = [j for j in nbrs[order[-1]] if j not in seen]
        if not nxt:
            break
        j = min(nxt, key=lambda j: np.hypot(*(P[j] - P[order[-1]])))
        order.append(j)
        seen.add(j)
    return P[order]


def _directions(P: np.ndarray, res: float, step_mm: float = 5.0) -> np.ndarray:
    """Riktningar (radianer) för korda med jämn båglängd längs en ordnad gren."""
    Q = _ordered_path(P) * res
    if len(Q) < 2:
        return np.array([])
    s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(Q, axis=0).T))])
    if s[-1] < 2 * step_mm:
        return np.array([])
    t = np.arange(0, s[-1] + 1e-9, step_mm)
    R = np.column_stack([np.interp(t, s, Q[:, 0]), np.interp(t, s, Q[:, 1])])
    d = np.diff(R, axis=0)
    return np.arctan2(d[:, 0], d[:, 1])


def _line_shape(P: np.ndarray, res: float) -> tuple[float, float]:
    """(längd, största avvikelse från rät linje) i mm för en punktmängd i pixelkoordinater."""
    if len(P) < 2:
        return len(P) * res, 0.0
    c = P - P.mean(axis=0)
    _, vecs = np.linalg.eigh(c.T @ c)
    along, across = c @ vecs[:, -1], c @ vecs[:, 0]
    return float(along.max() - along.min()) * res, float(np.abs(across).max()) * res


def classify_strokes(skel: np.ndarray, half_width: np.ndarray, res: float, rune_min_mm: float = 12.0,
                     rune_max_mm: float = 250.0, max_bend_deg: float = 25.0, max_width_cv: float = 0.5,
                     neighbour_factor: float = 2.5, max_local_deg: float = 20.0, max_turn_deg: float = 25.0,
                     perpendicular_deg: float = 20.0) -> dict:
    """Delar spårens mittlinjer i streck och avgör vilka som är runor (se METHODS.md, 2b).

    1. Mittlinjen bryts vid korsningar i grenar.
    2. Grenar som fortsätter rakt genom en korsning eller över ett kort avbrott (högst två spårbredder)
       slås ihop till ett streck: riktningen ändras högst max_bend_deg och linjerna förskjuts i sidled
       högst en halv spårbredd. En korsning räknas som hela området inom en halv spårbredd. En
       slingkant som runor stöter emot blir då ett långt streck, medan runans huvudstav och bistavar
       blir egna streck.
    3. Ett streck är ett runstreck om det är rakt – avvikelse från rät linje ≤ max(2 mm, 4 % av
       längden) och varje 10 mm-korda inom max_local_deg från streckets riktning –, lagom långt
       (rune_min_mm–rune_max_mm) och jämnbrett (variationskoefficient ≤ max_width_cv).
       Raka streck längre än 2,2 × 75:e percentilen av runstreckens längd (minst åtta runstreck)
       räknas som ram- eller slinglinjer, eftersom runorna i en inskrift är ungefär lika höga. Ett rakt
       streck som fortsätter en ram- eller slinglinje (inte ett kort böjt streck) (i linje med den över en korsning eller ett avbrott) hör
       också till linjen; regeln sprids längs linjen. Stavarna i en runrad är ungefär parallella och
       slinglinjerna går tvärs över dem, medan bistavarna sitter snett: ett streck som står vinkelrätt
       (±perpendicular_deg) mot den tydligt dominerande riktningen bland runstrecken inom tre
       stavlängder (minst 1,5 gånger så mycket streck tvärs som längs) och är minst en halv stavlängd
       långt är en del av en slinglinje.
       Långa eller jämnt böjda streck är ornamentik eller slingkanter. Sicksackande spår (median-
       vridningen mellan 5 mm-kordor > max_turn_deg, eller > 8° med växlande vridriktning i mer än
       40 % av fallen), korta och ojämna spår kan vara naturliga sprickor och vittring.
    4. Runstreck som sitter ihop bildar en runa. En runa godtas bara om minst en annan runa finns
       inom neighbour_factor × dess höjd – runor står i rader, medan ett ensamt rakt spår lika
       gärna kan vara en naturlig spricka eller en repa. Har stenen slinglinjer (ornamentstreck minst
       en halv stavlängd långa, sammanlagt minst fyra stavlängder; stavlängd = 90:e percentilen av
       runstreckens längd) måste runans mitt dessutom ligga inom 0,75 × max(stavlängd, runans höjd)
       från en sådan linje, eftersom runorna står i banden.

    Returnerar en etikett per mittlinjepixel ("branch"), etikett → streck, strecktyp och runor."""
    nb = _neighbour_count(skel)
    # A junction is a blob as wide as the groove: thick crossings give several junction pixels joined by
    # stubs that carry no direction, so everything within the groove's half-width of a junction is one zone
    hw_typ = float(np.median(half_width[skel])) if skel.any() else res
    r_px = max(1, int(round(hw_typ / res)))
    junction_zone = ndimage.binary_dilation(skel & (nb >= 3), structure=np.ones((3, 3)), iterations=r_px) & skel
    junction_zone = ndimage.binary_dilation(junction_zone, structure=np.ones((3, 3)))
    branches, n_br = ndimage.label(skel & ~junction_zone, structure=np.ones((3, 3)))
    if n_br == 0:
        return {"branch_labels": branches, "branch_stroke": {}, "strokes": {}, "runes": []}
    objs = ndimage.find_objects(branches)
    pts = {}
    for b, sl in enumerate(objs, start=1):
        yy, xx = np.nonzero(branches[sl] == b)
        pts[b] = np.column_stack([yy + sl[0].start, xx + sl[1].start]).astype(float)

    # Join branches by good continuation (union-find): through junctions and across short gaps
    parent = list(range(n_br + 1))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    reach = max(4.0, 6.0 / res)
    cos_max = math.cos(math.radians(max_bend_deg))
    max_offset = max(1.5, hw_typ) / res

    def ends_of(b):
        """Branch ends (pixel, outward direction): the two pixels farthest apart along the branch."""
        P = pts[b]
        if len(P) < 3:
            return []
        c = P - P.mean(axis=0)
        t = c @ np.linalg.eigh(c.T @ c)[1][:, -1]
        out = []
        for e in (P[np.argmin(t)], P[np.argmax(t)]):
            d = _end_direction(P, e, reach)
            if d is not None:
                out.append((e, d))
        return out

    def continues(ea, da, eb, db):
        """b continues a's line: opposite directions, and b's end lies on a's line (small sideways offset)."""
        if np.dot(da, -db) < cos_max:
            return False
        v = eb - ea
        return abs(v[0] * da[1] - v[1] * da[0]) <= max_offset and np.dot(v, da) >= -max_offset

    end_list = [(b, e, d) for b in range(1, n_br + 1) for e, d in ends_of(b)]
    if end_list:
        E = np.array([e for _, e, _ in end_list])
        tree = cKDTree(E)
        # Candidate pairs: ends that meet across a junction zone (a crossing groove plus the zone on each
        # side) or across a gap of at most two groove widths
        gap_px = max(3.0, 4.0 * hw_typ) / res + 2 * (r_px + 1)
        pairs = []
        for i, j in tree.query_pairs(gap_px):
            (a, ea, da), (b, eb, db) = end_list[i], end_list[j]
            if a != b and continues(ea, da, eb, db) and continues(eb, db, ea, da):
                pairs.append((float(np.dot(da, -db)) - 0.01 * float(np.hypot(*(eb - ea))), i, j))
        used = set()
        for _, i, j in sorted(pairs, reverse=True):
            if i not in used and j not in used and find(end_list[i][0]) != find(end_list[j][0]):
                parent[find(end_list[i][0])] = find(end_list[j][0])
                used.update((i, j))

    branch_stroke = {b: find(b) for b in range(1, n_br + 1)}
    members: dict[int, list[int]] = {}
    for b, s in branch_stroke.items():
        members.setdefault(s, []).append(b)

    strokes = {}
    for s, bs in members.items():
        P = np.vstack([pts[b] for b in bs])
        length, dev = _line_shape(P, res)
        hw = half_width[P[:, 0].astype(int), P[:, 1].astype(int)]
        cv = float(np.std(hw) / np.mean(hw)) if np.mean(hw) > 0 else float("inf")
        c = P - P.mean(axis=0)
        axis = np.linalg.eigh(c.T @ c)[1][:, -1]
        axis_angle = math.atan2(axis[0], axis[1])
        local, turns, flips, bends = [], [], 0, 0
        for b in bs:
            a = _directions(pts[b], res)
            local.extend(np.abs((_directions(pts[b], res, 10.0) - axis_angle + np.pi / 2) % np.pi - np.pi / 2))
            t = np.degrees((np.diff(a) + np.pi) % (2 * np.pi) - np.pi)
            turns.extend(np.abs(t))
            # Direction changes beyond the pixel noise: a smooth curve keeps turning the same way, a crack alternates
            sig = np.sign(t[np.abs(t) > 8.0])
            flips += int((sig[1:] != sig[:-1]).sum())
            bends += max(0, len(sig) - 1)
        local_dev = math.degrees(max(local)) if local else 0.0
        turn = float(np.median(turns)) if turns else 0.0
        zigzag = flips / bends if bends >= 3 else 0.0
        straight = dev <= max(2.0, 0.04 * length) and local_dev <= max_local_deg
        if length < rune_min_mm or cv > max_width_cv:
            kind = "irregular"  # short or uneven: possibly a natural crack or weathering
        elif straight:
            kind = "rune" if length <= rune_max_mm else "ornament"
        elif turn > max_turn_deg or (turn > 8.0 and zigzag > 0.4):
            kind = "irregular"  # zigzagging: possibly a natural crack
        else:
            kind = "ornament"  # smoothly curved: ornament or band edge
        strokes[s] = {"kind": kind, "band": kind == "ornament" and length > rune_max_mm, "length_mm": length, "deviation_mm": dev, "local_deg": local_dev,
                      "turn_deg": turn, "zigzag": zigzag, "width_cv": cv, "branches": bs,
                      "angle": axis_angle % math.pi, "centre": P.mean(axis=0)}

    # The runes of one inscription are about equally tall: a straight stroke far longer than the typical
    # stave is a frame or band line
    rune_len = [st["length_mm"] for st in strokes.values() if st["kind"] == "rune"]
    if len(rune_len) >= 8:
        limit = 2.2 * float(np.percentile(rune_len, 75))
        for st in strokes.values():
            if st["length_mm"] > limit and (st["kind"] == "rune" or (st["kind"] == "ornament" and st["local_deg"] <= 2 * max_local_deg)):
                st["kind"], st["band"] = "ornament", True

    # A straight piece that continues a band or frame line (in line with it, across a crossing or a gap) is
    # part of that line, not a rune: runes meet band lines at an angle. Spread along the line.
    if end_list:
        loose = math.cos(math.radians(1.4 * max_bend_deg))
        for _ in range(20):
            changed = False
            for i, j in tree.query_pairs(1.5 * gap_px):
                (a, ea, da), (b, eb, db) = end_list[i], end_list[j]
                sa, sb = strokes[find(a)], strokes[find(b)]
                if sb["kind"] == "rune":
                    sa, sb, (ea, da), (eb, db) = sb, sa, (eb, db), (ea, da)
                if sa["kind"] != "rune" or not sb.get("band") or np.dot(da, -db) < loose:
                    continue
                v = eb - ea
                if abs(v[0] * da[1] - v[1] * da[0]) <= 2 * max_offset or abs(v[0] * db[1] - v[1] * db[0]) <= 2 * max_offset:
                    sa["kind"], sa["band"] = "ornament", True
                    changed = True
            if not changed:
                break

    # Staves in a row of runes are about parallel and band lines run across them, while branches are oblique.
    # A stroke at right angles (±perpendicular_deg) to the clearly dominant local stave direction, and at
    # least half as long as a typical stave, is a piece of band line.
    cand = [st for st in strokes.values() if st["kind"] == "rune"]
    if len(cand) >= 8:
        typical = float(np.percentile([st["length_mm"] for st in cand], 75))
        C = np.array([st["centre"] for st in cand]) * res
        A = np.array([st["angle"] for st in cand])
        W = np.array([st["length_mm"] for st in cand])
        ctree = cKDTree(C)
        tol = math.radians(perpendicular_deg)
        demote = []
        for k, st in enumerate(cand):
            if st["length_mm"] < 0.5 * typical:
                continue
            near = ctree.query_ball_point(C[k], 3.0 * typical)
            diff = np.abs((A[near] - A[k] + np.pi / 2) % np.pi - np.pi / 2)  # 0 = parallel, π/2 = across
            across = W[near][diff >= np.pi / 2 - tol].sum()  # strokes at right angles to this one
            along = W[near][diff <= tol].sum()  # strokes parallel to this one (itself included)
            if across >= 1.5 * along:
                demote.append(st)
        for st in demote:
            st["kind"], st["band"] = "ornament", True

    # Runes: rune strokes that touch (across the removed junction zones)
    rune_px = np.isin(branches, [b for b, s in branch_stroke.items() if strokes[s]["kind"] == "rune"])
    grown = ndimage.binary_dilation(rune_px, structure=np.ones((3, 3)), iterations=r_px + 3)
    groups, n_g = ndimage.label(grown, structure=np.ones((3, 3)))
    runes = []
    stroke_rune = {}
    for s, st in strokes.items():
        if st["kind"] != "rune":
            continue
        P = np.vstack([pts[b] for b in st["branches"]])
        g = int(np.bincount(groups[P[:, 0].astype(int), P[:, 1].astype(int)]).argmax())
        stroke_rune[s] = g
    for g in range(1, n_g + 1):
        ss = [s for s, r in stroke_rune.items() if r == g]
        if not ss:
            continue
        P = np.vstack([pts[b] for s in ss for b in strokes[s]["branches"]])
        height = max(strokes[s]["length_mm"] for s in ss)
        runes.append({"id": g, "strokes": ss, "height_mm": height, "centre": P.mean(axis=0)})
    # A rune needs company: runes stand in rows
    for r in runes:
        r["supported"] = any(o is not r and np.hypot(*(o["centre"] - r["centre"])) * res
                             <= neighbour_factor * max(r["height_mm"], o["height_mm"]) for o in runes)
    # On a stone with band or frame lines the runes stand inside the bands: a rune's centre lies within
    # about half a band width of a band line. Straight weathering lines in the open field are not runes.
    rune_len = [st["length_mm"] for st in strokes.values() if st["kind"] == "rune"]
    stave = float(np.percentile(rune_len, 90)) if rune_len else 0.0  # a whole stave (branches are shorter)
    band_b = [b for b, s in branch_stroke.items()
              if strokes[s]["kind"] == "ornament" and (strokes[s].get("band") or strokes[s]["length_mm"] >= 0.5 * stave)]
    if band_b and rune_len:
        band_px = np.isin(branches, band_b)
        if band_px.sum() * res >= 4 * stave:
            dist = ndimage.distance_transform_edt(~band_px) * res
            for r in runes:
                cy, cx = np.clip(np.round(r["centre"]).astype(int), 0, np.array(band_px.shape) - 1)
                if dist[cy, cx] > max(0.75 * stave, 0.75 * r["height_mm"]):
                    r["supported"] = False
    supported = {r["id"] for r in runes if r["supported"]}
    for s, g in stroke_rune.items():
        if g not in supported:
            strokes[s]["kind"] = "isolated"
        strokes[s]["rune"] = g
    return {"branch_labels": branches, "branch_stroke": branch_stroke, "strokes": strokes,
            "runes": [r for r in runes if r["supported"]]}


STROKE_REASONS = {
    "ornament": "inte runa: långt eller böjt spår (ornamentik/slingkant)",
    "irregular": "inte runa: kort, krokigt eller ojämnt spår (möjlig spricka)",
    "isolated": "inte runa: ensamt rakt spår utan andra runor intill",
}


def _angle_color(angle: float) -> tuple[int, int, int]:
    from matplotlib import colormaps
    lo, hi = ANGLE_COLOR_RANGE
    t = min(1.0, max(0.0, (angle - lo) / (hi - lo)))
    r, g, b, _ = colormaps["viridis"](t)
    return int(r * 255), int(g * 255), int(b * 255)


def _overlay_png(hf: Heightfield, mask: np.ndarray, wide: np.ndarray, slices: list[dict],
                 max_side: int = 1600) -> tuple[str, int, int, float]:
    from PIL import Image, ImageDraw

    gy, gx = np.gradient(hf.H, hf.res)
    # Hillshade with light from the upper left of the image (image y grows downwards)
    lx, ly, lz = -0.6, 0.6, 0.55
    shade = (-gx * lx - gy * ly + lz) / np.sqrt(gx ** 2 + gy ** 2 + 1)
    shade = np.clip(0.35 + 0.65 * shade / max(lz, 1e-6), 0, 1)
    rgb = np.dstack([shade * 235, shade * 232, shade * 226])
    rgb[~hf.region] = (245, 245, 245)
    tint = np.array([183, 65, 14], dtype=float)
    narrow = mask & ~wide
    rgb[narrow] = rgb[narrow] * 0.55 + tint * 0.45
    # Areas too wide to be a carved groove: shown, but not measured
    grey = np.array([120, 140, 170], dtype=float)
    rgb[wide] = rgb[wide] * 0.6 + grey * 0.4
    img = Image.fromarray(np.flipud(rgb).astype(np.uint8))
    scale = min(1.0, max_side / max(img.size))
    if scale < 1:
        img = img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))), Image.LANCZOS)
    draw = ImageDraw.Draw(img)
    ny = hf.H.shape[0]
    for s in slices:
        x = s["_ix"] * scale
        y = (ny - 1 - s["_iy"]) * scale
        s["img_x"], s["img_y"] = float(x), float(y)
        if s["accepted"]:
            draw.ellipse((x - 3.5, y - 3.5, x + 3.5, y + 3.5), fill=_angle_color(s["apex_vinkel_deg"]),
                         outline=(15, 23, 42))
        else:
            draw.ellipse((x - 1.5, y - 1.5, x + 1.5, y + 1.5), fill=(120, 120, 120))
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode("ascii"), img.width, img.height, scale


def _groove_map_png(hf: Heightfield, residual: np.ndarray, inner: np.ndarray, threshold: float,
                    size: tuple[int, int]) -> str:
    """Ristningskarta: spårdjupet som gråskala (mörkt = djupt), utan belysning och färg.
    Samma storlek och orientering som granskningsbilden, så att koordinaterna stämmer."""
    from PIL import Image

    depth = np.clip(-residual, 0, None)
    ref_depth = float(np.percentile(depth[depth > threshold], 95)) if (depth > threshold).any() else 1.0
    v = np.clip(depth / max(ref_depth, 1e-6), 0, 1)
    gray = (255 * (1 - v)).astype(np.uint8)
    gray[~hf.region] = 255
    img = Image.fromarray(np.flipud(gray)).resize(size, Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def analyze_grooves(mesh, normal, spacing_mm: float = 3.0, sensitivity: float = 3.0,
                    min_depth_mm: float = 0.3, scale_mm: float = 20.0, edge_margin_mm: float = 5.0,
                    min_fit_r2: float = 0.8, max_cells: int = 6_000_000, face_tree: cKDTree | None = None,
                    max_halfwidth_mm: float = 8.0, max_slope_deg: float = 45.0, up=None,
                    resolution_mm: float | None = None, harmonize_mm: float | None = None,
                    runes_only: bool = True, rune_min_mm: float = 12.0, rune_max_mm: float = 250.0) -> dict:
    """Hittar spåren i höjdfältet och mäter tvärsnitt genom själva mesh-filen, med samma
    profilutdragning och samma calculate_v_angle som den manuella analysen.

    Med runes_only mäts bara snitt på streck som classify_strokes känner igen som runor; övriga
    spår (ornamentik, slingkanter, möjliga sprickor) visas men mäts inte."""
    hf = Heightfield.from_mesh(mesh, normal, max_cells=max_cells, resolution=resolution_mm, up=up)
    edges = mesh.edges_unique_length
    mesh_spacing = float(np.median(edges)) if len(edges) else float("nan")
    face_tree = face_tree or cKDTree(mesh.triangles_center)
    res = hf.res
    ref = reference_surface(hf, scale_mm=scale_mm)
    residual = hf.H - ref

    # Pad with background so that the grid's own border also counts as an edge of the scan. The reference
    # surface is unreliable within half its scale of an edge, so the margin is at least that wide.
    margin = max(edge_margin_mm, scale_mm / 2)
    inner = (ndimage.distance_transform_edt(np.pad(hf.region, 1))[1:-1, 1:-1] * res) > margin
    # Exclude steep parts (the stone's sides and edges) where the surface turns away from the view
    gy, gx = np.gradient(ref, res)
    inner &= np.hypot(gx, gy) < math.tan(math.radians(max_slope_deg))
    if inner.sum() < 100:
        raise ValueError("Skanningens yta är för liten för automatisk analys.")
    d_in = residual[inner]
    noise = 1.4826 * float(np.median(np.abs(d_in - np.median(d_in))))
    threshold = max(min_depth_mm, sensitivity * noise)

    mask = (residual < -threshold) & inner
    mask = ndimage.binary_opening(mask)
    min_area_px = max(4, int(10.0 / (res * res)))  # spår mindre än ~10 mm² är brus
    mask = remove_small_objects(mask, max_size=min_area_px)
    # Fill only small holes (noise inside a groove). Filling every hole would also fill a rune band
    # closed off by staves, or the inside of a rune's loop, which then counted as one wide area.
    holes, _ = ndimage.label(ndimage.binary_fill_holes(mask) & ~mask)
    hole_size = np.bincount(holes.ravel())
    hole_size[0] = 0
    mask |= (hole_size <= min_area_px)[holes] & (holes > 0)

    skel = skeletonize(mask)
    half_width = ndimage.distance_transform_edt(mask) * res
    nb = _neighbour_count(skel)
    junctions = skel & (nb >= 3)
    endpoints = skel & (nb == 1)
    dist_junction = ndimage.distance_transform_edt(~junctions) * res if junctions.any() else np.full(skel.shape, np.inf)
    dist_end = ndimage.distance_transform_edt(~endpoints) * res if endpoints.any() else np.full(skel.shape, np.inf)

    skel_coords = np.argwhere(skel)
    tree = cKDTree(skel_coords) if len(skel_coords) else None
    # Areas wider than a carved groove (e.g. a lowered field or a flaked surface) are not measured
    too_wide = ndimage.maximum_filter(half_width, size=3) > max_halfwidth_mm
    # The too-wide parts themselves (grown back to their edges), for the review image
    core = half_width > max_halfwidth_mm
    wide_area = (ndimage.binary_dilation(core, iterations=max(1, int(max_halfwidth_mm / res)))
                 & mask) if core.any() else np.zeros_like(mask)
    candidates = skel & ~too_wide & (dist_junction > np.maximum(2.0 * half_width, 3.0)) & (dist_end > half_width)
    cand_coords = np.argwhere(candidates)
    samples = _greedy_spacing(cand_coords, spacing_mm / res)

    strokes = classify_strokes(skel, half_width, res, rune_min_mm=rune_min_mm, rune_max_mm=rune_max_mm)
    branch_labels = strokes["branch_labels"]
    branch_coords = np.argwhere(branch_labels > 0)
    branch_tree = cKDTree(branch_coords) if len(branch_coords) else None

    def stroke_at(iy, ix):
        b = int(branch_labels[iy, ix])
        if b == 0 and branch_tree is not None:
            dist, j = branch_tree.query([iy, ix])
            if dist * res <= max(3.0, 2.0 * half_width[iy, ix]):
                b = int(branch_labels[tuple(branch_coords[j])])
        if b == 0:
            return None, None
        sid = strokes["branch_stroke"][b]
        return sid, strokes["strokes"][sid]

    slices: list[dict] = []
    reasons: dict[str, int] = {}

    def reject(rec, reason):
        rec["accepted"] = False
        rec["reason"] = reason
        reasons[reason] = reasons.get(reason, 0) + 1

    for k, (iy, ix) in enumerate(samples):
        hw = float(half_width[iy, ix])
        rec: dict = {"_iy": float(iy), "_ix": float(ix), "halfwidth_mm": hw, "position_mm": k * spacing_mm}
        sid, stroke = stroke_at(iy, ix)
        rec["feature"] = stroke["kind"] if stroke else "irregular"
        if stroke and stroke["kind"] == "rune":
            rec["rune_id"] = int(stroke["rune"])
            rec["stroke_id"] = int(sid)
        if runes_only and rec["feature"] != "rune":
            reject(rec, STROKE_REASONS[rec["feature"]])
            slices.append(rec)
            continue
        if hw < 2 * res:
            reject(rec, "för smalt för upplösningen")
            slices.append(rec)
            continue
        idx = tree.query_ball_point([iy, ix], max(3.0, 2.0 * hw) / res)
        local = skel_coords[idx].astype(float)
        if len(local) < 3:
            reject(rec, "för kort mittlinje")
            slices.append(rec)
            continue
        c = local - local.mean(axis=0)
        _, vecs = np.linalg.eigh(c.T @ c)
        t_y, t_x = vecs[:, -1]  # tangent in (row, col), from the centre line
        (t_y, t_x), (by, bx) = trace_direction(hf, float(iy), float(ix), (t_y, t_x), max(hw, 2.0),
                                               max(3.0, 1.5 * hw))
        W = max(4.0, 3.0 * hw)
        h_bottom = float(hf.sample(np.array([by]), np.array([bx]))[0])
        point = hf.to_world(by, bx, h_bottom)
        tangent = _unit(t_x * hf.u + t_y * hf.v)
        try:
            s, z = extract_2d_profile_from_mesh(mesh, point, tangent, hf.n, window_mm=W, face_tree=face_tree)
            m = calculate_v_angle(s, z, harmonize_mm=harmonize_mm)
        except Exception:
            reject(rec, "anpassningen misslyckades")
            slices.append(rec)
            continue
        rec.update({key: float(m[key]) for key in METRICS})
        rec["fit_r2"] = float(m["fit_r2"])
        apex_x = float(m["x"][m["apex_idx"]])
        rec["point"] = [float(v) for v in point]
        rec["direction"] = [float(v) for v in tangent]
        rec["up"] = [float(v) for v in hf.n]
        if not all(np.isfinite(m[key]) for key in (*METRICS, "fit_r2")):
            for key in (*METRICS, "fit_r2"):
                rec.pop(key, None)
            reject(rec, "för få punkter i snittet")
        elif not (15 < m["apex_vinkel_deg"] < 170):
            reject(rec, "orimlig vinkel")
        elif m["fit_r2"] < min_fit_r2:
            reject(rec, "dålig väggpassning")
        elif m["spårdjup_mm"] < threshold:
            reject(rec, "för grunt")
        elif m["left_shoulder"] == 0 or m["right_shoulder"] >= len(m["x"]) - 1:
            reject(rec, "spårkant hittades inte")
        elif abs(apex_x) > max(1.5, 1.5 * hw):
            reject(rec, "botten utanför mittlinjen")
        else:
            rec["accepted"] = True
            rec["reason"] = None
            rec["profile"] = raw_profile(s, z)
        slices.append(rec)

    image_b64, width, height, scale = _overlay_png(hf, mask, wide_area, slices)
    groove_map = _groove_map_png(hf, residual, inner, threshold, (width, height))
    for rec in slices:
        rec.pop("_iy", None)
        rec.pop("_ix", None)

    accepted = [s for s in slices if s["accepted"]]
    measured_runes = sorted({s["rune_id"] for s in accepted if "rune_id" in s})
    kinds = {}
    for st in strokes["strokes"].values():
        kinds[st["kind"]] = kinds.get(st["kind"], 0) + 1
    return {
        "slices": slices,
        "image_base64": f"data:image/png;base64,{image_b64}",
        "groove_map_base64": groove_map,
        "image_width": width,
        "image_height": height,
        "angle_color_range": list(ANGLE_COLOR_RANGE),
        "counts": {
            "candidates": len(slices),
            "accepted": len(accepted),
            "rejected": len(slices) - len(accepted),
            "rejection_reasons": reasons,
            "groove_area_mm2": float((mask & ~wide_area).sum() * res * res),
            "wide_area_mm2": float(wide_area.sum() * res * res),
            "strokes": kinds,
            "runes_identified": len(strokes["runes"]),
            "runes_measured": len(measured_runes),
        },
        "runes": [{"id": int(r["id"]), "n_strokes": len(r["strokes"]), "height_mm": float(r["height_mm"]),
                   "n_slices": sum(1 for s in accepted if s.get("rune_id") == r["id"])}
                  for r in strokes["runes"]],
        "parameters": {
            "normal": [float(v) for v in hf.n],
            "up": [float(v) for v in hf.v],
            "resolution_mm": res,
            "mesh_point_spacing_mm": mesh_spacing,
            "harmonize_mm": harmonize_mm,
            "fixed_resolution": resolution_mm is not None,
            "reference_scale_mm": scale_mm,
            "noise_mm": noise,
            "threshold_mm": threshold,
            "sensitivity": sensitivity,
            "spacing_mm": spacing_mm,
            "edge_margin_mm": margin,
            "min_fit_r2": min_fit_r2,
            "max_halfwidth_mm": max_halfwidth_mm,
            "max_slope_deg": max_slope_deg,
            "runes_only": runes_only,
            "rune_min_mm": rune_min_mm,
            "rune_max_mm": rune_max_mm,
            "image_scale": scale,
        },
    }


def auto_slice(mesh, point, normal_hint=None, radius_mm: float = 15.0, tree: cKDTree | None = None) -> dict:
    """Snittriktning från ett enda klick i ett spår.

    Ytans normal skattas lokalt. Spårets riktning tas från höjdfältets Hessian vid klicket
    (den riktning där ytan kröker minst), på den skala där dalformen är tydligast.
    Mätpunkten flyttas till spårets botten."""
    point = np.asarray(point, dtype=float)
    tree = tree or cKDTree(mesh.vertices)
    idx = tree.query_ball_point(point, radius_mm)
    if len(idx) < 50:
        raise ValueError("För få punkter runt klicket. Klicka på stenens yta.")
    local = mesh.vertices[idx]
    c = local - local.mean(axis=0)
    _, vecs = np.linalg.eigh(c.T @ c)
    n = vecs[:, 0]
    # Orient outwards: with the clicked face's normal if given, otherwise the mesh's own vertex normals
    # (the click lies in a groove, below its surroundings, so its position cannot be used)
    reference = np.asarray(normal_hint, dtype=float) if normal_hint is not None else mesh.vertex_normals[idx].mean(axis=0)
    if np.dot(n, reference) < 0:
        n = -n

    nn_dist, _ = cKDTree(local).query(local[:: max(1, len(local) // 500)], k=2)
    spacing = float(np.median(nn_dist[:, 1]))
    res = min(max(spacing, radius_mm / 150), radius_mm / 40)
    hf = Heightfield(local - point, n, res)
    # Pixel of the clicked point (it is the origin of the local coordinates)
    cy, cx = -hf.b0 / res, -hf.a0 / res

    # Refine the normal with the groove-free reference surface (the groove biases the plane fit)
    ref = reference_surface(hf, scale_mm=min(20.0, radius_mm))
    gy, gx = np.gradient(ref, res)
    y0, x0 = int(round(cy)), int(round(cx))
    n = _unit(hf.n - gx[y0, x0] * hf.u - gy[y0, x0] * hf.v)
    hf = Heightfield(local - point, n, res)
    cy, cx = -hf.b0 / res, -hf.a0 / res

    best = None
    for scale_mm in (1.0, 2.0, 3.5, 5.0, 7.5):
        sp = scale_mm / res
        Hyy = ndimage.gaussian_filter(hf.H, sp, order=(2, 0))
        Hxx = ndimage.gaussian_filter(hf.H, sp, order=(0, 2))
        Hxy = ndimage.gaussian_filter(hf.H, sp, order=(1, 1))
        y0, x0 = int(round(cy)), int(round(cx))
        Hm = np.array([[Hyy[y0, x0], Hxy[y0, x0]], [Hxy[y0, x0], Hxx[y0, x0]]]) / (res * res)
        w, v = np.linalg.eigh(Hm)
        strength = scale_mm ** 2 * w[1]  # scale-normalised curvature across the valley
        if best is None or strength > best[0]:
            best = (strength, w, v, scale_mm)
    strength, w, v, scale_mm = best
    if strength <= 0.02:
        raise ValueError("Hittade inget spår vid klicket. Klicka mitt i en huggen linje.")

    along_y, along_x = v[:, 0]
    # Follow the groove bottom to refine direction and position
    (along_y, along_x), (by, bx) = trace_direction(hf, cy, cx, (along_y, along_x), 1.5 * scale_mm,
                                                   max(4.0, 2.0 * scale_mm))
    across_y, across_x = -along_x, along_y
    bottom = hf.to_world(by, bx, float(hf.sample(np.array([by]), np.array([bx]))[0])) + point

    along = _unit(along_x * hf.u + along_y * hf.v)
    across = _unit(across_x * hf.u + across_y * hf.v)
    return {
        "origin": [float(x) for x in bottom],
        "direction": [float(x) for x in along],
        "up": [float(x) for x in hf.n],
        "across": [float(x) for x in across],
        "scale_mm": scale_mm,
        "window_mm": float(max(8.0, 4 * scale_mm)),
        "confidence": float(w[1] / (abs(w[0]) + w[1] + 1e-12)),
    }
