"""Figurer ur R-analyserna för Månadens fynd: kartverktygets kartbilder (var mönstren samlas, genomsökningen av
landskapet, fornlämningarna) och korpusanalysernas övriga figurer.

En figur som används i ett inlägg kopieras till data/blog/figures/ under sin innehållshash och visas från
/api/blog/figures/{hash}.png. Kopian ändras aldrig, så ett publicerat inlägg behåller sin bild även när korpusanalysen
räknas om och figurerna får ett nytt fingeravtryck.
"""
from __future__ import annotations

import hashlib
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.path.join(ROOT, "data", "blog", "figures")
NAME = re.compile(r"^[0-9a-f]{16}\.png$")

# File name → group (map, time, other), Swedish and English caption, the R script
FIXED = {
    "landskap_genomsokning.png": ("map", "Dolda mönster i landskapet: varje mönster mot varje slags plats",
                                  "Hidden patterns in the landscape: every pattern against every kind of place", "remains.R"),
    "lamningar_narhet.png": ("map", "Runstenarna och fornlämningarna: andelen inom 500 m, mot slumpvisa platser i samma trakter",
                             "The runestones and the ancient monuments: the share within 500 m, against random places in the same districts",
                             "remains.R"),
    "geografi_vatten.png": ("map", "Avståndet till vatten: runstenarna mot slumpvisa platser",
                            "The distance to water: the runestones against random places", "geography.R"),
    "geografi_ristare.png": ("map", "Ristarnas områden", "The carvers' areas", "geography.R"),
    "okanda_ristare.png": ("map", "Grupper av stenar utan ristare", "Groups of stones without a carver", "anonymous.R"),
    "forandring_karta.png": ("map", "Var dragen är vanligast (rumslig modell med ristaren som slumpeffekt)",
                             "Where the features are most common (spatial model with the carver as a random effect)", "change.R"),
    "dialekt_grupper.png": ("map", "Stavningens geografi: grupper av härader", "The geography of spelling: groups of hundreds", "dialect.R"),
    "dialekt_efter.png": ("map", "Första runan i æftiR på kartan", "The first rune of æftiR on the map", "dialect.R"),
    "dialekt_sten.png": ("map", "Diftong och monoftong i stæinn på kartan", "Diphthong and monophthong in stæinn on the map", "dialect.R"),
    "dialekt_avstand.png": ("other", "Stavningen skiljer sig mer ju längre ifrån varandra häraderna ligger",
                            "Spelling differs more the further apart the hundreds are", "dialect.R"),
    "forandring_tid.png": ("time", "Dragen över tid, med plats och ristare konstanta", "The features over time, with place and carver held constant", "change.R"),
    "forandring_landskap.png": ("time", "Dragen landskap för landskap omkring 1050", "The features province by province around 1050", "change.R"),
    "seriation_diagram.png": ("time", "Seriationen av språk och innehåll", "The seriation of language and content", "chronology.R"),
    "seriation_validering.png": ("time", "Seriationen mot Gräslunds stilkronologi", "The seriation against Gräslund's style chronology", "chronology.R"),
    "seriation_skattning.png": ("time", "Skattade dateringar ur seriationen", "Estimated dates from the seriation", "chronology.R"),
    "kluster_mca.png": ("other", "Stenarnas grupper (MCA)", "The stones' groups (MCA)", "clusters.R"),
    "kluster_variabler.png": ("other", "Kategorierna i MCA", "The categories in the MCA", "clusters.R"),
    "kluster_ristare.png": ("other", "Ristarnas stenar i grupperna", "The carvers' stones in the groups", "clusters.R"),
    "kluster_silhuett.png": ("other", "Hur tydliga grupperna är (silhuett)", "How clear the groups are (silhouette)", "clusters.R"),
    "modell_delmodeller.png": ("other", "Attribueringsmodellen: vad varje del bidrar med", "The attribution model: what each part contributes", "attribution.R"),
    "modell_kalibrering.png": ("other", "Attribueringsmodellens kalibrering", "The attribution model's calibration", "attribution.R"),
    "modell_variabler.png": ("other", "Attribueringsmodellens viktigaste variabler", "The attribution model's most important variables", "attribution.R"),
    "modell_forvaxling.png": ("other", "Vilka ristare modellen blandar ihop", "Which carvers the model confuses", "attribution.R"),
    "natverk_formler.png": ("other", "Formelnätverket", "The network of formulas", "network.R"),
    "natverk_slakt.png": ("other", "Släktrelationerna i inskrifterna", "The kinship relations in the inscriptions", "network.R"),
    "text_formler.png": ("other", "Ristarnas formler", "The carvers' formulas", "text.R"),
    "text_stavning.png": ("other", "Stavningen av vanliga ord", "The spelling of common words", "text.R"),
}
GROUPS = {"map": "Kartan och landskapet", "time": "Tid och datering", "other": "Övriga analyser"}
GROUPS_EN = {"map": "The map and the landscape", "time": "Time and dating", "other": "Other analyses"}


def describe(name: str, labels: dict[str, str] | None = None, tr=lambda t: t) -> dict | None:
    """Grupp, bildtext på svenska och engelska och R-skriptet för en figurfil, eller None för okända filer."""
    m = re.match(r"^hotspot_(.+)\.png$", name)
    if m:
        label = (labels or {}).get(m.group(1), m.group(1))
        return {"name": name, "group": "map", "script": "hotspots.R",
                "label": f"{label} – var mönstret samlas (andel per område, heta områden och kluster)",
                "label_en": f"{tr(label)} – where the pattern gathers (share per area, hot areas and clusters)"}
    if name in FIXED:
        g, sv, en, script = FIXED[name]
        return {"name": name, "group": g, "script": script, "label": sv, "label_en": en}
    return None


def available(res: dict, labels: dict[str, str] | None = None, tr=lambda t: t) -> list[dict]:
    """Korpusanalysens figurer som kan användas i bloggen, kartbilderna först."""
    names = []
    for mod in res.values() if isinstance(res, dict) else []:
        figs = (mod or {}).get("figures") if isinstance(mod, dict) else None
        if isinstance(figs, dict):
            names += [v for v in figs.values() if isinstance(v, str)]
    out = [d for n in dict.fromkeys(names) if (d := describe(n, labels, tr))]
    order = {"map": 0, "time": 1, "other": 2}
    return sorted(out, key=lambda d: (order[d["group"]], not d["name"].startswith("hotspot_"), d["label"]))


def freeze(data: bytes) -> str:
    """Sparar en figur under sin innehållshash och ger dess adress; samma bild sparas bara en gång."""
    name = hashlib.sha256(data).hexdigest()[:16] + ".png"
    os.makedirs(DIR, exist_ok=True)
    path = os.path.join(DIR, name)
    if not os.path.exists(path):
        tmp = path + ".tmp"
        with open(tmp, "wb") as fh:
            fh.write(data)
        os.replace(tmp, path)
    return f"/api/blog/figures/{name}"


def path_of(name: str) -> str | None:
    if not NAME.match(name):
        return None
    p = os.path.join(DIR, name)
    return p if os.path.exists(p) else None


def markdown(url: str, d: dict, lang: str = "sv") -> str:
    """Figuren som block i ett inlägg (components/BlogBody.tsx): bilden och bildtexten med källan."""
    if lang == "en":
        return (f"![{d['label_en']}]({url})\n{d['label_en']}. Source: Vitki's corpus analysis in R ({d['script']}); "
                "Scandinavian Runic-text Data Base (ODbL).")
    return f"![{d['label']}]({url})\n{d['label']}. Källa: Vitkis korpusanalys i R ({d['script']}); Samnordisk runtextdatabas (ODbL)."
