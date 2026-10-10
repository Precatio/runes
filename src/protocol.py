"""Vitki-protokollet för automatisk huggspårsmätning (PROTOCOL.md) i maskinläsbar form.

Protokollet låser de parametrar som avgör om två stenar är jämförbara. Varje automatisk analys kontrolleras mot
dem, och proveniensen anger om analysen följde protokollet och vilka avvikelser som gjordes.
"""
from __future__ import annotations

VERSION = "vitki-groove-1-utkast"  # blir "vitki-groove-1" när protokollet låses vid en release med DOI
METHOD_VERSION = "groove-5"  # mätmetoden protokollet gäller (api/config.py; kontrolleras i testerna)

# Parametrar för analyze_grooves. Rutnätet är fast (inte skanningens egen upplösning), så att stenar skannade med
# olika punkttäthet mäts på samma sätt (METHODS.md 1, 1e).
PARAMETERS = {
    "resolution_mm": 0.6,
    "sensitivity": 3.0,
    "spacing_mm": 3.0,
    "max_halfwidth_mm": 8.0,
    "harmonize_mm": None,
    "runes_only": True,
}

# Krav på skanningen (rekommendationer; kontrolleras mot medelkantlängden när den finns)
MAX_MESH_SPACING_MM = 0.5

LABELS = {"resolution_mm": "rutnät", "sensitivity": "känslighet", "spacing_mm": "snittavstånd",
          "max_halfwidth_mm": "största halva spårbredd", "harmonize_mm": "harmonisering", "runes_only": "bara runor"}


def compliance(parameters: dict, method_version: str | None = None) -> dict:
    """Följer analysen protokollet? Jämför analysens parametrar (analyze_grooves 'parameters') med protokollets."""
    deviations = []
    if method_version and method_version != METHOD_VERSION:
        deviations.append(f"mätmetod {method_version} (protokollet: {METHOD_VERSION})")
    if not parameters.get("fixed_resolution"):
        deviations.append(f"rutnätet följer skanningen ({parameters.get('resolution_mm', 0):.2f} mm) i stället för fast "
                          f"{PARAMETERS['resolution_mm']} mm")
    for key, want in PARAMETERS.items():
        if key == "resolution_mm" and not parameters.get("fixed_resolution"):
            continue
        have = parameters.get(key)
        same = (have is None and want is None) or (have is not None and want is not None and
                                                     (abs(float(have) - float(want)) < 1e-6 if not isinstance(want, bool) else bool(have) == want))
        if not same:
            deviations.append(f"{LABELS[key]} {have} (protokollet: {want})")
    notes = []
    spacing = parameters.get("mesh_point_spacing_mm")
    if spacing and spacing == spacing and spacing > MAX_MESH_SPACING_MM:  # NaN-safe
        notes.append(f"skanningens punktavstånd {spacing:.2f} mm är större än rekommenderade {MAX_MESH_SPACING_MM} mm; "
                     "resultaten är mindre säkra (METHODS.md 1e)")
    return {"version": VERSION, "compliant": not deviations, "deviations": deviations, "notes": notes}
