"""Öppna 3D-skanningar av runstenar som appen känner till, så att rapporter krediterar den som skannat.

När en sten finns i en av serierna fyller stenrapporten i skanner, vem som skannat, licens och DOI, lägger
datamängden bland referenserna och tackar upphovspersonen. Uppgifter som användaren själv anger går före.
Signumen i serierna är hämtade ur filförteckningarna på Zenodo.
"""
from __future__ import annotations

from src.signum import fold_signum

KA_PROJECT = "forskningsprojektet Runristandets dynamik (2009–2014)"

DATASETS = [
    {
        "key": "sodermanland",
        "citation": "Kitzler Åhfeldt, L. 2024. 3D-data Runstenar i Södermanland / Runestones in Södermanland "
                    "[Dataset]. Riksantikvarieämbetet. https://doi.org/10.5281/zenodo.11951255",
        "short": "Kitzler Åhfeldt 2024a",
        "creator": "Laila Kitzler Åhfeldt", "doi": "10.5281/zenodo.11951255",
        "url": "https://doi.org/10.5281/zenodo.11951255", "license": "CC BY 4.0",
        "device": "ATOS I (GOM), strukturerat ljus", "project": KA_PROJECT,
        "note": "Bara inskriftsytorna är skannade.",
        "signa": ["Sö 45", "Sö 52", "Sö 75", "Sö 112", "Sö 113", "Sö 128", "Sö 129", "Sö 131", "Sö 134", "Sö 137",
                  "Sö 143", "Sö 149", "Sö 160", "Sö 161", "Sö 162", "Sö 163", "Sö 164", "Sö 165", "Sö 166", "Sö 184",
                  "Sö 205", "Sö 206", "Sö 207", "Sö 208", "Sö 211", "Sö 307", "Sö 319", "Sö 333", "Sö 360", "Sö 367",
                  "Sö 370", "Sö 371", "Sö Fv1948;282", "Sö Fv1954;19", "Sö Fv1973;189"],
    },
    {
        "key": "asmund",
        "citation": "Kitzler Åhfeldt, L. 2024. 3D-data Runstenar signerade av Åsmund Kåresson / Runestones signed by "
                    "Asmund Karasun [Dataset]. Riksantikvarieämbetet. https://doi.org/10.5281/zenodo.13347851",
        "short": "Kitzler Åhfeldt 2024b",
        "creator": "Laila Kitzler Åhfeldt", "doi": "10.5281/zenodo.13347851",
        "url": "https://doi.org/10.5281/zenodo.13347851", "license": "CC BY 4.0",
        "device": "ATOS I (GOM), strukturerat ljus", "project": KA_PROJECT, "note": "",
        "signa": ["Gs 11", "Gs 13", "U 1144"],
    },
    {
        "key": "halsingland",
        "citation": "Kitzler Åhfeldt, L. 2025. 3D-data Runstenar i Hälsingland [Dataset]. Riksantikvarieämbetet. "
                    "https://doi.org/10.5281/zenodo.15638873",
        "short": "Kitzler Åhfeldt 2025",
        "creator": "Laila Kitzler Åhfeldt", "doi": "10.5281/zenodo.15638873",
        "url": "https://doi.org/10.5281/zenodo.15638873", "license": "CC BY 4.0",
        "device": "HandySCAN BLACK Elite (Creaform), handhållen laserskanner", "project": "Runverket", "note": "",
        "signa": ["Hs 1", "Hs 2", "Hs 3", "Hs 4", "Hs 6", "Hs 9", "Hs 10", "Hs 11", "Hs 12", "Hs 14", "Hs 15",
                  "Hs 16", "Hs 21"],
    },
    {
        "key": "vastergotland",
        "citation": "Kitzler Åhfeldt, L. 2024. 3D-data Runstenar och tidigkristna gravmonument i Västergötland "
                    "[Dataset]. Riksantikvarieämbetet. https://doi.org/10.5281/zenodo.14046713",
        "short": "Kitzler Åhfeldt 2024c",
        "creator": "Laila Kitzler Åhfeldt", "doi": "10.5281/zenodo.14046713",
        "url": "https://doi.org/10.5281/zenodo.14046713", "license": "CC BY 4.0",
        "device": "", "project": KA_PROJECT, "note": "",
        "signa": ["Vg 24", "Vg 27", "Vg 41", "Vg 43", "Vg 51", "Vg 53"],
    },
]

_BY_SIGNUM = {fold_signum(sg): ds for ds in DATASETS for sg in ds["signa"]}


def lookup(signum: str | None) -> dict | None:
    """Den öppna skanningsserie stenen ingår i, eller None. Delsten (Sö 137A) räknas till stenen."""
    if not signum:
        return None
    key = fold_signum(signum)
    return _BY_SIGNUM.get(key) or _BY_SIGNUM.get(key.rstrip("ab"))


def fill_scan(scan: dict, signum: str | None) -> tuple[dict, dict | None]:
    """Skanningsuppgifterna med seriens uppgifter där användaren inte angett något."""
    ds = lookup(signum)
    if not ds:
        return scan, None
    out = dict(scan or {})
    defaults = {"device": ds["device"], "scanned_by": ds["creator"], "license": ds["license"], "url": ds["url"],
                "citation": ds["citation"]}
    for k, v in defaults.items():
        if v and not out.get(k):
            out[k] = v
    return out, ds


def credit_text(ds: dict, signum: str) -> str:
    return (f"Skanningen av {signum} är gjord av {ds['creator']} inom {ds['project']} och publicerad med licensen "
            f"{ds['license']} ({ds['short']}; doi:{ds['doi']}). Vi tackar för att datamängden gjorts fritt tillgänglig."
            + (f" {ds['note']}" if ds.get("note") else ""))
