"""Laddar upp rapporternas Zenodo-dataset (byggda med scripts/zenodo_dataset/build.py) som UTKAST, och publicerar dem
först när det begärs. Viktor 2026-11-10: "varje forskningsrapport får sina data som eget dataset på Zenodo; data blir
citerade".

    .venv/bin/python scripts/zenodo_dataset/ladda_upp.py [--slug S] [--sandlada]               # 1. utkast, inget publiceras
    .venv/bin/python scripts/zenodo_dataset/ladda_upp.py --publicera [--slug S] [--sandlada]   # 2. publicera utkasten

Steg 1 skapar per rapport en deposition med metadata ur zenodo_metadata.json och ett reserverat DOI, och lägger
README.md, MANIFEST.json och data_and_code.zip i dess bucket. Filernas MD5 jämförs med Zenodos svar och zip-filens
SHA-256 med MANIFEST.json (paketet ska vara orört sedan bygget). Inget publiceras: Viktor granskar utkasten på Zenodo.
Steg 2 publicerar utkast som redan finns. Båda stegen skriver DOI:erna till web/content/dataset_dois.json (samma form som
web/content/report_dois.json): det reserverade DOI:t med "published": null efter steg 1, publiceringsdatum och concept-DOI
efter steg 2. En rapport som redan står där får inget nytt utkast (ta bort posten för att börja om).

--sandlada använder sandbox.zenodo.org och skriver DOI:erna till /Volumes/2TB/Antigrvity/Runes/zenodo/dataset_dois_sandlada.json
i stället, så att webbplatsens fil aldrig får sandlådans DOI:er. Token (ZENODO_TOKEN, deposit:write och deposit:actions)
läses ur miljön eller .env som i scripts/zenodo_rapporter.py och skrivs aldrig ut. TLS kontrolleras mot certifi, eftersom
Pythons egen certifikatkontroll inte fungerar på den här datorn.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = "/Volumes/2TB/Antigrvity/Runes/zenodo/dataset"
DOIS = os.path.join(ROOT, "web", "content", "dataset_dois.json")
DOIS_SANDBOX = "/Volumes/2TB/Antigrvity/Runes/zenodo/dataset_dois_sandlada.json"
REPORT_DOIS = os.path.join(ROOT, "web", "content", "report_dois.json")
FILES = ["README.md", "MANIFEST.json", "data_and_code.zip"]
OM = ("Forskningsrapporternas data som egna dataset på Zenodo (scripts/zenodo_dataset/). doi = datasetets version, "
      "concept_doi = alla versioner, report_doi = rapportversionen datasetet hör till; published är null så länge "
      "datasetet är ett outgivet utkast.")


def _session(sandbox: bool):
    import certifi
    import requests
    token = os.environ.get("ZENODO_TOKEN")
    if not token:
        from dotenv import dotenv_values
        token = dotenv_values(os.path.join(ROOT, ".env")).get("ZENODO_TOKEN")
    assert token, "ZENODO_TOKEN saknas"
    s = requests.Session()
    s.headers["Authorization"] = f"Bearer {token}"
    s.verify = certifi.where()
    host = "https://sandbox.zenodo.org" if sandbox else "https://zenodo.org"
    return s, f"{host}/api", host


def _check(r, what: str):
    """raise_for_status with Zenodo's own message (the response never contains the token)."""
    if r.status_code >= 400:
        try:
            msg = json.dumps(r.json(), ensure_ascii=False)[:800]
        except ValueError:
            msg = r.text[:800]
        raise SystemExit(f"{what}: HTTP {r.status_code} {msg}")
    return r


def _load(path: str) -> dict:
    if os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    return {"_om": OM, "dataset": {}}


def _save(path: str, d: dict) -> None:
    d["dataset"] = dict(sorted(d["dataset"].items()))
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(d, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    os.replace(tmp, path)


def _md5(path: str) -> str:
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def slugs(only: str | None) -> list[str]:
    archived = json.load(open(REPORT_DOIS, encoding="utf-8"))["rapporter"]
    built = sorted(s for s in os.listdir(OUT) if os.path.isfile(os.path.join(OUT, s, "zenodo_metadata.json")))
    if only:
        assert only in built, f"{only}: inget byggt paket i {OUT} (kör build.py {only})"
        return [only]
    missing = sorted(set(archived) - set(built))
    if missing:
        print("Inget paket byggt för:", ", ".join(missing), file=sys.stderr)
    return built


def check_package(slug: str) -> dict:
    folder = os.path.join(OUT, slug)
    for f in FILES:
        assert os.path.isfile(os.path.join(folder, f)), f"{slug}: {f} saknas"
    man = json.load(open(os.path.join(folder, "MANIFEST.json"), encoding="utf-8"))
    assert man["report_slug"] == slug
    assert _sha256(os.path.join(folder, "data_and_code.zip")) == man["zip"]["sha256"], \
        f"{slug}: data_and_code.zip stämmer inte med MANIFEST.json – bygg om paketet"
    md = json.load(open(os.path.join(folder, "zenodo_metadata.json"), encoding="utf-8"))
    assert md["metadata"]["upload_type"] == "dataset"
    return {"metadata": md, "manifest": man}


def create_draft(slug: str, sandbox: bool, dois_path: str) -> dict:
    dois = _load(dois_path)
    if slug in dois["dataset"]:
        e = dois["dataset"][slug]
        print(f"{slug}: står redan i {os.path.basename(dois_path)} ({e['doi']}, "
              f"{'publicerad ' + e['published'] if e.get('published') else 'utkast'}); hoppar över")
        return e
    pkg = check_package(slug)
    folder = os.path.join(OUT, slug)
    s, api, host = _session(sandbox)
    md = json.loads(json.dumps(pkg["metadata"]))
    md["metadata"]["prereserve_doi"] = True
    d = _check(s.post(f"{api}/deposit/depositions", json=md), f"{slug}: skapa utkast").json()
    dep = f"{api}/deposit/depositions/{d['id']}"
    for f in FILES:
        with open(os.path.join(folder, f), "rb") as fh:
            _check(s.put(f"{d['links']['bucket']}/{f}", data=fh), f"{slug}: ladda upp {f}")
    d = _check(s.get(dep), f"{slug}: läs utkastet").json()
    got = {x["filename"]: x.get("checksum", "").replace("md5:", "") for x in d.get("files", [])}
    for f in FILES:
        assert got.get(f) == _md5(os.path.join(folder, f)), f"{slug}: {f} har fel kontrollsumma på Zenodo"
    doi = (d["metadata"].get("prereserve_doi") or {}).get("doi")
    assert doi, f"{slug}: inget reserverat DOI i utkastet {d['id']}"
    entry = {"doi": doi, "concept_doi": None, "version": 1, "record": f"{host}/records/{d['id']}", "published": None,
             "draft_id": d["id"], "report_doi": pkg["manifest"]["report_doi"],
             "report_concept_doi": pkg["manifest"]["report_concept_doi"], "zip_sha256": pkg["manifest"]["zip"]["sha256"]}
    dois = _load(dois_path)  # read again just before writing
    dois["dataset"][slug] = entry
    _save(dois_path, dois)
    print(f"{slug}: utkast {d['id']}, reserverat DOI {doi} – {d['links'].get('html')}")
    return entry


def publish(slug: str, sandbox: bool, dois_path: str) -> dict:
    dois = _load(dois_path)
    e = dois["dataset"].get(slug)
    if not e:
        print(f"{slug}: inget utkast i {os.path.basename(dois_path)}; skapa det först (utan --publicera)")
        return {}
    if e.get("published"):
        print(f"{slug}: redan publicerad {e['published']} ({e['doi']})")
        return e
    s, api, host = _session(sandbox)
    dep = f"{api}/deposit/depositions/{e['draft_id']}"
    d = _check(s.get(dep), f"{slug}: läs utkastet").json()
    assert sorted(x["filename"] for x in d.get("files", [])) == sorted(FILES), f"{slug}: utkastet har inte de tre filerna"
    d = _check(s.post(f"{dep}/actions/publish"), f"{slug}: publicera").json()
    assert d.get("doi") == e["doi"], f"{slug}: publicerat DOI {d.get('doi')} skiljer sig från det reserverade {e['doi']}"
    e.update({"concept_doi": d.get("conceptdoi"), "record": f"{host}/records/{d['id']}",
              "published": (d.get("metadata", {}).get("publication_date") or datetime.date.today().isoformat())})
    dois = _load(dois_path)
    dois["dataset"][slug] = e
    _save(dois_path, dois)
    print(f"{slug}: publicerad {e['published']}, DOI {e['doi']} (concept {e['concept_doi']})")
    return e


def main(argv=None) -> int:
    a = argparse.ArgumentParser(description="Rapporternas dataset till Zenodo: utkast, eller publicera med --publicera.")
    a.add_argument("--slug", help="bara en rapport")
    a.add_argument("--publicera", action="store_true", help="publicera utkast som redan finns (skapar inga nya)")
    a.add_argument("--sandlada", action="store_true", help="sandbox.zenodo.org; DOI:erna skrivs utanför repot")
    o = a.parse_args(argv)
    path = DOIS_SANDBOX if o.sandlada else DOIS
    for slug in slugs(o.slug):
        (publish if o.publicera else create_draft)(slug, o.sandlada, path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
