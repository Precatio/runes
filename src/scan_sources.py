"""Öppna 3D-skanningar av runstenar som appen känner till, så att rapporter krediterar den som skannat.

När den inlästa skanningen känns igen som en av seriernas publicerade filer (identify: SHA-256, md5, eller filnamn
och storlek ur data/scan_files.json) fyller stenrapporten i skanner, vem som skannat, licens och DOI, lägger
datamängden bland referenserna och tackar upphovspersonen; exporten från huggspårsanalysen (src/groove_export.py)
krediterar på samma sätt. Ett inskrivet signum räcker aldrig för att kreditera någon annan. Uppgifter som användaren
själv anger går före. Signumen i serierna är hämtade ur filförteckningarna på Zenodo.
"""
from __future__ import annotations

import json
import math
import os
from functools import lru_cache

from src.signum import fold_signum

KA_PROJECT = "forskningsprojektet Runristandets dynamik (2009–2014)"
# Hälsinglands och Medelpads stenar skannades av Henrik Zedig; Laila Kitzler Åhfeldt är medförfattare till
# datamängderna. "scanned_by" anger den som skannade, "creator" datamängdens upphovspersoner.
ZEDIG = "Henrik Zedig (Länsstyrelsen Västra Götaland)"
# The scanner's name and institution as the Zenodo records give them (creators/contributors and their affiliation),
# for the export's visible credit; "scanned_by" above keeps the stone report's wording
KA = {"scanner": "Laila Kitzler Åhfeldt", "institution": "Riksantikvarieämbetet"}
ZEDIG_SCANNER = {"scanner": "Henrik Zedig", "institution": "Länsstyrelsen Västra Götalands län"}
LICENSE_URLS = {"CC BY 4.0": "https://creativecommons.org/licenses/by/4.0/"}

DATASETS = [
    {
        "key": "sodermanland", **KA,
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
        "key": "asmund", **KA,
        "citation": "Kitzler Åhfeldt, L. 2024. 3D-data Runstenar signerade av Åsmund Kåresson / Runestones signed by "
                    "Asmund Karasun [Dataset]. Riksantikvarieämbetet. https://doi.org/10.5281/zenodo.13347851",
        "short": "Kitzler Åhfeldt 2024b",
        "creator": "Laila Kitzler Åhfeldt", "doi": "10.5281/zenodo.13347851",
        "url": "https://doi.org/10.5281/zenodo.13347851", "license": "CC BY 4.0",
        "device": "ATOS I (GOM), strukturerat ljus", "project": KA_PROJECT, "note": "",
        "signa": ["Gs 11", "Gs 13", "U 1144"],
    },
    {
        "key": "halsingland", **ZEDIG_SCANNER,
        "citation": "Kitzler Åhfeldt, L. & Zedig, H. 2025. 3D-data Runstenar i Hälsingland [Dataset]. "
                    "Riksantikvarieämbetet. https://doi.org/10.5281/zenodo.15638873",
        "short": "Kitzler Åhfeldt & Zedig 2025",
        "creator": "Laila Kitzler Åhfeldt och Henrik Zedig", "scanned_by": ZEDIG, "doi": "10.5281/zenodo.15638873",
        "url": "https://doi.org/10.5281/zenodo.15638873", "license": "CC BY 4.0",
        "device": "HandySCAN BLACK Elite (Creaform), handhållen laserskanner", "project": "Runverket", "note": "",
        "signa": ["Hs 1", "Hs 2", "Hs 3", "Hs 4", "Hs 6", "Hs 9", "Hs 10", "Hs 11", "Hs 12", "Hs 14", "Hs 15",
                  "Hs 16", "Hs 21"],
    },
    {
        "key": "vastergotland", **KA,
        "citation": "Kitzler Åhfeldt, L. 2024. 3D-data Runstenar och tidigkristna gravmonument i Västergötland "
                    "[Dataset]. Riksantikvarieämbetet. https://doi.org/10.5281/zenodo.14046713",
        "short": "Kitzler Åhfeldt 2024c",
        "creator": "Laila Kitzler Åhfeldt", "doi": "10.5281/zenodo.14046713",
        "url": "https://doi.org/10.5281/zenodo.14046713", "license": "CC BY 4.0",
        "device": "", "project": KA_PROJECT, "note": "",
        "signa": ["Vg 24", "Vg 27", "Vg 41", "Vg 43", "Vg 51", "Vg 53"],
    },
    {
        "key": "medelpad", **ZEDIG_SCANNER,
        "citation": "Kitzler Åhfeldt, L. & Zedig, H. 2024. 3D-data Runstenar i Medelpad [Dataset]. "
                    "Riksantikvarieämbetet. https://doi.org/10.5281/zenodo.14141222",
        "short": "Kitzler Åhfeldt & Zedig 2024",
        "creator": "Laila Kitzler Åhfeldt och Henrik Zedig", "scanned_by": ZEDIG, "doi": "10.5281/zenodo.14141222",
        "url": "https://doi.org/10.5281/zenodo.14141222", "license": "CC BY 4.0",
        "device": "HandySCAN BLACK Elite (Creaform), handhållen laserskanner, upplösning 0,40 mm",
        "project": "forskningsprojektet Evighetsrunor: en forskningsplattform för Sveriges runinskrifter",
        "note": "Skannat inför en korpusutgåva av Medelpads runinskrifter. M 14 finns i två filer.",
        "signa": ["M 1", "M 2", "M 3", "M 4", "M 5", "M 6", "M 7", "M 8", "M 10", "M 11", "M 13", "M 14", "M 15",
                  "M 16"],
    },
    {
        "key": "gravmonument_og_sm", "scanner": "Laila Kitzler Åhfeldt", "institution": None,
        "citation": "Kitzler Åhfeldt, L. 2025. 3D-data Tidigkristna gravmonument Östergötland och Småland [Dataset]. "
                    "Zenodo. https://doi.org/10.5281/zenodo.17571537",
        "short": "Kitzler Åhfeldt 2025",
        "creator": "Laila Kitzler Åhfeldt", "doi": "10.5281/zenodo.17571537",
        "url": "https://doi.org/10.5281/zenodo.17571537", "license": "CC BY 4.0",
        "device": "ATOS II (GOM), strukturerat ljus, punktavstånd 0,27 mm",
        "project": "Cecilia Ljungs avhandlingsprojekt om tidigkristna gravmonument (skannat 2008; Ljung 2016)",
        "note": "Bara inskriftsytorna är skannade. Ög 240 och Ög 241 är samma gravhäll.",
        "signa": ["Ög 2", "Ög 5", "Ög 6", "Ög 240", "Ög 241", "Ög Hov12;21", "Ög Hov14;22", "Ög Hov15;22", "Sm 124",
                  "Sm 125"],
    },
]

_BY_SIGNUM = {fold_signum(sg): ds for ds in DATASETS for sg in ds["signa"]}


def lookup(signum: str | None) -> dict | None:
    """Den öppna skanningsserie stenen ingår i, eller None. Delsten (Sö 137A) räknas till stenen."""
    if not signum:
        return None
    key = fold_signum(signum)
    return _BY_SIGNUM.get(key) or _BY_SIGNUM.get(key.rstrip("ab"))


def fill_scan(scan: dict, ds: dict | None) -> dict:
    """Skanningsuppgifterna med seriens uppgifter där användaren inte angett något. ds är den igenkända filens serie
    (identify), aldrig en serie som slagits upp på signum."""
    out = dict(scan or {})
    if not ds:
        return out
    defaults = {"device": ds["device"], "scanned_by": ds.get("scanned_by") or ds["creator"], "license": ds["license"],
                "url": ds["url"],
                "citation": ds["citation"]}
    for k, v in defaults.items():
        if v and not out.get(k):
            out[k] = v
    return out


# ---- the published files ---------------------------------------------------------------------------------------------
# A scan is credited to a series only when the loaded file is one of the series' own files: the same SHA-256 or md5
# as the published file, or (when neither checksum is known, as in older analyses) the same file name and, when
# known, the same size. A typed signum alone never attaches a third-party credit (METHODS.md 2f).

FILES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "scan_files.json")
_BY_KEY = {ds["key"]: ds for ds in DATASETS}


@lru_cache(maxsize=1)
def _files() -> dict:
    """data/scan_files.json: the STL files of each series (Zenodo's name, size and md5; SHA-256 where a downloaded
    copy matched Zenodo's md5). Empty when the file is missing."""
    try:
        with open(FILES_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return {"by_sha256": {}, "by_md5": {}, "by_name": {}}
    by_sha, by_md5, by_name = {}, {}, {}
    for key, block in (data.get("datasets") or {}).items():
        if key not in _BY_KEY:
            continue
        for rec in block.get("files") or []:
            item = (key, rec)
            if rec.get("sha256"):
                by_sha[rec["sha256"].lower()] = item
            if rec.get("md5"):
                by_md5[rec["md5"].lower()] = item
            by_name.setdefault(rec["name"], []).append(item)
    return {"by_sha256": by_sha, "by_md5": by_md5, "by_name": by_name}


def identify(filename: str | None = None, sha256: str | None = None, md5: str | None = None,
             size: int | None = None) -> dict | None:
    """The published file the loaded scan is, or None: {"dataset", "file", "match"}.

    A checksum decides when one is known: an unknown SHA-256 or md5 means a different (for example a reduced or
    edited) file, even under a published name. Without a matching checksum the file name and the size must both
    match; a file name alone is never enough."""
    reg = _files()
    sha = (sha256 or "").strip().lower()
    m5 = (md5 or "").strip().lower()
    if sha and sha in reg["by_sha256"]:
        key, rec = reg["by_sha256"][sha]
        return {"dataset": _BY_KEY[key], "file": rec, "match": "sha256"}
    if m5 and m5 in reg["by_md5"]:
        key, rec = reg["by_md5"][m5]
        return {"dataset": _BY_KEY[key], "file": rec, "match": "md5"}
    if size is None:
        return None  # a file name alone (no size, no matching checksum) is not enough to tell
    name = os.path.basename((filename or "").replace("\\", "/"))
    for key, rec in reg["by_name"].get(name, []):
        if m5 and rec.get("md5"):
            continue  # the md5 is known and differs: not the published file
        if sha and rec.get("sha256"):
            continue  # likewise for SHA-256
        if rec.get("size") is None or int(size) != int(rec["size"]):
            continue
        return {"dataset": _BY_KEY[key], "file": rec, "match": "filnamn och storlek"}
    return None


def identify_mesh(mesh: dict | None) -> dict | None:
    """identify for a loaded model's info or an analysis' provenance.mesh (filename, sha256, md5, bytes)."""
    m = mesh if isinstance(mesh, dict) else {}
    size = m.get("bytes")
    size = int(size) if isinstance(size, (int, float)) and not isinstance(size, bool) and math.isfinite(size) else None
    text = (lambda v: v if isinstance(v, str) else None)
    return identify(text(m.get("filename")), text(m.get("sha256")), text(m.get("md5")), size)


def file_signa(file: dict) -> list[str]:
    """The stones a published file shows: its "signa" (one file can hold two, as Ög 240 and Ög 241), else its
    signum."""
    signa = [sg for sg in (file.get("signa") or []) if isinstance(sg, str) and sg]
    return signa or ([file["signum"]] if file.get("signum") else [])


def file_credit_text(ds: dict, file: dict, ref: str | None = None) -> str:
    """The visible credit for an identified file: scanner, institution, project, licence with link and DOI.

    ref is a short reference ("Kitzler Åhfeldt 2024a") for a document with a reference list (the stone report); a file
    on its own (PNG footers, CSV '#' lines) has none, so it names the dataset by its DOI alone."""
    who = ds.get("scanner") or ds.get("scanned_by") or ds["creator"]
    inst = ds.get("institution")
    who = f"{who} ({inst})" if inst else f"{who} (institutionen anges inte i datamängden)"
    lic = ds["license"]
    lic_url = LICENSE_URLS.get(lic)
    lic_text = f"{lic} ({lic_url})" if lic_url else lic
    signa = file_signa(file)
    what = f"Skanningen av {' och '.join(signa)}" if signa else "Skanningen"
    published = "publicerad" if who.startswith(ds["creator"]) else f"publicerad av {ds['creator']}"
    where = f"med licensen {lic_text} i {ref}" if ref else f"som datamängd med licensen {lic_text}"
    return (f"{what} (filen {file['name']}) är gjord av {who} inom {ds['project']} och {published} {where}, "
            f"doi:{ds['doi']} ({ds['url']})." + (f" {ds['note']}" if ds.get("note") else ""))


def report_credit_text(ds: dict, file: dict) -> str:
    """The stone report's thanks for an identified file: the export's credit and a thank-you."""
    return file_credit_text(ds, file, ds["short"]) + " Vi tackar för att datamängden gjorts fritt tillgänglig."

