"""Analysrutnätet för en huggspårsmätning (parameters.resolution_mm, fixed_resolution, harmonize_mm) och om flera
mätningar delar det (2026-11-19).

Ett grövre rutnät flyttar måtten: i det låsta provet 2026-11-19 (utdata/sakra_runor/resultat.md, planerna
analysplaner/2026-11-19-sakra-runor-*.md) gav rutnätet 1,2 mm i stället för 0,6 mm, på samma skanningar, i medel
1,9° större V-vinkel och 0,95 mm större spårbredd på Kitzler Åhfeldts skanningar (2,9° och 1,1 mm på Zedigs).
Stenarnas medelvärden följde varandra väl (ICC 0,93–0,99), men nivån flyttades. Jämförelser och samlingar av
mätningar från flera stenar varnar därför när rutnäten skiljer sig. Samma regel som web/src/lib/analysisGrid.ts."""
from __future__ import annotations

import math

PROTOCOL_GRID_MM = 0.6  # src/protocol.PARAMETERS["resolution_mm"]
GRID_TOLERANCE_MM = 0.01  # rutnät närmare än så räknas som samma

GRID_EFFECT_TEXT = ("Ett grövre analysrutnät flyttar måtten: i provet 2026-11-19 gav rutnätet 1,2 mm i stället för "
                    "0,6 mm, på samma skanningar, omkring 2° större V-vinkel (1,9° på skanningarna från Södermanland, "
                    "2,9° på dem från Medelpad och Hälsingland) och omkring 1 mm större spårbredd. Skillnader mellan mätningar med olika rutnät "
                    "kan alltså komma av rutnätet och inte av stenarna.")
GRID_REMEDY_TEXT = ("Mät om med samma rutnät: analysera skanningen i 3D-vyn med Vitki-protokollet (fast rutnät "
                    "0,6 mm).")


def _num(v) -> float | None:
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) else None


def grid_of(params: dict | None) -> dict:
    """Rutnätet ur en mätnings parametrar (eller provenance.parameters)."""
    p = params or {}
    fixed = p.get("fixed_resolution")
    return {"resolution_mm": _num(p.get("resolution_mm")),
            "fixed": fixed if isinstance(fixed, bool) else None,
            "harmonize_mm": _num(p.get("harmonize_mm")) or None}


def same_grid(a: dict, b: dict) -> bool | None:
    if a["resolution_mm"] is None or b["resolution_mm"] is None:
        return None
    return (abs(a["resolution_mm"] - b["resolution_mm"]) < GRID_TOLERANCE_MM
            and abs((a["harmonize_mm"] or 0) - (b["harmonize_mm"] or 0)) < GRID_TOLERANCE_MM)


def _mm(v: float) -> str:
    return f"{v:.2f} mm".replace(".", ",")


def grid_label(g: dict) -> str:
    if g["resolution_mm"] is None:
        return "okänt rutnät"
    return (_mm(g["resolution_mm"]) + (" (följer skanningen)" if g["fixed"] is False else "")
            + (f", harmonisering {_mm(g['harmonize_mm'])}" if g["harmonize_mm"] else ""))


def comparability_check(params_a: dict | None, params_b: dict | None) -> dict | None:
    """Kontrollen för Jämför stenar (src/stone_compare.comparability): None när något rutnät saknas."""
    a, b = grid_of(params_a), grid_of(params_b)
    same = same_grid(a, b)
    if same is None:
        return None
    if same:
        return {"key": "rutnät", "ok": True, "text": f"Samma analysrutnät ({grid_label(a)})."}
    return {"key": "rutnät", "ok": False,
            "text": f"Olika analysrutnät ({grid_label(a)} och {grid_label(b)}). {GRID_EFFECT_TEXT} {GRID_REMEDY_TEXT}"}


def grid_mix(grids: list[dict]) -> dict:
    """Rutnäten bland flera mätningar, vanligast först: {groups: [{label, resolution_mm, n}], mixed, unknown}."""
    reps: list[dict] = []
    groups: list[dict] = []
    unknown = 0
    for g in grids:
        if g["resolution_mm"] is None:
            unknown += 1
            continue
        for k, r in enumerate(reps):
            if same_grid(r, g):
                groups[k]["n"] += 1
                break
        else:
            reps.append(g)
            groups.append({"label": grid_label(g), "resolution_mm": g["resolution_mm"], "n": 1})
    groups.sort(key=lambda x: -x["n"])
    return {"groups": groups, "mixed": len(groups) > 1, "unknown": unknown}


def reference_check(query_params: dict | None, reference_params: list[dict | None]) -> dict | None:
    """För syntesen: stenens rutnät mot korpusstenarnas. None när stenens rutnät inte är känt."""
    q = grid_of(query_params)
    if q["resolution_mm"] is None:
        return None
    refs = [grid_of(p) for p in reference_params]
    mix = grid_mix(refs)
    other = sum(1 for r in refs if same_grid(q, r) is False)
    warning = None
    if other:
        warning = (f"Stenen är mätt med rutnätet {grid_label(q)}, men {other} av {len(refs)} stenar i jämförelsen "
                   f"med ett annat ({', '.join(f'{g['label']}: {g['n']}' for g in mix['groups'])}). "
                   f"{GRID_EFFECT_TEXT} {GRID_REMEDY_TEXT}")
    return {"query": grid_label(q), "reference": [{"label": g["label"], "n": g["n"]} for g in mix["groups"]],
            "mixed": bool(other), "warning": warning}
