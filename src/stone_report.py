"""Stenrapport: en artikel om en enskild runsten, dokumenterad med 3D-skanning.

Uppläggningen följer två traditioner. Stenen och inskriften presenteras som i Sveriges runinskrifter och
runologiska tidskrifter (signum, placering, material, translitterering i fetstil, normalisering i kursiv,
översättning inom citattecken, ristare, stilgrupp, datering, tidigare utgåva). Huggspårsanalysen redovisas
som en arkeometrisk studie (material och metod med 3D-dokumentationens paradata, resultat med figurer och
tabeller, diskussion, begränsningar, data och reproducerbarhet).

Alla figurer och siffror räknas fram här ur snittens råprofiler, deras positioner och – om 3D-modellen
finns i analysmotorns minne – själva ytan. En språkmodell får som mest formulera sammanfattning,
inledning och diskussion ur facts_text().
"""
from __future__ import annotations

import base64
import datetime
import io
import re
import warnings
from collections import defaultdict

import numpy as np

from src.academic import DIGITS, FEATURE_NAMES, bullets, figure, fmt, h, p, table
from src import r_report, scan_sources
from src.reading import runes_to_latin
from src.slice_analysis import PROFILE_STEP_MM, RIM_MM, calculate_v_angle
from src.stats import METRICS, METRIC_LABELS, attribute, compare_stones, summarize

ACCENT = "#b7410e"
GROUP_COLORS = {"rune": "#b7410e", "ornament": "#1f6f8b", "unknown": "#64748b"}
FEATURE_TITLES = {"rune": "Runor", "ornament": "Ornamentik", "unknown": "Ej angivet"}
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
PERIODS = {"V": "vikingatid (V)", "M": "medeltid (M)", "U": "urnordisk tid (U)"}

# Sveriges runinskrifter per landskap (signum utan tillägg som Fv, DR m.m.)
SRI = {
    "Öl": "Söderberg, S. & Brate, E. 1900–1906. Ölands runinskrifter. (Sveriges runinskrifter 1.) Stockholm.",
    "Ög": "Brate, E. 1911–1918. Östergötlands runinskrifter. (Sveriges runinskrifter 2.) Stockholm.",
    "Sö": "Brate, E. & Wessén, E. 1924–1936. Södermanlands runinskrifter. (Sveriges runinskrifter 3.) Stockholm.",
    "Sm": "Kinander, R. 1935–1961. Smålands runinskrifter. (Sveriges runinskrifter 4.) Stockholm.",
    "Vg": "Jungner, H. & Svärdström, E. 1940–1970. Västergötlands runinskrifter. (Sveriges runinskrifter 5.) Stockholm.",
    "U": "Wessén, E. & Jansson, S. B. F. 1940–1958. Upplands runinskrifter. (Sveriges runinskrifter 6–9.) Stockholm.",
    "G": "Jansson, S. B. F., Wessén, E. & Svärdström, E. 1962–1978. Gotlands runinskrifter. "
         "(Sveriges runinskrifter 11–12.) Stockholm.",
    "Vs": "Jansson, S. B. F. 1964. Västmanlands runinskrifter. (Sveriges runinskrifter 13.) Stockholm.",
    "Nä": "Jansson, S. B. F. 1975. Närkes runinskrifter. (Sveriges runinskrifter 14:1.) Stockholm.",
    "Vr": "Jansson, S. B. F. 1978. Värmlands runinskrifter. (Sveriges runinskrifter 14:2.) Stockholm.",
    "Gs": "Jansson, S. B. F. 1981. Gästriklands runinskrifter. (Sveriges runinskrifter 15:1.) Stockholm.",
}

REFERENCES = [
    "Gräslund, A.-S. 1998. Ornamentiken som dateringsgrund för Upplands runstenar. I: Innskrifter og "
    "datering / Dating inscriptions. Trondheim, s. 73–91.",
    "Kitzler Åhfeldt, L. 2002. Work and Worship. Laser Scanner Analysis of Viking Age Rune Stones. "
    "Stockholms universitet.",
    "Kitzler Åhfeldt, L. & Imer, L. M. 2019. Rune Carvers and Sponsor Families on Bornholm. "
    "Danish Journal of Archaeology 8. https://doi.org/10.7146/dja.v8i0.113226",
    "Samnordisk runtextdatabas. Institutionen för nordiska språk, Uppsala universitet. "
    "http://www.nordiska.uu.se/forskn/samnord.htm",
]


def fmt_p(v) -> str:
    if v is None:
        return "–"
    return "< 0,001" if v < 0.001 else fmt(v, 3)


def inscription(transliteration: str, normalization: str, normalization_ows: str, translation: str,
                source: str) -> dict:
    return {"type": "inscription", "transliteration": transliteration, "normalization": normalization,
            "normalization_ows": normalization_ows, "translation": translation, "source": source}


def _names(text: str) -> str:
    # Rundata marks proper names with a leading quotation mark
    return (text or "").replace('"', "")


def sri_reference(signum: str) -> str | None:
    m = re.match(r"^([A-ZÅÄÖ][a-zåäö]?) \d+\s*$", signum or "")
    return SRI.get(m.group(1)) if m else None


def sri_short(full: str) -> str:
    """'Wessén, E. & Jansson, S. B. F. 1940–1958. …' -> 'Wessén & Jansson 1940–1958'."""
    m = re.match(r"^(.*?) (\d{4}(?:–\d{4})?)\.", full)
    if not m:
        return full
    names = re.findall(r"([A-ZÅÄÖ][a-zåäöé]+),", m.group(1))
    return f"{' & '.join(names) if len(names) < 3 else names[0] + ' m.fl.'} {m.group(2)}"


# ---- figures -------------------------------------------------------------------------------

def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 8, "axes.titlesize": 9, "axes.labelsize": 8,
                         "font.family": "DejaVu Sans"})
    return plt


def _png(fig, dpi=220) -> str:
    plt = _plt()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _nice_length(span_mm: float) -> float:
    target = span_mm / 5
    return max([x for x in (1, 2, 5, 10, 20, 50, 100, 200, 500, 1000) if x <= max(target, 1)])


def _scalebar(ax, extent):
    x0, x1, y0, y1 = extent
    L = _nice_length(x1 - x0)
    pad = 0.04 * (x1 - x0)
    ax.plot([x0 + pad, x0 + pad + L], [y0 + pad, y0 + pad], color="black", lw=3, solid_capstyle="butt")
    ax.plot([x0 + pad, x0 + pad + L], [y0 + pad, y0 + pad], color="white", lw=1.2, solid_capstyle="butt")
    ax.text(x0 + pad + L / 2, y0 + pad * 1.6, f"{L:g} mm", ha="center", va="bottom", fontsize=7,
            bbox={"facecolor": "white", "alpha": 0.75, "edgecolor": "none", "pad": 1})


def hillshade(H: np.ndarray, res: float, azimuth_deg: float, altitude_deg: float) -> np.ndarray:
    """Belysning från azimut (0° = upp i bilden, medurs) och höjd över ytan."""
    gy, gx = np.gradient(H, res)
    az, alt = np.radians(azimuth_deg), np.radians(altitude_deg)
    L = np.array([np.cos(alt) * np.sin(az), np.cos(alt) * np.cos(az), np.sin(alt)])
    shade = (-gx * L[0] - gy * L[1] + L[2]) / np.sqrt(gx ** 2 + gy ** 2 + 1)
    return np.clip(shade, 0, 1)


class Surface:
    """Den ristade ytan som höjdfält, beskuren till skanningen och nedskalad för figurer."""

    def __init__(self, mesh, normal, up=None, max_cells: int = 3_000_000, max_px: int = 1800):
        from src.auto_grooves import Heightfield, reference_surface
        hf = Heightfield.from_mesh(mesh, normal, max_cells=max_cells, up=up)
        from scipy import ndimage
        residual = hf.H - reference_surface(hf, scale_mm=20.0)
        # The reference surface is unreliable within half its scale (10 mm) of the scan's edge
        inner = ndimage.distance_transform_edt(np.pad(hf.region, 1))[1:-1, 1:-1] * hf.res > 10.0
        rows, cols = np.where(hf.region)
        r0, r1, c0, c1 = rows.min(), rows.max() + 1, cols.min(), cols.max() + 1
        step = max(1, int(np.ceil(max(r1 - r0, c1 - c0) / max_px)))
        sl = (slice(r0, r1, step), slice(c0, c1, step))
        self.hf, self.H, self.residual, self.region = hf, hf.H[sl], residual[sl], hf.region[sl]
        self.inner = inner[sl]
        self.res = hf.res * step
        self.origin = (hf.a0 + c0 * hf.res, hf.b0 + r0 * hf.res)
        self.extent = (0.0, self.H.shape[1] * self.res, 0.0, self.H.shape[0] * self.res)

    def xy(self, point) -> tuple[float, float]:
        pt = np.asarray(point, float)
        return float(pt @ self.hf.u - self.origin[0]), float(pt @ self.hf.v - self.origin[1])

    def shaded(self, azimuth=315.0, altitude=35.0) -> np.ndarray:
        s = hillshade(self.H, self.res, azimuth, altitude)
        s[~self.region] = np.nan
        return s


def _gray(ax, img, extent, **kw):
    cmap = _plt().get_cmap("gray").copy()
    cmap.set_bad("white")
    return ax.imshow(img, cmap=cmap, origin="lower", extent=extent, vmin=0, vmax=1, interpolation="bilinear", **kw)


def _clean_axes(ax):
    ax.set_xlabel("mm")
    ax.set_ylabel("mm")
    ax.set_aspect("equal")
    ax.tick_params(labelsize=6)


def overview_figure(surf: Surface, slices: list[dict], marked: dict[int, str]) -> str:
    """Strykljus med snittens positioner, färgade efter V-vinkel; representativa snitt bokstavsmärkta."""
    plt = _plt()
    w, hgt = surf.extent[1], surf.extent[3]
    fig, ax = plt.subplots(figsize=(7, 7 * hgt / w if w else 7))
    _gray(ax, surf.shaded(), surf.extent)
    pts = [(surf.xy(s["point"]), s) for s in slices if s.get("point")]
    if pts:
        xs, ys = zip(*[xy for xy, _ in pts])
        angles = [s["apex_vinkel_deg"] for _, s in pts]
        sc = ax.scatter(xs, ys, c=angles, cmap="viridis", s=14, edgecolors="black", linewidths=0.3, zorder=3)
        cb = fig.colorbar(sc, ax=ax, fraction=0.035, pad=0.02)
        cb.set_label("V-vinkel (°)")
        for i, s in enumerate(slices):
            if i in marked and s.get("point"):
                x, y = surf.xy(s["point"])
                ax.annotate(marked[i], (x, y), xytext=(6, 6), textcoords="offset points", fontsize=8, weight="bold",
                            color="black", bbox={"facecolor": "white", "alpha": 0.85, "edgecolor": "black",
                                                 "boxstyle": "round,pad=0.15", "lw": 0.5}, zorder=4)
    _scalebar(ax, surf.extent)
    _clean_axes(ax)
    return _png(fig)


def raking_figure(surf: Surface) -> str:
    """Fyra strykljusvyer (låg ljusvinkel från fyra håll) – motsvarar fotografering i strykljus."""
    plt = _plt()
    w, hgt = surf.extent[1], surf.extent[3]
    fig, axes = plt.subplots(2, 2, figsize=(7, 7 * hgt / w if w else 7))
    for ax, (az, name) in zip(axes.flat, [(315, "nordväst"), (45, "nordost"), (135, "sydost"), (225, "sydväst")]):
        _gray(ax, surf.shaded(az, 20), surf.extent)
        ax.set_title(f"Ljus från {name}, 20°")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_aspect("equal")
    _scalebar(axes.flat[2], surf.extent)
    fig.tight_layout()
    return _png(fig)


def depth_figure(surf: Surface) -> str:
    """Djup under den rekonstruerade stenytan (morfologisk referensyta, 20 mm)."""
    plt = _plt()
    depth = np.clip(-surf.residual, 0, None)
    depth[~surf.inner] = np.nan
    vmax = float(np.nanpercentile(depth, 99.5)) if np.isfinite(depth).any() else 1.0
    w, hgt = surf.extent[1], surf.extent[3]
    fig, ax = plt.subplots(figsize=(7, 7 * hgt / w if w else 7))
    cmap = plt.get_cmap("magma_r").copy()
    cmap.set_bad("white")
    im = ax.imshow(depth, cmap=cmap, origin="lower", extent=surf.extent, vmin=0, vmax=max(vmax, 0.1),
                   interpolation="bilinear")
    cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cb.set_label("Djup under stenytan (mm)")
    _scalebar(ax, surf.extent)
    _clean_axes(ax)
    return _png(fig)


def spatial_figure(surf: Surface, slices: list[dict]) -> str | None:
    pts = [(surf.xy(s["point"]), s) for s in slices if s.get("point")]
    if len(pts) < 3:
        return None
    plt = _plt()
    w, hgt = surf.extent[1], surf.extent[3]
    fig, axes = plt.subplots(1, 3, figsize=(10, 10 / 3 * hgt / w + 0.6 if w else 4))
    xs, ys = zip(*[xy for xy, _ in pts])
    for ax, (m, cmap) in zip(axes, [("spårdjup_mm", "magma_r"), ("spårbredd_mm", "cividis"), ("ytråhet_mm", "plasma")]):
        _gray(ax, surf.shaded(), surf.extent, alpha=0.55)
        sc = ax.scatter(xs, ys, c=[s[m] for _, s in pts], cmap=cmap, s=10, edgecolors="black", linewidths=0.2)
        cb = fig.colorbar(sc, ax=ax, fraction=0.046, pad=0.02, orientation="horizontal")
        cb.set_label(METRIC_LABELS[m])
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_aspect("equal")
    fig.tight_layout()
    return _png(fig)


def _fit(profile: dict):
    x, z = np.asarray(profile["x"], float), np.asarray(profile["z"], float)
    if len(x) < 10:
        return None
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            m = calculate_v_angle(x, z)
    except Exception:
        return None
    if not np.isfinite(m["apex_vinkel_deg"]):
        return None
    return m["x"], m["z"], m  # the indices in m refer to the resampled profile


def profiles_figure(slices: list[dict], picks: list[int]) -> str | None:
    """Representativa tvärsnitt (från minsta till största V-vinkel) med anpassade spårväggar."""
    items = []
    for i in picks:
        f = _fit(slices[i]["profile"]) if slices[i].get("profile") else None
        if f:
            items.append((i, f))
    if not items:
        return None
    plt = _plt()
    cols = 4 if len(items) > 4 else len(items)
    rows = int(np.ceil(len(items) / cols))
    # Panels are about twice as wide as high at equal axis scale
    fig, axes = plt.subplots(rows, cols, figsize=(2.6 * cols, 1.45 * rows + 0.5), squeeze=False)
    for ax in axes.flat:
        ax.axis("off")
    for k, (i, (x, z, m)) in enumerate(items):
        ax = axes.flat[k]
        ax.axis("on")
        a = int(m["apex_idx"])
        ls, rs = int(m["left_shoulder"]), int(m["right_shoulder"])
        rw = int(round(RIM_MM / PROFILE_STEP_MM))
        rim = 0.5 * (np.max(z[max(0, ls - rw):ls + 1]) + np.max(z[rs:rs + rw + 1]))
        x0, z0 = x[a], rim
        ax.plot(x - x0, z - z0, ".", ms=1.5, color="#334155")
        (k1, m1), (k2, m2) = m["fit_left"], m["fit_right"]
        if k1 < 0 < k2:
            xl, xr = (rim - m1) / k1, (rim - m2) / k2
            xa = (m2 - m1) / (k1 - k2)
            za = k1 * xa + m1
            ax.plot([xl - x0, xa - x0], [rim - z0, za - z0], color=ACCENT, lw=1.2)
            ax.plot([xa - x0, xr - x0], [za - z0, rim - z0], color=ACCENT, lw=1.2)
        ax.axhline(0, color="#94a3b8", lw=0.6, ls="--")
        zz = z - z0
        ax.set_xlim(float(np.min(x - x0)), float(np.max(x - x0)))
        ax.set_ylim(float(np.min(zz)) - 0.4, max(float(np.max(zz)), 0.0) + 0.4)
        ax.set_aspect("equal", adjustable="box")
        ax.tick_params(labelsize=6)
        s = slices[i]
        ax.set_title(f"{LETTERS[k]}  {s['apex_vinkel_deg']:.1f}° · d {s['spårdjup_mm']:.2f} · b {s['spårbredd_mm']:.2f} mm",
                     fontsize=7)
    fig.supxlabel("Avstånd tvärs spåret (mm)", fontsize=8)
    fig.supylabel("Höjd rel. stenytan (mm)", fontsize=8)
    fig.tight_layout()
    return _png(fig)


def overlay_figure(groups: dict[str, list[dict]]) -> str | None:
    """Alla tvärsnitt överlagrade med botten i origo, median och interkvartilband per spårtyp."""
    data = {}
    for ft, slices in groups.items():
        curves = []
        for s in slices:
            f = _fit(s["profile"]) if s.get("profile") else None
            if f:
                x, z, m = f
                a = int(m["apex_idx"])
                curves.append((x - x[a], z - z[a]))
        if curves:
            data[ft] = curves
    if not data:
        return None
    plt = _plt()
    fig, axes = plt.subplots(1, len(data), figsize=(4.2 * len(data), 3.2), squeeze=False)
    for ax, (ft, curves) in zip(axes.flat, data.items()):
        span = min(8.0, max(float(np.max(np.abs(c[0]))) for c in curves))
        grid = np.linspace(-span, span, 161)
        Z = np.array([np.interp(grid, cx, cz, left=np.nan, right=np.nan) for cx, cz in curves])
        for cx, cz in curves:
            ax.plot(cx, cz, color="#94a3b8", lw=0.4, alpha=0.35)
        # Only where at least half of the profiles have data, so that the edges are not driven by a few curves
        enough = np.sum(np.isfinite(Z), axis=0) >= max(1, len(curves) / 2)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            med = np.where(enough, np.nanmedian(Z, axis=0), np.nan)
            q1 = np.where(enough, np.nanpercentile(Z, 25, axis=0), np.nan)
            q3 = np.where(enough, np.nanpercentile(Z, 75, axis=0), np.nan)
        col = GROUP_COLORS.get(ft, ACCENT)
        ax.fill_between(grid, q1, q3, color=col, alpha=0.3, lw=0)
        ax.plot(grid, med, color=col, lw=1.8)
        ax.set_xlim(-span, span)
        top = float(np.nanmax(q3)) if np.isfinite(q3).any() else 1.0
        ax.set_ylim(-0.2, top * 1.1)
        ax.set_aspect("equal")
        ax.set_title(f"{FEATURE_TITLES.get(ft, ft)} (n = {len(curves)})")
        ax.set_xlabel("Avstånd från botten (mm)")
        ax.set_ylabel("Höjd över botten (mm)")
    fig.tight_layout()
    return _png(fig)


def distributions_figure(groups: dict[str, list[dict]]) -> str:
    plt = _plt()
    fig, axes = plt.subplots(2, 4, figsize=(10, 4.6))
    for ax, m in zip(axes.flat, METRICS):
        per = {}
        for ft, slices in groups.items():
            vals = np.array([s[m] for s in slices if s.get(m) is not None], float)
            vals = vals[np.isfinite(vals)]
            if len(vals):
                per[ft] = vals
        if not per:
            continue
        everything = np.concatenate(list(per.values()))
        bins = np.histogram_bin_edges(everything, bins=min(20, max(6, len(everything) // 4)))
        for ft, vals in per.items():
            col = GROUP_COLORS.get(ft, ACCENT)
            ax.hist(vals, bins=bins, color=col, alpha=0.25, label=FEATURE_TITLES.get(ft, ft))
            ax.hist(vals, bins=bins, color=col, histtype="step", lw=1.2)
            ax.axvline(vals.mean(), color=col, lw=1.4, ls="--")
        ax.set_title(METRIC_LABELS[m])
        ax.tick_params(labelsize=6)
        ax.locator_params(axis="x", nbins=5)
    axes.flat[-1].axis("off")
    handles, labels = axes.flat[0].get_legend_handles_labels()
    if handles:
        axes.flat[-1].legend(handles, labels, loc="center", frameon=False)
    fig.tight_layout()
    return _png(fig)


def relations_figure(slices: list[dict]) -> str | None:
    if len(slices) < 5:
        return None
    plt = _plt()
    d = np.array([s["spårdjup_mm"] for s in slices])
    b = np.array([s["spårbredd_mm"] for s in slices])
    a = np.array([s["apex_vinkel_deg"] for s in slices])
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3.2))
    sc = ax1.scatter(b, d, c=a, cmap="viridis", s=10, edgecolors="black", linewidths=0.2)
    fig.colorbar(sc, ax=ax1, fraction=0.046, pad=0.02).set_label("V-vinkel (°)")
    ax1.set_xlabel("Spårbredd (mm)")
    ax1.set_ylabel("Spårdjup (mm)")
    ax2.scatter(d, a, s=10, color=ACCENT, alpha=0.7)
    if len(d) > 2 and np.ptp(d) > 0:
        k, m = np.polyfit(d, a, 1)
        xx = np.linspace(d.min(), d.max(), 20)
        ax2.plot(xx, k * xx + m, color="black", lw=1)
    ax2.set_xlabel("Spårdjup (mm)")
    ax2.set_ylabel("V-vinkel (°)")
    for ax in (ax1, ax2):
        ax.grid(alpha=0.3)
    fig.tight_layout()
    return _png(fig)


def groups_figure(groups: dict[str, list[dict]]) -> str | None:
    usable = {ft: s for ft, s in groups.items() if len(s) >= 3}
    if len(usable) < 2:
        return None
    plt = _plt()
    fig, axes = plt.subplots(1, 4, figsize=(10, 2.8))
    for ax, m in zip(axes, METRICS[:4]):
        data = [[s[m] for s in sl] for sl in usable.values()]
        bp = ax.boxplot(data, patch_artist=True, widths=0.6)
        for patch, ft in zip(bp["boxes"], usable):
            patch.set_facecolor(GROUP_COLORS.get(ft, ACCENT))
            patch.set_alpha(0.5)
        ax.set_xticks(range(1, len(usable) + 1))
        ax.set_xticklabels([FEATURE_TITLES.get(ft, ft) for ft in usable], fontsize=7)
        ax.set_title(METRIC_LABELS[m])
    fig.tight_layout()
    return _png(fig)


def corpus_figure(this: dict, reference: list[dict], signum: str) -> str | None:
    """Stenens medelvärden mot de uppmätta stenarna per ristare i korpusen."""
    if not reference:
        return None
    plt = _plt()
    carvers = sorted({r["group"] for r in reference})
    fig, axes = plt.subplots(1, 3, figsize=(10, 0.3 * len(carvers) + 1.6), sharey=True)
    for ax, (k, m) in zip(axes, [(0, "apex_vinkel_deg"), (2, "spårdjup_mm"), (3, "spårbredd_mm")]):
        for y, c in enumerate(carvers):
            vals = [r["values"][k] for r in reference if r["group"] == c]
            ax.scatter(vals, [y] * len(vals), color="#64748b", s=14)
            ax.plot([np.mean(vals)] * 2, [y - 0.3, y + 0.3], color="black", lw=1)
        ax.axvline(this[m], color=ACCENT, lw=1.6)
        ax.set_title(METRIC_LABELS[m])
        ax.grid(axis="x", alpha=0.3)
    axes[0].set_yticks(range(len(carvers)))
    axes[0].set_yticklabels([f"{c} ({sum(r['group'] == c for r in reference)})" for c in carvers], fontsize=7)
    fig.suptitle(f"Linjen: {signum}", fontsize=8, color=ACCENT)
    fig.tight_layout()
    return _png(fig)


def to_png_b64(data_url: str, max_side: int = 1600) -> str | None:
    from PIL import Image
    try:
        raw = base64.b64decode(data_url.split(",", 1)[1] if "," in data_url else data_url)
        img = Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception:
        return None
    img.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def rune_forms_figure(crops: list[dict]) -> str | None:
    from PIL import Image
    forms = []
    for c in crops:
        src = c.get("formPng") or c.get("imageBase64")
        if not src:
            continue
        try:
            raw = base64.b64decode(src.split(",", 1)[1] if "," in src else src)
            forms.append((c.get("tag") or "", Image.open(io.BytesIO(raw)).convert("L")))
        except Exception:
            continue
    if not forms:
        return None
    plt = _plt()
    cols = min(8, len(forms))
    rows = int(np.ceil(len(forms) / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(1.2 * cols, 1.45 * rows), squeeze=False)
    for ax in axes.flat:
        ax.axis("off")
    for ax, (tag, img) in zip(axes.flat, forms):
        ax.imshow(np.asarray(img), cmap="gray", vmin=0, vmax=255)
        ax.set_title(tag[:14], fontsize=7)
    fig.tight_layout()
    return _png(fig)


# ---- facts ---------------------------------------------------------------------------------

def _carvers_text(rec: dict | None) -> str:
    cs = (rec or {}).get("carvers") or []
    return ", ".join(f"{c['name']} ({c['kind']}{'?' if c['uncertain'] else ''})" for c in cs) or "–"


def _certain_carver(rec: dict | None) -> str | None:
    cs = [c["name"] for c in (rec or {}).get("carvers", []) if c["kind"] in ("S", "A") and not c["uncertain"]]
    return cs[0] if len(cs) == 1 else None


def build_facts(req: dict, rundata_lookup) -> dict:
    signum = (req.get("signum") or "").strip()
    rec = rundata_lookup(signum) if signum else None
    groups: dict[str, list[dict]] = defaultdict(list)
    provenances = []
    for a in req.get("analyses") or []:
        ft = a.get("feature_type") or "unknown"
        for s in a.get("slices") or []:
            if all(s.get(m) is not None and np.isfinite(s[m]) for m in METRICS):
                groups[ft].append(s)
        if a.get("provenance"):
            provenances.append(a["provenance"])
    order = [ft for ft in ("rune", "ornament", "unknown") if groups.get(ft)]
    groups = {ft: groups[ft] for ft in order}
    all_slices = [s for ft in order for s in groups[ft]]
    summaries = {ft: {m: summarize([s[m] for s in sl]) for m in METRICS} for ft, sl in groups.items()}

    comparison = None
    if len([ft for ft in groups if len(groups[ft]) >= 3]) >= 2 and "rune" in groups and "ornament" in groups:
        comparison = compare_stones(groups["rune"], groups["ornament"])

    # Comparison with the measured corpus: stones with exactly one certain carver, same feature type
    main_ft = order[0] if order else "rune"
    reference = []
    for e in req.get("corpus") or []:
        if (e.get("signum") or "").strip().lower() == signum.lower():
            continue
        if (e.get("feature_type") or "unknown") != main_ft:
            continue
        means = e.get("means") or {}
        if any(means.get(m) is None for m in METRICS):
            continue
        carver = _certain_carver(rundata_lookup(e.get("signum") or ""))
        if carver:
            reference.append({"group": carver, "label": e["signum"], "values": [float(means[m]) for m in METRICS]})
    this_means = {m: summaries[main_ft][m]["mean"] for m in METRICS} if order else None
    attribution = attribute(reference, [this_means[m] for m in METRICS]) if this_means and reference else None

    prov = provenances[-1] if provenances else {}
    # Open scan series (e.g. Kitzler Åhfeldt's on Zenodo): credit the scanner and cite the dataset
    scan, scan_source = scan_sources.fill_scan(req.get("scan") or {}, rec["signum"] if rec else signum)
    return {
        "signum": rec["signum"] if rec else signum,
        "rundata": rec,
        "meta": req.get("meta") or {},
        "scan": scan,
        "scan_source": scan_source,
        "condition": req.get("condition") or {},
        "groups": groups,
        "order": order,
        "all_slices": all_slices,
        "summaries": summaries,
        "comparison": comparison,
        "main_feature": main_ft,
        "this_means": this_means,
        "reference": reference,
        "attribution": attribution,
        "provenance": prov,
        "method_versions": sorted({pv.get("method_version", "okänd") for pv in provenances}) or ["okänd"],
        "counts": req.get("counts"),
        "two_d": req.get("two_d") or {},
        "synthesis": req.get("synthesis") or None,
        "reading": req.get("reading") or None,
        "workflow": req.get("workflow") or None,
        "date": datetime.date.today().isoformat(),
    }


def facts_text(f: dict) -> str:
    rec = f["rundata"] or {}
    lines = [f"Sten: {f['signum']}, {rec.get('place', '')} ({rec.get('parish', '')}), material {rec.get('material') or f['meta'].get('stone', '–')}",
             f"Rundata: ristare {_carvers_text(rec)}, stilgrupp {rec.get('style') or '–'}, datering {rec.get('dating') or '–'}",
             f"Translitterering: {rec.get('transliteration', '–')}",
             f"Översättning (Rundata, engelska): {rec.get('translation_en', '–')}",
             f"Vittring: {f['condition'].get('weathering') or f['meta'].get('weathering') or '–'}",
             f"Mätmetod: {', '.join(f['method_versions'])}; antal uppmätta tvärsnitt: {len(f['all_slices'])}"]
    for ft, summ in f["summaries"].items():
        parts = [f"{METRIC_LABELS[m]} {fmt(summ[m]['mean'], DIGITS[m])} ± {fmt(summ[m]['sd'], DIGITS[m])}" for m in METRICS]
        lines.append(f"{FEATURE_TITLES[ft]} (n = {summ['apex_vinkel_deg']['n']}): " + "; ".join(parts))
    if f["comparison"]:
        lines.append(f"Runor mot ornamentik, samlat permutationstest p {fmt_p(f['comparison']['overall'].get('p_value'))}")
    at = f["attribution"]
    if at and at.get("ranking"):
        rk = ", ".join(f"{r['group']} ({r['distance']:.2f})" for r in at["ranking"][:3])
        lines.append(f"Närmaste ristare i mätkorpusen (Mahalanobisavstånd): {rk}")
        ev = at.get("evaluation")
        if ev:
            lines.append(f"Korsvaliderad träffsäkerhet för attribueringen: {ev['top1_accuracy']:.0%} "
                         f"({ev['n_stones']} stenar, {ev['n_groups']} ristare, slumpnivå {ev['chance_top1']:.0%})")
    else:
        lines.append("Mätkorpusen räcker inte för en jämförelse med ristare (minst två ristare med två uppmätta stenar krävs).")
    rd = f.get("reading")
    rv = f.get("reading_validation") or {}
    if rd and rd.get("transliteration"):
        if rv.get("reliable", True):
            lines.append(f"Appens läsning av bilden (AI): {runes_to_latin(rd['transliteration'])}")
            if rd.get("comparison"):
                lines.append(f"Läsningen mot Rundata: {rd['comparison']}")
        else:
            lines.append(f"Appens blinda AI-läsning kunde inte bekräftas och får inte användas som läsning: {rv.get('text')}")
    sy = f.get("synthesis")
    if sy:
        if sy.get("outcome"):
            lines.append(f"Syntes mot litteraturen: {sy['outcome']['text']}")
        for c in (sy.get("candidates") or [])[:3]:
            lines.append(f"Kandidat {c['name']}: {c['strength']}a belägg (källor: {', '.join(c.get('sources') or [])})")
        for c in sy.get("conflicts") or []:
            lines.append(f"Motsägelse: {c}")
    rs = f.get("research") or {}
    if rs.get("purpose"):
        lines.append("Inskriftens syfte: " + ", ".join(f"{c['label']} ({round(c['base_rate'] * 100)} % av runstenarna)" for c in rs["purpose"]))
    for c in rs.get("carvers") or []:
        cats = "; ".join(f"{x['label']} {x['k']} av {x['n']}" for x in c["categories"])
        lines.append(f"{c['carver']}: stilgrupp {c['style']} i {c['style_k']} av {c['style_n']} inskrifter med stilgrupp"
                     + (f"; {cats}" if cats else ""))
    st = rs.get("status") or {}
    if st and not st.get("carver"):
        lines.append("Forskningsluckor: stenen saknar ristare i Rundata" + ("" if rs.get("hypothesis") else
                     " och finns inte bland de ortografiska hypoteserna."))
    r = f.get("r") or {}
    m = r.get("model")
    if m:
        lines.append("Attribueringsmodell i R (random forest, korsvaliderad 72 % träffsäkerhet på 18 ristare; sannolikheterna "
                     "är försiktiga): " + ", ".join(f"{x['carver']} {x['p']:.2f}" for x in m["top"][:3]) + f" ({m['source']})")
    c = r.get("cluster") or {}
    if c.get("included"):
        lines.append(f"Klustring i R: grupp {c['cluster']} av {c['k']} ({c['structure']} struktur)")
    ch = r.get("chronology") or {}
    if ch.get("included"):
        lines.append(f"Upplands seriation i R: percentil {round(ch['percentile'] * 100)}, ca {ch['estimate']} "
                     f"({ch['lo']}–{ch['hi']}); ordningen säkrare än årtalet")
    land = r.get("landscape") or {}
    if land.get("view"):
        lines.append(f"Landskap (R): synlig från {round(land['view']['share_2km'] * 100)} % av ytan inom 2 km, synligare än "
                     f"{round((land['view'].get('percentile') or 0) * 100)} % av slumpvisa platser i närheten")
        if land.get("routes"):
            rt = land["routes"]
            lines.append(f"Landskap (R): {rt['stone_to_route_km']:.2f} km till simulerade vägar mellan grannplatser, "
                         f"slumpvisa punkter median {rt['random_median_km']:.2f} km")
    td = f["two_d"].get("result") or {}
    if td.get("predicted_style"):
        lines.append(f"AI-bedömning av stilgrupp från bild (okalibrerad): {td['predicted_style']}")
    return "\n".join(lines)


# ---- document ------------------------------------------------------------------------------

def _summary_table(f: dict) -> dict:
    rows = []
    for ft, summ in f["summaries"].items():
        for m in METRICS:
            s = summ[m]
            ci = s.get("ci95")
            rows.append([FEATURE_TITLES[ft], METRIC_LABELS[m], str(s["n"]), fmt(s["mean"], DIGITS[m]), fmt(s["sd"], DIGITS[m]),
                         f"{fmt(ci[0], DIGITS[m])}–{fmt(ci[1], DIGITS[m])}" if ci else "–",
                         f"{fmt(s['min'], DIGITS[m])}–{fmt(s['max'], DIGITS[m])}"])
    return rows


def _pick_profiles(slices: list[dict], k: int = 12) -> list[int]:
    idx = [i for i, s in enumerate(slices) if s.get("profile")]
    if not idx:
        return []
    idx.sort(key=lambda i: slices[i]["apex_vinkel_deg"])
    if len(idx) <= k:
        return idx
    return [idx[int(round(j))] for j in np.linspace(0, len(idx) - 1, k)]


def _flat_params(params: dict) -> list[list[str]]:
    rows = []
    for k, v in (params or {}).items():
        if isinstance(v, dict):
            continue
        if isinstance(v, (list, tuple)):
            v = ", ".join(fmt(x, 3) if isinstance(x, float) else str(x) for x in v)
        elif isinstance(v, float):
            v = fmt(v, 3)
        rows.append([str(k), str(v)])
    return rows


def workflow_appendix(wf: dict, signum: str, fig, tab) -> list[dict]:
    """Bilaga B: hur analysen gjordes – arbetsgång, spåranalysens känslighet, granskningsbilder, alla
    blinda läsningar och de fel eller begränsningar som uppstod. Gör artikeln granskningsbar."""
    out = [h(1, "Bilaga B. Arbetsgång"),
           p(wf.get("intro") or (
               f"Analysen gjordes {wf.get('date', '')} med Vitkis fullständiga stenanalys: bilder ur skanningen, "
               "automatisk spåranalys med känslighetsanalys, 2D-bildanalys, blind läsning jämförd med Rundata, syntes och "
               "stenrapport. Varje steg använder samma beräkningar som de enskilda verktygen i appen."))]
    steps = wf.get("steps") or []
    if steps:
        out.append(tab(["Steg", "Utfall"], [[st.get("name", ""), st.get("result", "")] for st in steps],
                       "Arbetsgångens steg och utfall."))
    sens = wf.get("sensitivity") or []
    if sens:
        out.append(h(2, "B.1 Spåranalysens känslighet"))
        out.append(p("Den automatiska spåranalysen kördes med flera känsligheter. Känsligheten styr tröskeln för vad som "
                     "räknas som ett spår (känslighet × brusnivå, minst 0,3 mm). Artikelns huvudanalys använder "
                     f"känslighet {sens[0].get('sensitivity')}."))
        out.append(tab(["Känslighet", "Tröskel (mm)", "Kandidater", "Godkända", "För breda partier (mm²)", "V-vinkel (°)",
                        "Djup (mm)", "Bredd (mm)"],
                       [[str(x.get("sensitivity")), fmt(x.get("threshold_mm"), 2), str(x.get("candidates", "–")),
                         str(x.get("accepted", "–")), fmt(x.get("wide_area_mm2"), 0),
                         f"{fmt(x.get('angle_mean'), 1)} ± {fmt(x.get('angle_sd'), 1)}", fmt(x.get("depth_mean"), 2),
                         fmt(x.get("width_mean"), 2)] for x in sens],
                       f"Automatisk spåranalys av {signum} med olika känslighet."))
        for x in sens:
            img = to_png_b64(x["review_png"], 1800) if x.get("review_png") else None
            if img:
                out.append(fig(img, f"{signum}. Granskningsbild, känslighet {x.get('sensitivity')}: godkända snitt (färgade "
                                    "efter V-vinkel), spår (rött) och partier bedömda som för breda för ett huggspår (blått), "
                                    "som inte mäts.", f"granskning-k{x.get('sensitivity')}"))
    if wf.get("relief_png"):
        img = to_png_b64(wf["relief_png"], 1800)
        if img:
            out.append(fig(img, f"{signum}. Relief ur skanningen: det mörkaste av fyra strykljus, så att varje spår blir "
                                "mörkt oavsett riktning.", "relief"))
    if wf.get("two_d_reasoning"):
        out.append(h(2, "B.2 2D-bildanalys"))
        out.append(p(f"Bildanalysens motivering (förkortad): {wf['two_d_reasoning'][:600].rstrip()} …", ai=True))
    readings = wf.get("readings") or []
    if readings:
        out.append(h(2, "B.3 Blinda läsningar"))
        out.append(p("Språkmodellen läste runorna utan att få veta signumet. Jämförelsen med Rundata är framräknad utan AI. "
                     "Den första läsningen prövas i resultatavsnittet och redovisas där bara om den bekräftas."))
        rows = []
        for r in readings:
            t = runes_to_latin(r.get("transliteration") or "")
            c = r.get("reading_comparison") or {}
            pc = lambda v: f"{round(v * 100)} %" if isinstance(v, (int, float)) else "–"
            rows.append([r.get("label", ""), (t[:70] + " …") if len(t) > 70 else (t or r.get("error") or "–"),
                         pc(c.get("char_agreement")), pc(c.get("word_agreement")), pc(c.get("coverage")),
                         (r.get("validation") or {}).get("status", "–")])
        out.append(tab(["Läsning", "Translitterering (början)", "Runor som stämmer", "Ord som stämmer", "Täckning", "Status"], rows,
                       f"Blinda AI-läsningar av {signum} jämförda med Rundatas läsning."))
        found = [r["validation"]["text"] for r in readings if (r.get("validation") or {}).get("status") == "annan inskrift"]
        if found:
            out.append(p(" ".join(dict.fromkeys(found))))
    notes = wf.get("notes") or []
    if notes:
        out.append(h(2, "B.4 Fel och begränsningar"))
        out.append(bullets(notes))
    return out


def research_blocks(rs: dict, signum: str, tab, synthesis: dict | None) -> list[dict]:
    """Inskriftens syfte och stenens läge i Forskningsluckor (Rundatas täckning, hypoteser, prioriteringar)."""
    out = []
    purpose = rs.get("purpose") or []
    if purpose:
        out.append(h(2, "Inskriftens syfte"))
        out.append(p(f"{signum} hör enligt appens katalogisering till "
                     + ", ".join(f"{c['label'].lower()} ({c['definition'][0].lower() + c['definition'][1:].rstrip('.')}; "
                                 f"{round(c['base_rate'] * 100)} % av de vikingatida runstenarna med text)" for c in purpose)
                     + ". Kategorierna sätts med regler på Rundatas normalisering och översättning."))
    st, prov = rs["status"], rs["province"]
    out.append(h(2, "Stenen i forskningsläget"))
    yes = lambda b: "ja" if b else "nej"
    rows = [
        ["Ristare i Rundata", st["carver_text"] or "ingen angiven"],
        ["Säker stilgrupp", f"{yes(st['style'])}{' (' + st['style_text'] + ')' if st['style_text'] else ''}"],
        ["Osäker tolkning", yes(st["uncertain_interpretation"])],
        ["Daterad med årtal", yes(st["dated_by_year"])],
        ["Försvunnen", yes(st["lost"])],
    ]
    if prov.get("total"):
        rows.append([f"{prov['name']}: runstenar med ristare", f"{prov['carver']} av {prov['total']} ({round(100 * prov['carver'] / prov['total'])} %)"
                     + (" – ristaruppgifterna bygger främst på Axelson (1993)" if prov.get("axelson") else "")])
        rows.append([f"{prov['name']}: osäkert tolkade / försvunna", f"{prov['uncertain_interpretation']} / {prov['lost']}"])
    hyp, rec_ = rs.get("hypothesis"), rs.get("reconsider")
    if hyp:
        rows.append(["Ortografisk hypotes", f"{hyp['carver']} (likhet {fmt(hyp['similarity'], 2)}, precision "
                     f"{round((hyp.get('carver_precision') or 0) * 100)} %)"])
    if rec_:
        rows.append(["Att ompröva", f"Rundata anger {', '.join(rec_.get('attributed_to') or [])}; ortografin pekar på {rec_['carver']}"])
    for pr in rs.get("priorities") or []:
        rows.append(["Mätprioritering", f"föreslås för att mäta {pr['carver']} ({pr['inscriptions']} inskrifter, {pr['measured']} uppmätta)"])
    for fd in rs.get("findings") or []:
        rows.append([f"Mot forskningen ({fd['method']})", f"{fd['verdict']}: {fd['assessment']}"])
    out.append(tab(["", ""], rows, f"{signum} i Forskningsluckor."))
    if not st["carver"] and not hyp:
        o = ((synthesis or {}).get("evidence") or {}).get("orthography") or {}
        r = o.get("ranking") or []
        why = ""
        if len(r) >= 2:
            why = (f" Den ortografiska jämförelsen skiljer inte tydligt mellan ristarna: {r[0]['carver']} "
                   f"{fmt(r[0]['similarity'], 2)} mot {r[1]['carver']} {fmt(r[1]['similarity'], 2)}, en marginal under 0,05.")
        out.append(p("Stenen saknar ristare i Rundata men finns inte bland Forskningsluckors ortografiska hypoteser, som "
                     "kräver likhet minst 0,6, marginal minst 0,05 och minst åtta läsbara ord." + why))
    out.append(p(rs.get("source_note", "")))
    return out


def build_document(f: dict, author: str, institution: str, ai: dict | None, surface: Surface | None,
                   title: str | None = None) -> list[dict]:
    ai = ai or {}
    rec = f["rundata"] or {}
    meta, scan, cond = f["meta"], f["scan"], f["condition"]
    signum = f["signum"] or meta.get("text") or "Okänd sten"
    place = rec.get("place") or meta.get("location") or ""
    title = title or f"{signum}{', ' + place if place else ''}: huggteknik dokumenterad med 3D-skanning"
    groups, order = f["groups"], f["order"]
    all_slices = f["all_slices"]
    n_fig = 0
    n_tab = 0

    def fig(png, caption, slug):
        nonlocal n_fig
        n_fig += 1
        return figure(png, f"Figur {n_fig}. {caption}", f"figur{n_fig}_{slug}.png")

    def tab(headers, rows, caption):
        nonlocal n_tab
        n_tab += 1
        return table(headers, rows, f"Tabell {n_tab}. {caption}")

    blocks: list[dict] = [{"type": "title", "text": title, "author": author, "institution": institution, "date": f["date"]}]

    # Abstract and introduction
    main = f["summaries"].get(f["main_feature"]) if order else None
    default_abstract = (
        f"Artikeln redovisar en 3D-baserad analys av huggspåren på {signum}"
        + (f" ({place})" if place else "") + ". "
        + (f"Totalt {len(all_slices)} tvärsnitt mättes; för {FEATURE_NAMES[f['main_feature']]} är V-vinkeln i medel "
           f"{fmt(main['apex_vinkel_deg']['mean'], 1)}° (SD {fmt(main['apex_vinkel_deg']['sd'], 1)}) och spårdjupet "
           f"{fmt(main['spårdjup_mm']['mean'], 2)} mm." if main else "Inga godkända tvärsnitt fanns.")
    )
    blocks += [h(1, "Sammanfattning"), p(ai.get("abstract") or default_abstract, ai=bool(ai.get("abstract")))]
    blocks += [h(1, "1. Inledning"),
               p(ai.get("introduction") or
                 "Syftet är att dokumentera huggtekniken på stenen med mätbara spårvariabler ur en 3D-skanning, så att "
                 "den kan jämföras med andra stenar och prövas mot tidigare attribueringar. Frågeställningarna "
                 "formuleras av författaren.", ai=bool(ai.get("introduction")))]

    # 2. The stone and the inscription
    blocks.append(h(1, "2. Stenen och inskriften"))
    loc = ", ".join(x for x in [rec.get("place"), rec.get("parish"), rec.get("district"), rec.get("municipality")] if x)
    facts_rows = [
        ["Signum", signum],
        ["Plats", loc or meta.get("location") or "–"],
        ["Placering", rec.get("placement") or "–"],
        ["Föremål och material", ", ".join(x for x in [rec.get("object"), rec.get("material") or meta.get("stone")] if x) or "–"],
        ["Ristare (Rundata)", _carvers_text(rec)],
        ["Stilgrupp (Rundata)", (rec.get("style") or "–") + (" (osäker)" if rec.get("style_uncertain") else "")],
        ["Datering (Rundata)", PERIODS.get(rec.get("dating") or "", rec.get("dating")) or meta.get("period") or "–"],
        ["Ornamentik", meta.get("ornamentation") or "–"],
        ["Skick", ", ".join(x for x in [
            f"vittring {cond.get('weathering') or meta.get('weathering')}" if (cond.get("weathering") or meta.get("weathering")) else "",
            "lav" if cond.get("lichen") else "", "ommålad" if cond.get("paint") else "", cond.get("notes") or ""] if x) or "–"],
    ]
    if rec.get("flags", {}).get("lost"):
        facts_rows.append(["Anmärkning", "Stenen är försvunnen enligt Rundata."])
    if rec.get("other"):
        facts_rows.append(["Övrigt (Rundata)", rec["other"]])
    blocks.append(tab(["", ""], facts_rows, f"Uppgifter om {signum}."))
    geo = f.get("geology")
    if geo and geo.get("verdict") != "okänt":
        blocks.append(p(f"Berggrund: {geo['text']} {geo['caveat']} (Källa: {geo['source']})"))
    if rec.get("transliteration"):
        blocks.append(h(2, "Inskriften"))
        blocks.append(inscription(rec.get("transliteration", ""), _names(rec.get("normalization", "")),
                                  _names(rec.get("normalization_ows", "")), rec.get("translation_en", ""),
                                  "Samnordisk runtextdatabas"))
        blocks.append(p("Translitterering i fetstil och normalisering till runsvenska respektive fornvästnordiska i kursiv, "
                        "enligt Samnordisk runtextdatabas. Översättningen är Rundatas engelska. Ristare anges med S "
                        "(signerad), A (attribuerad); frågetecken markerar en osäker uppgift."))
    sri = sri_reference(signum)
    blocks.append(p(f"Inskriften är utgiven i Sveriges runinskrifter ({sri_short(sri)}). Tidigare tolkningar och attribueringar bör kontrolleras där och i senare "
                    "litteratur innan resultaten nedan ställs mot dem." if sri else
                    "Hänvisa till stenens utgåva och senare litteratur här."))
    rs = f.get("research")
    if rs:
        blocks += research_blocks(rs, signum, tab, f.get("synthesis"))

    # 3. Material and method
    blocks.append(h(1, "3. Material och metod"))
    blocks.append(h(2, "3.1 3D-dokumentation"))
    pm = f["provenance"].get("mesh") or {}
    extent = pm.get("extent_mm") or []
    scan_rows = [
        ["Skanner", scan.get("device") or "– (fyll i)"],
        ["Skannat av, datum", ", ".join(x for x in [scan.get("scanned_by"), scan.get("date")] if x) or "– (fyll i)"],
        ["Punktavstånd / upplösning", f"{fmt(scan['resolution_mm'], 2)} mm" if scan.get("resolution_mm") else "– (fyll i)"],
        ["Noggrannhet", f"{fmt(scan['accuracy_mm'], 2)} mm" if scan.get("accuracy_mm") else "– (fyll i)"],
        ["Modellfil", pm.get("filename") or "–"],
        ["Hörn / trianglar", f"{pm.get('vertices', '–')} / {pm.get('faces', '–')}"],
        ["Utsträckning", " × ".join(fmt(v, 0) for v in extent) + " mm" if extent else "–"],
        ["Kontrollsumma (SHA-256)", pm.get("sha256") or "–"],
        ["Publicerad skanning", (f"{scan['url']} ({f['scan_source']['short']})" if f.get("scan_source") else scan.get("url")) or "–"],
        ["Licens för skanningen", scan.get("license") or "–"],
    ]
    blocks.append(tab(["", ""], scan_rows, "3D-dokumentation och paradata."))
    blocks.append(p("Bilderna av ytan i figurerna är räknade direkt ur 3D-modellen: modellen projiceras på den ristade "
                    "sidans plan till ett höjdfält, som belyses digitalt (strykljus) eller jämförs med en rekonstruerad "
                    "stenyta (morfologisk stängning med 20 mm skala) för att visa djupet. Ingen bild är retuscherad."))
    blocks.append(h(2, "3.2 Mätning av huggspår"))
    prov = f["provenance"]
    mode = (prov.get("parameters") or {}).get("mode")
    runes_only = bool((prov.get("parameters") or {}).get("runes_only"))
    blocks.append(p(
        f"Huggspåren mättes med Vitki {prov.get('version', '')} (mätmetod {', '.join(f['method_versions'])}). "
        + ("Spåren hittades automatiskt som fördjupningar under den rekonstruerade stenytan; tvärsnitt lades med jämna "
           "mellanrum längs spårens mittlinjer vinkelrätt mot spårets riktning, och varje snitt granskades mot "
           "kvalitetskriterier (väggpassning, rimlig vinkel, djup över brusnivån, spårkanter inom snittet). "
           + ("Bara spår som känns igen som runor mättes: mittlinjerna delades i streck, och bara raka, jämnbreda "
              "streck av runors längd som står i rader – på stenar med slingband inne i banden – räknades som runor; "
              "slinglinjer, ornamentik och oregelbundna spår (möjliga sprickor) sorterades bort. "
              if runes_only else "")
           if mode == "automatic" else
           "Tvärsnitt lades vinkelrätt mot spåret i markerade spårpartier. ")
        + "I varje tvärsnitt anpassas spårväggarna med linjär regression mellan 20 och 80 procent av spårdjupet; "
          "V-vinkeln är öppningsvinkeln mellan väggarnas linjer, bredden mäts där linjerna når stenytans nivå och "
          "djupet från spårkanten till botten. Bottenradien är krökningsradien hos en parabel anpassad kring botten "
          "och ytråheten medelavvikelsen från väggarnas linjer. Metoden är validerad på syntetiska spår med kända "
          "mått (vinkelfel inom ±0,6°). Runor och ornamentik redovisas var för sig."))
    counts = f.get("counts")
    if counts:
        rr = [[k, str(v)] for k, v in (counts.get("rejection_reasons") or {}).items()]
        blocks.append(tab(["Utfall", "Antal snitt"],
                          [["Kandidater", str(counts.get("candidates", "–"))], ["Godkända", str(counts.get("accepted", "–"))]]
                          + ([["Igenkända runor", str(counts["runes_identified"])], ["Runor med godkända snitt", str(counts["runes_measured"])]]
                             if counts.get("runes_identified") is not None else [])
                          + [[f"Underkända: {k}", v] for k, v in rr],
                          "Kvalitetskontroll av de automatiska tvärsnitten."))
    params = _flat_params(prov.get("parameters") or {})
    if params:
        blocks.append(tab(["Parameter", "Värde"], params, "Analysparametrar (för reproducerbarhet)."))
    blocks.append(h(2, "3.3 Statistik"))
    blocks.append(p("Varje mått sammanfattas med medelvärde, standardavvikelse och 95 % konfidensintervall för "
                    "medelvärdet (t-fördelning). Runor och ornamentik jämförs med permutationstest per mått "
                    "(Bonferroni-justerat) och samlat. Jämförelsen med andra stenar använder stenarnas medelvärden i "
                    "Vitkis mätkorpus och Mahalanobisavstånd till ristarnas medelvärden, med "
                    "lämna-en-ute-korsvalidering av träffsäkerheten; bara stenar med en säker signerad eller "
                    "attribuerad ristare i Rundata används som referens."))
    rr_ = f.get("r") if (f.get("r") and not f["r"].get("error")) else None
    if rr_:
        blocks += r_report.method_blocks(rr_)

    # 4. Results
    blocks.append(h(1, "4. Resultat"))
    marked: dict[int, str] = {}
    picks = _pick_profiles(all_slices)
    for k, i in enumerate(picks):
        marked[i] = LETTERS[k]
    if surface is not None:
        blocks.append(h(2, "4.1 Ytan"))
        blocks.append(fig(raking_figure(surface),
                          f"{signum}. Digitalt strykljus från fyra riktningar (20° över ytan), beräknat ur 3D-modellen.",
                          "strykljus"))
        blocks.append(fig(depth_figure(surface),
                          f"{signum}. Djup under den rekonstruerade stenytan; mörkare = djupare. Kantzonen (10 mm), där "
                          "referensytan är osäker, är utelämnad. Kartan visar formen; spårdjupen i tabellerna är mätta i "
                          "tvärsnitten och är något större, eftersom referensytan är utjämnad.", "djupkarta"))
        if any(s.get("point") for s in all_slices):
            blocks.append(fig(overview_figure(surface, all_slices, marked),
                              f"{signum}. Tvärsnittens positioner färgade efter V-vinkel. Bokstäverna hänvisar till "
                              "profilerna i figuren över representativa tvärsnitt.", "snittpositioner"))
            sp = spatial_figure(surface, all_slices)
            if sp:
                blocks.append(fig(sp, f"{signum}. Spårdjup, spårbredd och ytråhet per tvärsnitt över ytan.", "matt-over-ytan"))
    else:
        blocks.append(p("Bilderna av ytan saknas: 3D-modellen fanns inte i analysmotorns minne när rapporten skapades. "
                        "Ladda in skanningen i 3D-vyn och skapa rapporten igen för att få med dem."))

    blocks.append(h(2, "4.2 Spårprofiler"))
    pf = profiles_figure(all_slices, picks)
    if pf:
        blocks.append(fig(pf, f"{signum}. Representativa tvärsnitt, ordnade från minsta till största V-vinkel. Punkter: "
                              "uppmätt profil; röda linjer: anpassade spårväggar; streckad linje: stenytans nivå. "
                              "Lika skala på axlarna.", "tvarsnitt"))
    of = overlay_figure(groups)
    if of:
        blocks.append(fig(of, f"{signum}. Alla tvärsnitt överlagrade med botten i origo; median (heldragen) och "
                              "interkvartilområde (skuggat).", "profiler-overlagrade"))
    if not pf and not of:
        blocks.append(p("Råprofilerna saknas i underlaget, så tvärsnitten kan inte visas."))

    blocks.append(h(2, "4.3 Spårmått"))
    if all_slices:
        blocks.append(tab(["Spår", "Mått", "n", "Medel", "SD", "95 % KI", "Min–max"], _summary_table(f),
                          f"Spårmått för {signum}."))
        for ft, summ in f["summaries"].items():
            a, d, b = summ["apex_vinkel_deg"], summ["spårdjup_mm"], summ["spårbredd_mm"]
            ci = a.get("ci95")
            blocks.append(p(
                f"{FEATURE_TITLES[ft]} ({a['n']} tvärsnitt): V-vinkeln är i medel {fmt(a['mean'], 1)}° "
                f"(SD {fmt(a['sd'], 1)}°" + (f", 95 % KI {fmt(ci[0], 1)}–{fmt(ci[1], 1)}°" if ci else "")
                + f", spridning {fmt(a['min'], 1)}–{fmt(a['max'], 1)}°), spårdjupet {fmt(d['mean'], 2)} mm "
                f"(SD {fmt(d['sd'], 2)}) och spårbredden {fmt(b['mean'], 2)} mm (SD {fmt(b['sd'], 2)}); "
                f"se tabell {n_tab}."))
        blocks.append(fig(distributions_figure(groups), f"{signum}. Fördelning av måtten per tvärsnitt; lodrät linje = medelvärde.",
                          "fordelningar"))
        rf = relations_figure(all_slices)
        if rf:
            blocks.append(fig(rf, f"{signum}. Samband mellan spårbredd, spårdjup och V-vinkel per tvärsnitt.", "samband"))
    else:
        blocks.append(p("Underlaget innehåller inga godkända tvärsnitt."))

    if f["comparison"]:
        blocks.append(h(2, "4.4 Runor och ornamentik"))
        gf = groups_figure(groups)
        if gf:
            blocks.append(fig(gf, f"{signum}. Runor och ornamentik jämförda.", "runor-ornamentik"))
        cmp = f["comparison"]
        blocks.append(tab(["Mått", "Runor", "Ornamentik", "p", "p (justerat)"],
                          [[r["label"], fmt(r["a"]["mean"], DIGITS[r["metric"]]), fmt(r["b"]["mean"], DIGITS[r["metric"]]),
                            fmt_p(r["p_value"]), fmt_p(r["p_adjusted"])] for r in cmp["per_metric"]],
                          "Permutationstest runor mot ornamentik."))
        pv = cmp["overall"].get("p_value")
        blocks.append(p(f"Samlat test: p {fmt_p(pv) if pv is not None and pv < 0.001 else '= ' + fmt_p(pv)}. "
                        f"{cmp['interpretation']}"))

    blocks.append(h(2, "4.5 Jämförelse med andra stenar"))
    at = f["attribution"]
    if f["reference"] and f["this_means"]:
        cf = corpus_figure(f["this_means"], f["reference"], signum)
        if cf:
            blocks.append(fig(cf, f"{signum} (linjen) jämförd med stenar med säker ristare i mätkorpusen; punkter = "
                                  "stenarnas medelvärden, streck = ristarens medelvärde. Antal stenar inom parentes.",
                              "jamforelse-korpus"))
    if at and at.get("ranking"):
        blocks.append(tab(["Ristare", "Stenar", "Mahalanobisavstånd"],
                          [[r["group"], str(r["n"]), fmt(r["distance"], 2)] for r in at["ranking"][:8]],
                          "Avstånd från stenens medelvärden till ristarnas i mätkorpusen (kortare = mer likt)."))
        ev = at.get("evaluation")
        if ev:
            blocks.append(p(f"Med lämna-en-ute-korsvalidering hamnar rätt ristare först för {ev['top1_accuracy'] * 100:.0f} "
                            f"procent av {ev['n_stones']} referensstenar ({ev['n_groups']} ristare, slumpnivå "
                            f"{ev['chance_top1'] * 100:.0f} procent). Rangordningen ovan bör läsas mot den siffran."))
    else:
        blocks.append(p((at or {}).get("note") or
                        "Mätkorpusen innehåller ännu för få stenar med säker ristare för en jämförelse."))

    td = f["two_d"]
    td_res = td.get("result") or {}
    img = to_png_b64(td["image"]) if td.get("image") else None
    forms = rune_forms_figure(td.get("crops") or [])
    if img or td_res or forms:
        blocks.append(h(2, "4.6 Bildanalys"))
        if img:
            blocks.append(fig(img, f"{signum}. {td.get('caption') or 'Bild använd i 2D-analysen.'}", "bild"))
        if td_res.get("predicted_style"):
            agree = rec.get("style") and td_res["predicted_style"] == rec.get("style")
            blocks.append(p(f"En språkmodell bedömde stilgruppen från bilden som {td_res['predicted_style']} "
                            f"(egen, okalibrerad säkerhet {td_res.get('confidence', '–')} %). "
                            + (f"Rundata anger {rec['style']}, " + ("vilket stämmer överens." if agree else "vilket avviker.")
                               if rec.get("style") else "Rundata anger ingen stilgrupp.")
                            + " Bedömningen är en hypotes och inte ett mätresultat."))
        if forms:
            blocks.append(fig(forms, f"{signum}. Normaliserade runformer ur bilden (svartvita, lika stora), "
                                     "underlag för formjämförelser.", "runformer"))

    rd = f.get("reading")
    rv = f.get("reading_validation") or {}
    if rd and rd.get("transliteration") and not rv.get("reliable", True):
        # An unconfirmed AI reading is never presented as the stone's text
        blocks.append(h(2, "4.7 Läsning av bilden"))
        blocks.append(p("En språkmodell läste runorna från bilden utan tillgång till tidigare läsningar (blind läsning). "
                        "Läsningen prövades utan AI mot Rundata, mot alla kända inskrifter och mot andra läsningar av samma "
                        f"bild. {rv.get('text', '')}"))
        blocks.append(p("Den blinda läsningen återges därför inte som läsning av stenen, och ingen normalisering, "
                        "översättning eller fonetisk rekonstruktion redovisas. Stenens text i avsnitt 2 är Rundatas."
                        + (" Alla läsningar och jämförelser finns i bilaga B." if f.get("workflow") else "")
                        + " Reliefbilderna ur skanningen (figur 1 och 2) är ett bättre underlag för en runologs läsning."))
    elif rd and rd.get("transliteration"):
        blocks.append(h(2, "4.7 Läsning av bilden"))
        blocks.append(p("Runorna lästes från bilden av en språkmodell utan tillgång till tidigare läsningar ("
                        "blind läsning); normalisering, översättning och fonetisk rekonstruktion är modellens "
                        "tolkning. Jämförelsen med Rundata och kontrollen av ordformerna är framräknade utan AI."
                        + (" Läsningen har därefter rättats manuellt." if rd.get("corrected") else "")
                        + (f" {rv['text']}" if rv.get("text") else "")))
        blocks.append(inscription(runes_to_latin(rd.get("transliteration", "")), rd.get("normalization", ""), "",
                                  rd.get("translation", ""), "appens läsning (AI)"))
        if rd.get("comparison"):
            blocks.append(p(rd["comparison"]))
        cmp = rd.get("reading_comparison") or {}
        diffs = [sg for sg in cmp.get("segments", []) if sg["op"] != "equal"]
        if diffs:
            label = {"replace": "olika", "delete": "bara vår läsning", "insert": "bara Rundata"}
            blocks.append(tab(["Skillnad", "Vår läsning", "Rundata"],
                              [[label.get(sg["op"], sg["op"]), " ".join(sg["ours"]) or "–", " ".join(sg["rundata"]) or "–"]
                               for sg in diffs[:40]],
                              f"Skillnader mellan vår läsning och Rundatas för {signum} (ord för ord)."))
        fc = rd.get("form_check") or {}
        if fc.get("items"):
            missing = sorted({i["form"] for i in fc["items"] if not i["attested"]})
            blocks.append(p(f"{fc['attested']} av {fc['total']} normaliserade ordformer är belagda i Rundatas "
                            "vikingatida inskrifter." + (f" Inte belagda: {', '.join(missing)}." if missing else "")))
        if rd.get("phonetic_ipa"):
            blocks.append(p(f"Fonetisk rekonstruktion (AI): [{rd['phonetic_ipa'].strip().strip('[]/').strip()}]", ai=True))
        if rd.get("sound_laws_applied"):
            blocks.append(p("Ljudlagar som modellen anger: " + "; ".join(rd["sound_laws_applied"]) + ".", ai=True))

    sy = f.get("synthesis")
    if sy and sy.get("candidates") is not None:
        blocks.append(h(2, "4.8 Attribuering"))
        blocks.append(p("Beläggen från Rundata, ortografisk stilometri och huggteknik vägs samman; ortografi och "
                        "huggteknik vägs efter metodens korsvaliderade träffsäkerhet i fallet. Kandidaterna prövas mot "
                        "geografi, ristarens stilgrupper och, där ristarens stenar är uppmätta, sten mot sten med "
                        "permutationstest. Inga sannolikheter anges."))
        if sy.get("outcome"):
            blocks.append(p(sy["outcome"]["text"]))
        cands = sy.get("candidates") or []
        if cands:
            blocks.append(tab(["Ristare", "Belägg", "Poäng", "Källor", "Mot Rundata"],
                              [[c["name"], c["strength"], fmt(c.get("score"), 1), ", ".join(c.get("sources") or []),
                                (c.get("literature") or {}).get("verdict", "–")] for c in cands],
                              f"Attribueringskandidater för {signum}."))
            checks = []
            for c in cands[:3]:
                for key, label in (("geography", "geografi"), ("styles", "stilgrupper"), ("material", "bergart"),
                                   ("language", "språkdrag"), ("stone_tests", "sten mot sten")):
                    if c.get(key):
                        checks.append(f"{c['name']}, {label}: {c[key]['text']}")
            if checks:
                blocks.append(bullets(checks))
        cand_rows = (rs or {}).get("carvers") or []
        if cand_rows:
            cats = [c["label"] for c in (rs.get("purpose") or [])]
            pc = lambda k, n: f"{k} av {n} ({round(100 * k / n)} %)" if n else "–"
            blocks.append(tab(["Ristare", f"Stilgrupp {cand_rows[0]['style'] or '–'}"] + cats,
                              [[c["carver"], pc(c["style_k"], c["style_n"])]
                               + [next((pc(x["k"], x["n"]) for x in c["categories"] if x["label"] == lab), "–") for lab in cats]
                               for c in cand_rows],
                              f"Hur ofta kandidaterna ristade i {signum}s stilgrupp och inskriftstyp (säkra inskrifter i "
                              "Rundata; stilgrupp av inskrifter med säker stilgrupp, typ av vikingatida runstenar med text)."))
        if rr_:
            blocks += r_report.attribution_blocks(rr_, signum, fig, tab)
        if sy.get("conflicts"):
            blocks.append(p("Motsägelser mellan källorna:"))
            blocks.append(bullets(sy["conflicts"]))
        if sy.get("missing"):
            blocks.append(p("Belägg som saknas:"))
            blocks.append(bullets(sy["missing"]))

    if rr_:
        if not (sy and sy.get("candidates") is not None):
            blocks.append(h(2, "4.8 Attribuering"))
            blocks += r_report.attribution_blocks(rr_, signum, fig, tab)
        blocks += r_report.corpus_blocks(rr_, signum, fig, tab)
        blocks += r_report.landscape_blocks(rr_.get("landscape"), signum, fig, tab)

    # 5. Discussion
    blocks.append(h(1, "5. Diskussion"))
    blocks.append(p(ai.get("discussion") or "Diskussionen skrivs av författaren utifrån resultaten ovan.",
                    ai=bool(ai.get("discussion"))))
    blocks.append(h(2, "Källkritik och begränsningar"))
    blocks.append(bullets([
        "Spårmåtten påverkas av vittring, bergart, lav, ommålning och skanningens upplösning.",
        "Var tvärsnitten läggs påverkar resultatet; positionerna redovisas därför i figurerna.",
        "Ristaruppgifterna i Rundata är hypoteser i litteraturen och inte facit.",
        "Måtten är inte verifierade som likvärdiga med Groove Measure-variablerna i Kitzler Åhfeldts studier; "
        "direkta jämförelser kräver att samma referensstenar mäts med båda metoderna.",
    ] + (r_report.LIMITATIONS if rr_ else [])))

    blocks.append(h(1, "Data och reproducerbarhet"))
    blocks.append(p(f"Mätningarna är gjorda med Vitki {prov.get('version', '')}, mätmetod "
                    f"{', '.join(f['method_versions'])}. Modellfilen identifieras med kontrollsumman ovan, och "
                    "parametrarna i tabellen räcker för att upprepa analysen. Tvärsnittens mått finns i bilagan; "
                    "råprofilerna kan publiceras i Vitkis mätkorpus (CC BY 4.0)."
                    + (" " + r_report.data_text(rr_) if rr_ else "")))
    blocks.append(h(1, "Tack"))
    ss = f.get("scan_source")
    blocks.append(p((scan_sources.credit_text(ss, signum) + " Fyll i: markägare, länsstyrelse, finansiärer.") if ss else
                    "Fyll i: den som skannat stenen, markägare, länsstyrelse, finansiärer."))
    blocks.append(h(1, "Referenser"))
    refs = list(REFERENCES) + (r_report.R_REFERENCES if rr_ else [])
    if ss:
        refs.append(ss["citation"])
    elif scan.get("citation"):
        refs.append(scan["citation"])
    if sri:
        refs.append(sri)
    refs.append(f"Vitki, version {prov.get('version', '2.0')}. Programvara. "
                "https://github.com/Precatio/runes")
    # Harvard order: single author before co-authored works by the same first author
    blocks.append(bullets(sorted(refs, key=lambda r: r.replace(" &", "~"))))

    if all_slices:
        blocks.append(h(1, "Bilaga A. Mått per tvärsnitt" if f.get("workflow") else "Bilaga. Mått per tvärsnitt"))
        letter = {i: marked.get(i, "") for i in range(len(all_slices))}
        ft_of = [ft for ft in order for _ in groups[ft]]
        blocks.append(tab(["#", "Spår", "Profil"] + [METRIC_LABELS[m] for m in METRICS] + ["R²"],
                          [[str(i + 1), FEATURE_TITLES[ft_of[i]], letter[i]]
                           + [fmt(s[m], DIGITS[m]) for m in METRICS] + [fmt(s.get("fit_r2"), 2)]
                           for i, s in enumerate(all_slices)],
                          f"Alla godkända tvärsnitt för {signum}."))
    wf = f.get("workflow")
    if wf:
        blocks += workflow_appendix(wf, signum, fig, tab)

    if any(b.get("ai") for b in blocks):
        blocks.append(p("Avsnitt markerade som AI-genererade är formulerade av en språkmodell utifrån de framräknade "
                        "resultaten och ska granskas av författaren."))
    # Result subsections are optional (e.g. no ornament to compare); number the ones present consecutively
    k = 0
    for b in blocks:
        if b["type"] == "heading" and b["level"] == 2 and re.match(r"^4\.\d+ ", b["text"]):
            k += 1
            b["text"] = re.sub(r"^4\.\d+", f"4.{k}", b["text"])
    return blocks
