"""Lägger de arkiverade forskningsrapporternas PDF:er på webbplatsen, så att Google Scholar hittar en PDF på samma
webbplats som rapportsidan (metataggen citation_pdf_url, web/src/lib/report.ts) och läsaren kan ladda ned den.
Läser web/content/report_dois.json (vilken version som är arkiverad på Zenodo) och PDF:erna som
scripts/zenodo_rapporter.py skrev i /Volumes/2TB/Antigrvity/Runes/zenodo/rapporter/<slug>/; kopierar dem till
web/public/forskningsrapporter-pdf/<slug>-v<version>-<sv|en>.pdf och skriver web/content/report_pdfs.json.
Bara PDF:er vars metadata.json har samma version som det arkiverade DOI:t läggs ut. Körs efter varje ny Zenodo-version.
Viktor 2026-11-10: "se till så att detta görs på alla forskningsrapporter".
    .venv/bin/python scripts/rapport_pdf_webb.py"""
import json
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = "/Volumes/2TB/Antigrvity/Runes/zenodo/rapporter"
DOIS = os.path.join(ROOT, "web", "content", "report_dois.json")
DEST = os.path.join(ROOT, "web", "public", "forskningsrapporter-pdf")
MANIFEST = os.path.join(ROOT, "web", "content", "report_pdfs.json")
URL = "/forskningsrapporter-pdf"


def main():
    dois = json.load(open(DOIS, encoding="utf-8"))["rapporter"]
    os.makedirs(DEST, exist_ok=True)
    out, keep = {}, set()
    for slug, a in sorted(dois.items()):
        folder = os.path.join(SRC, slug)
        meta = os.path.join(folder, "metadata.json")
        if not os.path.exists(meta):
            print("saknar PDF-mapp:", slug)
            continue
        m = json.load(open(meta, encoding="utf-8"))
        ver = str((m.get("metadata", m)).get("version", "")).split()[-1]
        if ver != str(a["version"]):
            print(f"{slug}: PDF:erna är version {ver}, arkivet {a['version']} – hoppar över")
            continue
        entry = {"version": a["version"]}
        for lang in ("sv", "en"):
            src = os.path.join(folder, f"{slug}_{lang}.pdf")
            if not os.path.exists(src):
                continue
            name = f"{slug}-v{a['version']}-{lang}.pdf"
            dst = os.path.join(DEST, name)
            if not os.path.exists(dst) or os.path.getsize(dst) != os.path.getsize(src):
                shutil.copyfile(src, dst)
            keep.add(name)
            entry[lang] = {"url": f"{URL}/{name}", "bytes": os.path.getsize(src)}
        if "sv" in entry or "en" in entry:
            out[slug] = entry
    for f in os.listdir(DEST):  # older versions' PDFs leave the site; Zenodo keeps them
        if f.endswith(".pdf") and f not in keep:
            os.remove(os.path.join(DEST, f))
    json.dump({"_om": "Rapporternas PDF:er på webbplatsen (scripts/rapport_pdf_webb.py), samma version som på Zenodo. "
               "Används av web/src/lib/report.ts för citation_pdf_url och nedladdningslänken.", "rapporter": out},
              open(MANIFEST, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(out), "rapporter,", len(keep), "PDF:er i", DEST)


if __name__ == "__main__":
    main()
