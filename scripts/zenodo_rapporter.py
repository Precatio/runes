"""Förbereder Vitkis publicerade forskningsrapporter för Zenodo: en PDF på svenska och en på engelska per rapport (sidan
/forskningsrapporter/<slug> och /en/forskningsrapporter/<slug> ur den lokala appen, utskriven i A4 med sidans egen
utskriftsstil) och Zenodos metadata (metadata.json), i /Volumes/2TB/Antigrvity/Runes/zenodo/rapporter/<slug>/.

Rapporterna hämtas ur web/content/articles.json, alltså bara de publicerade. Rubrikraden i den engelska texten (den
kanoniska för citering) ger rapportversion, datum, Vitkis version och nyckelord.

    .venv/bin/python scripts/zenodo_rapporter.py                 # PDF:er och metadata, inget laddas upp
    .venv/bin/python scripts/zenodo_rapporter.py --bara-metadata  # metadata utan att skriva PDF:er
    ZENODO_TOKEN=… .venv/bin/python scripts/zenodo_rapporter.py --ladda-upp [--sandlada] [--vitki-doi 10.5281/zenodo.N]

--ladda-upp skapar ett UTKAST per rapport på Zenodo (filer och metadata) men publicerar inget: Viktor granskar och trycker
Publish själv. Token skapas på zenodo.org under Applications → Personal access tokens (deposit:write och deposit:actions).
--sandlada använder sandbox.zenodo.org för en provomgång. --vitki-doi knyter rapporterna till programvarans DOI.

Ny version av en arkiverad rapport (posten står i web/content/report_dois.json):
    .venv/bin/python scripts/zenodo_rapporter.py --slug S --ny-version            # 1. utkast till ny version, DOI reserveras
    (för in DOI:t i report_dois.json, bygg om appen så att sidan visar det, skriv PDF:erna med --slug S)
    .venv/bin/python scripts/zenodo_rapporter.py --slug S --ny-version --ladda-upp  # 2. byt filerna och metadata i utkastet
Utkastet publiceras inte av skriptet. Token läses ur miljön eller .env och skrivs aldrig ut.
När versionen är publicerad på Zenodo: kör scripts/rapport_pdf_webb.py, som lägger PDF:erna på webbplatsen
(/forskningsrapporter-pdf/, citation_pdf_url för Google Scholar och nedladdningslänken på rapportsidan).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = "/Volumes/2TB/Antigrvity/Runes/zenodo/rapporter"
APP = "http://127.0.0.1:3000"
SITE = "https://vitkirunor.se"
PDF_JS = r"""
import { chromium } from "%s";
const jobs = JSON.parse(process.argv[2]);
const b = await chromium.launch();
for (const [url, out] of jobs) {
  const p = await b.newPage();
  const r = await p.goto(url, { waitUntil: "networkidle" });
  if (!r || r.status() !== 200) { console.error("FEL", r && r.status(), url); process.exit(1); }
  await p.emulateMedia({ media: "print" });
  await p.pdf({ path: out, format: "A4", printBackground: true, margin: { top: "18mm", bottom: "18mm", left: "16mm", right: "16mm" } });
  await p.close();
  console.log("pdf", out);
}
await b.close();
"""


def reports() -> list[dict]:
    posts = json.load(open(os.path.join(ROOT, "web", "content", "articles.json"), encoding="utf-8"))["posts"]
    return [p for p in posts if "Rapport" in (p.get("labels") or [])]


def header(body_en: str) -> dict:
    """Rubrikraden överst i den engelska texten: *Viktor Kvant, independent researcher. … Keywords: …*"""
    line = body_en.strip().splitlines()[0].strip("* ")
    m = re.search(r"Report version (\d+), (\d{4}-\d{2}-\d{2})", line)
    v = re.search(r"(?:made|done) in Vitki (\d+(?:\.\d+)*)", line)
    k = re.search(r"Keywords: ([^.]+)\.", line)
    lvl = re.search(r"independent researcher\. ([^.]+)\.", line)
    assert m and v and k, line[:200]
    return {"version": m.group(1), "date": m.group(2), "vitki": v.group(1), "level": lvl.group(1) if lvl else "",
            "keywords": [x.strip() for x in k.group(1).split(",") if x.strip()], "licence": "CC BY 4.0" if "CC BY 4.0" in line else None}


def metadata(p: dict, vitki_doi: str | None) -> dict:
    h = header(p["body_en"])
    assert h["licence"] == "CC BY 4.0", p["slug"]
    url_en, url_sv = f"{SITE}/en/forskningsrapporter/{p['slug']}", f"{SITE}/forskningsrapporter/{p['slug']}"
    desc = (f"<p>{p['summary_en']}</p><p><em>{h['level']}.</em> Research report from Vitki, an open platform for the analysis of "
            f"runic inscriptions. Report version {h['version']}; the analysis was made in Vitki {h['vitki']}. The report is "
            f"published in English (canonical for citation) and Swedish; both are included as PDF.</p>"
            f"<p><strong>Svenska:</strong> {p['title']}. {p['summary']}</p>")
    rel = [{"identifier": url_en, "relation": "isIdenticalTo", "scheme": "url", "resource_type": "publication-report"},
           {"identifier": url_sv, "relation": "isVariantFormOf", "scheme": "url", "resource_type": "publication-report"},
           {"identifier": "https://github.com/Precatio/runes", "relation": "isSupplementedBy", "scheme": "url", "resource_type": "software"}]
    if vitki_doi:
        rel.append({"identifier": vitki_doi, "relation": "isSupplementedBy", "scheme": "doi", "resource_type": "software"})
    return {"metadata": {
        "upload_type": "publication", "publication_type": "report",
        "title": p["title_en"], "creators": [{"name": "Kvant, Viktor", "affiliation": "Independent researcher", "orcid": "0009-0005-3886-6007"}],
        "description": desc, "publication_date": h["date"], "version": f"Report version {h['version']}",
        "language": "eng", "keywords": h["keywords"], "license": "cc-by-4.0", "access_right": "open",
        "related_identifiers": rel,
        "notes": f"Swedish title: {p['title']}. Analysis made in Vitki {h['vitki']} (https://github.com/Precatio/runes).",
    }}


def upload(slug: str, md: dict, folder: str, sandbox: bool) -> str:
    import requests
    token = os.environ["ZENODO_TOKEN"]
    base = "https://sandbox.zenodo.org/api" if sandbox else "https://zenodo.org/api"
    s = requests.Session()
    s.headers["Authorization"] = f"Bearer {token}"
    d = s.post(f"{base}/deposit/depositions", json={}).json()
    for f in sorted(os.listdir(folder)):
        if f.endswith(".pdf"):
            with open(os.path.join(folder, f), "rb") as fh:
                s.put(f"{d['links']['bucket']}/{f}", data=fh).raise_for_status()
    s.put(f"{base}/deposit/depositions/{d['id']}", json=md).raise_for_status()
    return d["links"]["html"]


def _session(sandbox: bool):
    import requests
    token = os.environ.get("ZENODO_TOKEN")
    if not token:
        from dotenv import dotenv_values
        token = dotenv_values(os.path.join(ROOT, ".env")).get("ZENODO_TOKEN")
    assert token, "ZENODO_TOKEN saknas"
    s = requests.Session()
    s.headers["Authorization"] = f"Bearer {token}"
    return s, ("https://sandbox.zenodo.org/api" if sandbox else "https://zenodo.org/api")


def new_version_draft(slug: str, sandbox: bool) -> dict:
    """A draft for a new version of the archived report (or the open draft if one exists); the version DOI is reserved."""
    rec = json.load(open(os.path.join(ROOT, "web", "content", "report_dois.json"), encoding="utf-8"))["rapporter"][slug]
    s, base = _session(sandbox)
    r = s.post(f"{base}/deposit/depositions/{rec['record'].rstrip('/').rsplit('/', 1)[1]}/actions/newversion")
    r.raise_for_status()
    d = s.get(r.json()["links"]["latest_draft"]).json()
    assert d.get("state") != "done" and not d.get("submitted"), f"utkastet {d.get('id')} är redan publicerat"
    doi = (d["metadata"].get("prereserve_doi") or {}).get("doi") or f"10.5281/zenodo.{d['id']}"
    out = {"slug": slug, "draft_id": d["id"], "doi": doi, "concept_doi": rec["concept_doi"], "previous": rec["doi"],
           "html": d["links"].get("html"), "files": [f["filename"] for f in d.get("files", [])]}
    json.dump(out, open(os.path.join(OUT, slug, "ny_version.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return out


def fill_new_version(slug: str, sandbox: bool) -> dict:
    """Replaces the files carried over from the previous version with the new PDFs and sets the new metadata."""
    folder = os.path.join(OUT, slug)
    nv = json.load(open(os.path.join(folder, "ny_version.json"), encoding="utf-8"))
    md = json.load(open(os.path.join(folder, "metadata.json"), encoding="utf-8"))
    s, base = _session(sandbox)
    url = f"{base}/deposit/depositions/{nv['draft_id']}"
    d = s.get(url).json()
    for f in d.get("files", []):
        s.delete(f"{url}/files/{f['id']}").raise_for_status()
    pdfs = sorted(f for f in os.listdir(folder) if f.endswith(".pdf"))
    for f in pdfs:
        with open(os.path.join(folder, f), "rb") as fh:
            s.put(f"{d['links']['bucket']}/{f}", data=fh).raise_for_status()
    md["metadata"]["prereserve_doi"] = d["metadata"].get("prereserve_doi")
    md["metadata"] = {k: v for k, v in md["metadata"].items() if v is not None}
    s.put(url, json=md).raise_for_status()
    d = s.get(url).json()
    return {"draft_id": nv["draft_id"], "doi": nv["doi"], "files": [f["filename"] for f in d.get("files", [])],
            "version": d["metadata"].get("version"), "publication_date": d["metadata"].get("publication_date"),
            "html": d["links"].get("html")}


def main(argv=None) -> int:
    a = argparse.ArgumentParser()
    a.add_argument("--bara-metadata", action="store_true")
    a.add_argument("--ladda-upp", action="store_true")
    a.add_argument("--sandlada", action="store_true")
    a.add_argument("--vitki-doi")
    a.add_argument("--slug", help="bara en rapport")
    a.add_argument("--ny-version", action="store_true", help="ny version av en arkiverad rapport (kräver --slug)")
    o = a.parse_args(argv)
    if o.ny_version:
        assert o.slug, "--ny-version kräver --slug"
        os.makedirs(os.path.join(OUT, o.slug), exist_ok=True)
        print(json.dumps(fill_new_version(o.slug, o.sandlada) if o.ladda_upp else new_version_draft(o.slug, o.sandlada),
                         ensure_ascii=False, indent=1))
        return 0
    rs = [p for p in reports() if not o.slug or p["slug"] == o.slug]
    # a report whose builder output (utdata/rapporter) has a higher version than the published one must be put live
    # first (utdata/blogg/build/patch_rapporter_live.py), or the PDFs would archive the old text
    local = {}
    for f in os.listdir(os.path.join(ROOT, "utdata", "rapporter")):
        if f.startswith("rapport") and f.endswith(".json"):
            d = json.load(open(os.path.join(ROOT, "utdata", "rapporter", f), encoding="utf-8"))
            local[d["slug"]] = (f, int(header(d["body_en"])["version"]))
    stale = [f"{p['slug']} (publicerad v{header(p['body_en'])['version']}, {local[p['slug']][0]} v{local[p['slug']][1]})"
             for p in rs if p["slug"] in local and local[p["slug"]][1] > int(header(p["body_en"])["version"])]
    if stale:
        print("Rättade versioner är inte publicerade än – kör först utdata/blogg/build/patch_rapporter_live.py:\n  "
              + "\n  ".join(stale), file=sys.stderr)
        return 1
    jobs = []
    for p in rs:
        folder = os.path.join(OUT, p["slug"])
        os.makedirs(folder, exist_ok=True)
        md = metadata(p, o.vitki_doi)
        json.dump(md, open(os.path.join(folder, "metadata.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        jobs += [(f"{APP}/en/forskningsrapporter/{p['slug']}", os.path.join(folder, f"{p['slug']}_en.pdf")),
                 (f"{APP}/forskningsrapporter/{p['slug']}", os.path.join(folder, f"{p['slug']}_sv.pdf"))]
        print(p["slug"], "–", md["metadata"]["version"], md["metadata"]["publication_date"], len(md["metadata"]["keywords"]), "nyckelord")
    if not o.bara_metadata and not o.ladda_upp:
        js = os.path.join(OUT, "_pdf.mjs")
        open(js, "w").write(PDF_JS % os.path.join(ROOT, "web", "node_modules", "playwright", "index.mjs"))
        subprocess.run(["node", js, json.dumps(jobs)], check=True)
    if o.ladda_upp:
        for p in rs:
            folder = os.path.join(OUT, p["slug"])
            md = json.load(open(os.path.join(folder, "metadata.json"), encoding="utf-8"))
            print("utkast:", upload(p["slug"], md, folder, o.sandlada))
    return 0


if __name__ == "__main__":
    sys.exit(main())
