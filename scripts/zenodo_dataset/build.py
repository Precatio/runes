"""Bygger ett Zenodo-dataset per arkiverad forskningsrapport: analysplanerna med kontrollsummor, koden, resultatfilerna
och tabellerna per sten, i /Volumes/2TB/Antigrvity/Runes/zenodo/dataset/<slug>/ (utanför repot). Viktor 2026-11-10:
"varje forskningsrapport får sina data som eget dataset på Zenodo; data blir citerade". Inget laddas upp här; det gör
scripts/zenodo_dataset/ladda_upp.py.

    python3 scripts/zenodo_dataset/build.py              # alla rapporter i spec.py
    python3 scripts/zenodo_dataset/build.py SLUG [SLUG]  # bara de rapporterna
    python3 scripts/zenodo_dataset/oversikt.py           # skriver dataset/OVERSIKT.md ur senaste bygget

Per rapport skrivs README.md (engelska + ett stycke på svenska), MANIFEST.json (källsökväg, commit, storlek, SHA-256 och
licens per fil), zenodo_metadata.json, data_and_code.zip (Zenodo har inga mappar) och repo/ med samma filer uppackade i
repots mappstruktur. Filerna tas ur git: delad kod (src/, r/, scripts/, data/, web/, METHODS.md) ur analysens commit,
rapportens egna filer ur commiten för den arkiverade rapportversionen; data/cache/ (git-ignorerad) kopieras från disk.
Den frysta korpusen tas med som corpus_subset.csv (signum och de kolumner koden läser) eller, med full=True i spec.py,
som hela corpus.csv (när planen låser filens SHA-256). Varje fil får en licens: kod GPL-3.0, tabeller per sten ur Rundata
ODbL 1.0, Vitkis egna resultat och planer CC BY 4.0.

Ny rapport: lägg en post REPORTS["<slug>"] i spec.py (slugen måste stå i web/content/report_dois.json, alltså vara
arkiverad på Zenodo) med
  json      rapportfilen i utdata/rapporter/,
  archive   commiten för den arkiverade rapportversionen, analysis  commiten där analysen kördes (står under Data och kod),
  files     varje fil rapporten nämner: planer + .sha256, skript, resultat, tabeller per sten, ev. data/cache/r/corpus/<fp>/…;
            en sträng räcker om DESC/CACHE_DESC har en beskrivning, annars (sökväg, "en rad på engelska"),
  globs     (mönster, beskrivning med {stone}) för filer per sten, file_commit  undantag från commit-regeln ("disk" = från disk),
  corpus    dict(fp=…, scan=[skript som läser corpus.csv], note=…, full=False) eller None med corpus_note,
  inputs    nycklar i TP för indata från andra källor som inte tas med, reproduce  kommandona, repro_note,
  excluded_extra / uncertain_extra  det som lämnats utanför och öppna licensfrågor.
Kör build.py SLUG, läs README.md och kontrollera varningarna (MISSING/WARN), kör oversikt.py och sedan ladda_upp.py.
Bygg utan artikelbyggare (utdata/blogg/build/), upphovsrättsskyddad text, .env eller filer över 50 MB.
"""
import csv
import glob
import hashlib
import html
import io
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spec import REPORTS, DESC, CACHE_DESC, TP, GH  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = "/Volumes/2TB/Antigrvity/Runes/zenodo/dataset"
SUMMARY = "/Volumes/2TB/Antigrvity/Runes/zenodo/dataset_bygge.json"  # senaste bygget, läses av oversikt.py
SOFTWARE_DOI = "10.5281/zenodo.24004432"
MAX = 50 * 1024 * 1024
CREATOR = {"name": "Kvant, Viktor", "affiliation": "Independent researcher", "orcid": "0009-0005-3886-6007"}
SHARED = ("src/", "r/", "scripts/", "data/", "web/", "METHODS.md")
SIG = re.compile(r"(?<![A-Za-zÅÄÖåäö])(U|Sö|Ög|Sm|Vg|Öl|Gs|Hs|M|Nä|Vs|D|Bo|Gö|Ds|J|G|Hä|Lp|Bl|DR|N)[ _](?:Fv|ATA|NOR|SHM|\d)")
STRICT = {"words", "pairs", "normalization"}
RUNDATA_ATTR = "Samnordisk runtextdatabas, Institutionen för nordiska språk, Uppsala universitet"

DOIS = json.load(open(os.path.join(ROOT, "web/content/report_dois.json"), encoding="utf-8"))["rapporter"]
POSTS = {p["slug"]: p for p in json.load(open(os.path.join(ROOT, "web/content/articles.json"), encoding="utf-8"))["posts"]}


def git(*a, check=True):
    r = subprocess.run(["git", "-C", ROOT, *a], capture_output=True)
    if check and r.returncode:
        raise RuntimeError(r.stderr.decode()[:300])
    return r


def show(commit, path):
    r = git("show", f"{commit}:{path}", check=False)
    return r.stdout if r.returncode == 0 else None


def sha(b):
    return hashlib.sha256(b).hexdigest()


def header(body_en):
    line = body_en.strip().splitlines()[0].strip("* ")
    k = re.search(r"Keywords: ([^.]+)\.", line)
    v = re.search(r"Report version (\d+), (\d{4}-\d{2}-\d{2})", line)
    return {"keywords": [x.strip() for x in k.group(1).split(",") if x.strip()] if k else [],
            "version": v.group(1) if v else "", "date": v.group(2) if v else ""}


def licence(path, data):
    name = os.path.basename(path)
    if path.endswith((".py", ".R", ".sh")):
        return "GPL-3.0"
    if path == "METHODS.md":
        return "GPL-3.0 (repository documentation)"
    if path.startswith("analysplaner/") or name.startswith("analysplan") or name.endswith(".sha256") or name.startswith("MALL"):
        return "CC BY 4.0"
    if name.endswith(("_feats_e.json", "_grooves.json")):
        return "CC BY 4.0 (measured from the 3D scans of Kitzler Åhfeldt 2024, CC BY 4.0)"
    if name.startswith("sexarsgard_1314"):
        return "CC BY 4.0 (derived from SDHK, Riksarkivet, CC BY 4.0)"
    if path in ("data/geo/socknar_land.csv", "web/src/lib/historiska_land.json"):
        return "CC BY 4.0 (derived from ISOF, CC BY 4.0, and Wikidata, CC0) - UNCERTAIN, see README"
    if name.endswith((".log", "_params.json", "done.json", "sessionInfo.txt")):
        return "CC BY 4.0"
    text = data.decode("utf-8", "ignore")
    per_stone = (name.endswith(".csv") and "signum" in text.split("\n", 1)[0]) or len(SIG.findall(text)) >= 20
    if per_stone:
        extra = ""
        if path == "utdata/strand/stenar.csv":
            extra = "; distances computed from SGU's shore displacement model, CC BY 4.0"
        elif path in ("utdata/riktning/stenar.csv", "utdata/familjens_plats/stenar.csv"):
            extra = "; includes values from Kulturmiljöregistret, CC0"
        return f"ODbL 1.0 (per-stone table derived from Rundata{extra})"
    return "CC BY 4.0"


def category(path):
    n = os.path.basename(path)
    if path.startswith("analysplaner/") or n.startswith("analysplan") or n.startswith("MALL"):
        return "Analysis plans and template"
    if n.endswith((".py", ".R", ".sh")):
        return "Code"
    if n == "METHODS.md":
        return "Documentation"
    if n.endswith((".log", "_params.json", "done.json", "sessionInfo.txt")):
        return "Run records"
    if path.startswith("data/") and not path.startswith("data/cache/"):
        return "Hand codings and inputs"
    if path.startswith(("web/", "data/geo/")) or path.startswith("utdata/brittiska/"):
        return "Hand codings and inputs"
    return "Results and per-stone tables"


def describe(path, given):
    if given:
        return given
    if path in DESC:
        return DESC[path]
    m = re.match(r"data/cache/r/corpus/[0-9a-f]{16}/(.*)$", path)
    if m:
        rest = m.group(1)
        if rest in CACHE_DESC:
            return CACHE_DESC[rest]
        if rest.endswith("_params.json"):
            return f"Parameters passed to the {rest[:-12]} R module (paths, seed)"
        if rest.endswith(".log"):
            return f"Log of the {rest[:-4]} R module run"
    raise KeyError(f"no description for {path}")


def corpus_columns(header_cols, texts):
    blob = "\n".join(texts)
    keep = ["signum"]
    # columns chosen by name pattern: "trait_"/f"trait_{..}", regexes like "^pm_", and r/common.R's trait_cols()/cat_cols()
    prefixes = [p for p in ("trait_", "cat_", "pm_", "dot_")
                if re.search(r"""["'`]\^?""" + p + r"""["'{]|""" + p + r"""\{|""" + p + r"""cols\(""", blob)]
    for c in header_cols:
        if c == "signum":
            continue
        if c in STRICT:  # generic words: only quoted names or R's $name count as a use of the column
            hit = re.search(r"""["']""" + re.escape(c) + r"""["']|\$""" + re.escape(c) + r"(?![A-Za-z0-9_])", blob)
        else:
            hit = re.search(r"(?<![A-Za-z0-9_])" + re.escape(c) + r"(?![A-Za-z0-9_])", blob)
        if any(c.startswith(p) for p in prefixes) or hit:
            keep.append(c)
    return keep, prefixes


def build(slug):
    S = REPORTS[slug]
    rep = json.load(open(os.path.join(ROOT, S["json"]), encoding="utf-8"))
    post = POSTS[slug]
    assert rep["title_en"] == post["title_en"]
    dois = DOIS[slug]
    hdr = header(post["body_en"])
    out = os.path.join(OUT, slug)
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(os.path.join(out, "repo"))
    archive, analysis = S["archive"], S["analysis"]
    fc = S.get("file_commit", {})

    entries = []
    for f in S["files"]:
        entries.append(f if isinstance(f, tuple) else (f, None))
    for pat, tmpl in S.get("globs", []):
        for p in sorted(glob.glob(os.path.join(ROOT, pat))):
            rel = os.path.relpath(p, ROOT)
            stone = os.path.basename(rel).replace("led_f_", "").replace("_feats_e.json", "").replace(".json", "").replace("_", " ")
            entries.append((rel, tmpl.format(stone=stone)))

    manifest, warnings, missing = [], [], []
    texts = {}
    seen = set()
    for path, given in entries:
        if path in seen:
            continue
        seen.add(path)
        disk = os.path.join(ROOT, path)
        if path.startswith("data/cache/") or fc.get(path) == "disk":
            commit = None
        else:
            commit = fc.get(path) or (analysis if path.startswith(SHARED) else archive)
        data, src_commit = None, None
        if commit:
            data = show(commit, path)
            src_commit = commit
            if data is None and commit != archive:
                data = show(archive, path)
                src_commit = archive
                if data is not None:
                    warnings.append(f"{path}: not in {commit}; taken from {archive}")
        if data is None:
            if os.path.isfile(disk):
                data = open(disk, "rb").read()
                if commit:
                    warnings.append(f"{path}: not in git at {commit}; copied from the working tree")
                src_commit = None
            else:
                missing.append(path)
                continue
        if len(data) > MAX:
            warnings.append(f"{path}: {len(data)} bytes > 50 MB, skipped")
            continue
        on_disk = open(disk, "rb").read() if os.path.isfile(disk) else None
        rec = {"path": "repo/" + path, "source": path, "commit": src_commit,
               "identical_to_working_tree_2026_11_10": (on_disk == data) if on_disk is not None else None,
               "bytes": len(data), "sha256": sha(data), "licence": licence(path, data),
               "category": category(path), "description": describe(path, given)}
        if src_commit and path.startswith("utdata/") and analysis != archive and src_commit == archive:
            if git("diff", "--quiet", analysis, archive, "--", path, check=False).returncode == 1 and show(analysis, path) is not None:
                rec["note"] = f"changed between the analysis commit {analysis} and the archive commit {archive}"
        dst = os.path.join(out, "repo", path)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "wb") as fh:
            fh.write(data)
        manifest.append(rec)
        if path.endswith((".py", ".R", ".sh")):
            texts[path] = data.decode("utf-8", "ignore")

    corpus_info = None
    if S.get("corpus"):
        cp = S["corpus"]
        full = os.path.join(ROOT, "data/cache/r/corpus", cp["fp"], "corpus.csv")
        raw = open(full, "rb").read()
        rows = list(csv.reader(io.StringIO(raw.decode("utf-8"))))
        hdr_cols = rows[0]
        scan = [texts[p] for p in cp["scan"] if p in texts]
        if len(scan) != len(cp["scan"]):
            warnings.append(f"corpus scan: {set(cp['scan']) - set(texts)} not in package")
        if cp.get("full"):  # the plan locks the file's SHA-256: ship the whole file so the hash can be checked
            cols, prefixes = list(hdr_cols), []
        else:
            cols, prefixes = corpus_columns(hdr_cols, scan)
        idx = [hdr_cols.index(c) for c in cols]
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator="\n")
        for r in rows:
            w.writerow([r[i] for i in idx])
        sub = raw if cp.get("full") else buf.getvalue().encode("utf-8")
        rel = f"data/cache/r/corpus/{cp['fp']}/" + ("corpus.csv" if cp.get("full") else "corpus_subset.csv")
        dst = os.path.join(out, "repo", rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, "wb").write(sub)
        corpus_info = {"full": bool(cp.get("full")), "fp": cp["fp"], "full_sha256": sha(raw), "full_bytes": len(raw), "full_cols": len(hdr_cols),
                       "rows": len(rows) - 1, "cols": cols, "prefixes": prefixes, "note": cp.get("note")}
        if cp.get("full"):
            manifest.append({"path": "repo/" + rel, "source": rel, "commit": None, "bytes": len(sub), "sha256": sha(sub),
                             "licence": "ODbL 1.0 (derived from Rundata)", "category": "Frozen corpus",
                             "description": CACHE_DESC["corpus.csv"] + f"; all {len(hdr_cols)} columns"})
        else:
            manifest.append({"path": "repo/" + rel, "source": f"data/cache/r/corpus/{cp['fp']}/corpus.csv (columns subset)",
                             "commit": None, "source_full_file_sha256": sha(raw), "bytes": len(sub), "sha256": sha(sub),
                             "licence": "ODbL 1.0 (derived from Rundata)", "category": "Frozen corpus",
                             "description": CACHE_DESC["corpus_subset.csv"] + f"; {len(cols)} of {len(hdr_cols)} columns"})

    manifest.sort(key=lambda r: r["path"])
    has_odbl = any(r["licence"].startswith("ODbL") for r in manifest)
    lic = "odbl-1.0" if has_odbl else "cc-by-4.0"
    has_plan = any("analysplan" in r["source"] for r in manifest)
    S["_has_plan"] = has_plan

    # ---- zip of repo/ (Zenodo has no folders) -------------------------------------------------------------------
    zpath = os.path.join(out, "data_and_code.zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for r in manifest:
            zi = zipfile.ZipInfo(r["path"], date_time=(2026, 11, 10, 0, 0, 0))
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            z.writestr(zi, open(os.path.join(out, r["path"]), "rb").read())

    title = f"Data and code for: {post['title_en']}"
    uncertain = list(S.get("uncertain_extra", []))
    for r in manifest:
        if "UNCERTAIN" in r["licence"] and not any(r["source"] in u for u in uncertain):
            uncertain.append(f"{r['source']}: {r['licence']}")
    if "runor" in S["inputs"]:
        uncertain.append("Runor (2020 edition), Riksantikvarieämbetet: the repository states no licence for the Runor data (data/raa/runor_2020.json is not included; per-stone tables here carry at most flags derived from it, e.g. the column moved_runor in robustness/data.csv). Licence: see source (runor.raa.se).")
    if "copernicus" in S["inputs"]:
        uncertain.append("Copernicus DEM GLO-30: referenced, not included; its licence (Copernicus DEM licence) is not stated in the repository.")
    if has_odbl:
        uncertain.append("The package mixes licences (ODbL 1.0 tables, GPL-3.0 code, CC BY 4.0 results). Zenodo takes one licence per record; odbl-1.0 is set because Rundata-derived tables are included, and README/MANIFEST give the licence of each file.")

    meta = {"metadata": {
        "upload_type": "dataset",
        "title": title,
        "creators": [CREATOR],
        "description": (f"<p>{'Locked analysis plans, code' if has_plan else 'Code'}, result files and per-stone tables behind the Vitki research report "
                        f"<em>{html.escape(post['title_en'])}</em> (report version {dois['version']}, "
                        f"<a href=\"https://doi.org/{dois['doi']}\">doi:{dois['doi']}</a>).</p>"
                        f"<p>The folder structure in data_and_code.zip mirrors the GitHub repository {GH}; README.md gives each file's "
                        f"description, source commit and licence, and how to rerun the analysis. Rundata-derived tables: ODbL 1.0, "
                        f"source {RUNDATA_ATTR}. Code: GPL-3.0. Vitki's own results and plans: CC BY 4.0.</p>"
                        f"<p><strong>Svenska:</strong> Data och kod till forskningsrapporten <em>{html.escape(post['title'])}</em>.</p>"),
        "access_right": "open",
        "license": lic,
        "keywords": hdr["keywords"] + ["research data", "Rundata", "reproducibility"],
        "language": "eng",
        "version": "1",
        "related_identifiers": [
            {"identifier": dois["doi"], "relation": "isSupplementTo", "scheme": "doi", "resource_type": "publication-report"},
            {"identifier": dois["concept_doi"], "relation": "isSupplementTo", "scheme": "doi", "resource_type": "publication-report"},
            {"identifier": SOFTWARE_DOI, "relation": "isSupplementTo", "scheme": "doi", "resource_type": "software"},
        ],
        "notes": f"Swedish title of the report: {post['title']}. Per-file licences in README.md and MANIFEST.json.",
    }}
    json.dump(meta, open(os.path.join(out, "zenodo_metadata.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    man = {"dataset": title, "report_slug": slug, "report_doi": dois["doi"], "report_concept_doi": dois["concept_doi"],
           "report_version": dois["version"], "software_doi": SOFTWARE_DOI, "repository": GH,
           "analysis_commit": analysis, "archive_commit": archive, "prepared": "2026-11-10",
           "repository_head_when_prepared": git("rev-parse", "--short", "HEAD").stdout.decode().strip(),
           "zip": {"file": "data_and_code.zip", "bytes": os.path.getsize(zpath), "sha256": sha(open(zpath, "rb").read())},
           "files": manifest}
    json.dump(man, open(os.path.join(out, "MANIFEST.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    readme(out, S, slug, post, dois, hdr, manifest, corpus_info, uncertain, lic, warnings)
    total = sum(r["bytes"] for r in manifest)
    return {"slug": slug, "n": len(manifest), "bytes": total, "zip": os.path.getsize(zpath), "licence": lic,
            "missing": missing, "warnings": warnings, "uncertain": uncertain,
            "excluded": [f"utdata/blogg/build/{os.path.basename(builder(slug))}"] + S.get("excluded_extra", []),
            "inputs": S["inputs"]}


def builder(slug):
    b = {"kvinnor-bland-resarna-svealand-gotaland": "kvinnor", "soner-och-broder-dog-utanfor-norden": "unga",
         "familjegrupper-vid-gravfalten": "familjens_plats", "upplands-folkland-skiljer-runstenarna": "folkland",
         "monoftongstavningen-blir-ovanligare": "monoftong", "barnen-arvde-namnled": "namnled", "r-for-yr-runan-vastra-uppland": "r_for_R",
         "ristningen-vand-mot-vagen": "riktning", "ristarforslag-blindprov": "ristarmodellen", "seriationen-foljer-stilkronologin": "seriation",
         "skanningen-som-ledtrad": "sparlasare", "runstenarna-vid-sin-tids-vatten": "strand"}[slug]
    return f"utdata/blogg/build/build_rapport_{b}.py"


def human(n):
    return f"{n / 1024 / 1024:.1f} MB" if n >= 1024 * 1024 else f"{n / 1024:.0f} kB"


def readme(out, S, slug, post, dois, hdr, manifest, ci, uncertain, lic, warnings):
    L = []
    a = L.append
    a(f"# Data and code for: {post['title_en']}\n")
    a(f"*Swedish title of the report: {post['title']}*\n")
    a(f"Dataset version 1, prepared 2026-11-10 by Viktor Kvant (independent researcher, ORCID [0009-0005-3886-6007](https://orcid.org/0009-0005-3886-6007)).\n")
    a("## The report\n")
    a(f"- Kvant, V. (2026). *{post['title_en']}*. Vitki research report, report version {dois['version']}.")
    a(f"- Report DOI (this version): [{dois['doi']}](https://doi.org/{dois['doi']})")
    a(f"- Concept DOI (all versions): [{dois['concept_doi']}](https://doi.org/{dois['concept_doi']})")
    a(f"- Online: https://vitkirunor.se/en/forskningsrapporter/{slug}")
    a(f"- Software: Vitki 3.1.0, [doi:{SOFTWARE_DOI}](https://doi.org/{SOFTWARE_DOI}); code on GitHub, {GH} (GPL-3.0)\n")
    a("## What is here\n")
    a(("The locked analysis plans with their checksums, the analysis code" if S["_has_plan"] else
       "The analysis code (this study has no locked analysis plan; the report's section 2 says what was fixed in advance)")
      + ", the result files and the per-stone tables that the report's numbers come from. "
      "The folder `repo/` mirrors the layout of the GitHub repository, so every path below is the "
      "path the report and the scripts use. On Zenodo the folder is packed as `data_and_code.zip` (Zenodo has no folders); "
      "`MANIFEST.json` lists every file with its source path, source commit, size, SHA-256 and licence.\n")
    commits = sorted({r["commit"] for r in manifest if r["commit"]})
    a(f"**Code state.** Shared code (`src/`, `r/`, `scripts/`, `data/`, `web/`, `METHODS.md`) is taken from the analysis commit "
      f"`{S['analysis']}`, the code state the report names for the analysis; report-specific files (plans, `utdata/…`) from "
      f"`{S['archive']}`, the commit of the archived report version, unless MANIFEST.json says otherwise. Commits used: "
      + ", ".join(f"`{c}`" for c in commits) + ". Files under `data/cache/` are not under version control and were copied "
      "from the working tree; their dates and the corpus fingerprint are in `done.json` where present.\n")
    noted = [r for r in manifest if r.get("note")]
    if noted:
        a("Files that changed between the analysis commit and the archive commit (the archive version is included): "
          + ", ".join(f"`{r['source']}`" for r in noted) + "." + (" " + S["change_note"] if S.get("change_note") else "") + "\n")
    later = [r["source"] for r in manifest if r.get("identical_to_working_tree_2026_11_10") is False]
    if later:
        a("Changed in the repository after the report (the copies here are the pinned versions, not the current ones): "
          + ", ".join(f"`{x}`" for x in later) + ".\n")
    a("## Files\n")
    cats = ["Analysis plans and template", "Code", "Documentation", "Hand codings and inputs", "Frozen corpus",
            "Results and per-stone tables", "Run records"]
    for c in cats:
        rows = [r for r in manifest if r["category"] == c]
        if not rows:
            continue
        a(f"### {c}\n")
        a("| File | Description | Licence | Size |")
        a("|---|---|---|---|")
        for r in rows:
            a(f"| `{r['path'][5:]}` | {r['description']} | {r['licence']} | {human(r['bytes'])} |")
        a("")
    if ci and ci["full"]:
        a("## The frozen corpus\n")
        a(f"`data/cache/r/corpus/{ci['fp']}/corpus.csv` is the frozen corpus the results are keyed to, included whole "
          f"({ci['rows']} rows, one per Swedish Viking-Age runestone, {ci['full_cols']} columns, {ci['full_bytes']:,} bytes) so that "
          f"the SHA-256 locked in the analysis plan can be checked: `{ci['full_sha256']}`. It is built by the analysis engine "
          "from `data/rundata.json` (`src/r_bridge.py`) and is not in the repository.\n")
        if ci.get("note"):
            a(ci["note"] + "\n")
    elif ci:
        a("## The frozen corpus\n")
        a(f"`data/cache/r/corpus/{ci['fp']}/corpus_subset.csv` is the frozen corpus the results are keyed to (fingerprint "
          f"`{ci['fp']}`), cut to the {len(ci['cols'])} of {ci['full_cols']} columns that the included scripts read "
          f"({ci['rows']} rows, one per Swedish Viking-Age runestone). The full file "
          f"(`data/cache/r/corpus/{ci['fp']}/corpus.csv`, {ci['full_bytes']:,} bytes) has SHA-256 `{ci['full_sha256']}`; it is "
          "built by the analysis engine from `data/rundata.json` (`src/r_bridge.py`) and is not in the repository. The columns "
          "were chosen by searching the included scripts for each column name"
          + (f" (all columns starting with {', '.join('`' + p + '`' for p in ci['prefixes'])} are kept because the code builds those names)" if ci['prefixes'] else "")
          + ". To run a script that expects `corpus.csv`, rename the subset or rebuild the full file with the engine.\n")
        if ci.get("note"):
            a(ci["note"] + "\n")
        a("Columns: " + ", ".join(f"`{c}`" for c in ci["cols"]) + "\n")
    elif S.get("corpus_note"):
        a("## The corpus\n")
        a(S["corpus_note"] + "\n")
    a("## How to reproduce\n")
    a(f"Paths assume the GitHub repository layout ({GH}) at the commits named here; release 3.1.0 (tag `v3.1.0`, commit `d81dfd9`, "
      f"2026-11-06, [doi:{SOFTWARE_DOI}](https://doi.org/{SOFTWARE_DOI})) contains the same layout"
      + (" but predates this report version, so use the commits below." if S["archive"] in ("deca8d4", "89a38c9") else ".") + "\n")
    a("```sh")
    for line in S["reproduce"]:
        a(line)
    a("```\n")
    if S.get("repro_note"):
        a(S["repro_note"] + "\n")
    a("Python scripts run from the project folder with the repository's virtual environment (`.venv`, `requirements.lock`); "
      "R scripts with R 4.6 (`sessionInfo.txt` where included).\n")
    a("## Inputs not included\n")
    a("| Input | Source | Licence | How to obtain |")
    a("|---|---|---|---|")
    for k in S["inputs"]:
        f, src, li, how = TP[k]
        a(f"| `{f}` | {src} | {li} | {how} |")
    a("")
    a("## Sources and licences\n")
    a(f"- **Rundata.** Tables derived from the Scandinavian Runic-text Database are licensed under the Open Database License "
      f"(ODbL 1.0); the contents under the Database Contents License (DbCL 1.0). Attribution: *{RUNDATA_ATTR}* "
      "(www.nordiska.uu.se/forskn/samnord.htm). Vitki's derived version merges the tables per signum, resolves aliases, "
      "structures the carver field and converts Swedish coordinates (RT90) to WGS 84 (`scripts/build_rundata.py`). Any "
      "redistributed adaptation of these tables must stay under ODbL 1.0.")
    if any(k in S["inputs"] for k in ("lamningar", "lamningar_extra", "kmr_runstenar", "gransmarken", "dims")):
        a("- **Kulturmiljöregistret via K-samsök** (Riksantikvarieämbetet): CC0. Values from it inside the per-stone tables are noted in the licence column.")
    if "sgu" in S["inputs"]:
        a("- **SGU** (Sveriges geologiska undersökning), shore displacement model: CC BY 4.0. The GeoPackages are referenced, not included; distances computed from them are in `utdata/strand/stenar.csv` and `resultat.json` (attribution: SGU).")
    if "runor" in S["inputs"]:
        a("- **Runor (2020 edition)**, Riksantikvarieämbetet (runor.raa.se): the repository states no licence for these data; see the source. The harvest itself is not included.")
    if "isof" in S["inputs"]:
        a("- **ISOF** (Institutet för språk och folkminnen), place-name register: CC BY 4.0; **Wikidata**: CC0.")
    if "osm" in S["inputs"]:
        a("- **OpenStreetMap** place names: ODbL 1.0, © OpenStreetMap contributors (referenced, not included). **Wikidata** churches: CC0.")
    if "scans" in S["inputs"]:
        a("- **3D scans**: Kitzler Åhfeldt, L. (2024), doi:10.5281/zenodo.11951255, CC BY 4.0 (Riksantikvarieämbetet). The scans are not included; the measured features derived from them are, under CC BY 4.0 with this attribution.")
    if any("sexarsgard" in r["path"] for r in manifest):
        a("- **SDHK** (Svenskt diplomatariums huvudkartotek, Riksarkivet), SDHK 2593: CC BY 4.0.")
    a("- **Code** (`.py`, `.R`, `.sh`) and `METHODS.md`: GPL-3.0 with the additional terms in the repository's `NOTICE`.")
    a("- **Vitki's own result files, plans and run records**: CC BY 4.0 (Viktor Kvant).")
    a(f"- **This Zenodo record** is filed under `{lic}`" + (" because it includes Rundata-derived tables; the licence of each file is given above and in `MANIFEST.json`." if lic == "odbl-1.0" else "."))
    a("")
    a("## Not included\n")
    a(f"- `{builder(slug)}`: article builder that turns the result files into the web report; in the GitHub repository.")
    a("- Report figures (PNG/WebP): they are in the archived report.")
    for x in S.get("excluded_extra", []):
        a(f"- {x}")
    a("")
    if uncertain:
        a("## Open questions on licences\n")
        for u in uncertain:
            a(f"- {u}")
        a("")
    a("## Svenska\n")
    a(f"Det här är data och kod till Vitkis forskningsrapport *{post['title']}* (rapportversion {dois['version']}, "
      f"doi:{dois['doi']}). Paketet innehåller " + ("de låsta analysplanerna med kontrollsummor, " if S["_has_plan"] else "") +
      "analyskoden, resultatfilerna och tabellerna per sten, i samma mappstruktur som GitHub-repot. Tabeller som bygger på Samnordisk runtextdatabas står under "
      f"ODbL 1.0 med källangivelsen *{RUNDATA_ATTR}*; koden under GPL-3.0; Vitkis egna resultat under CC BY 4.0. "
      "Filförteckningen ovan anger källa och licens för varje fil.\n")
    a("## How to cite\n")
    a(f"Kvant, V. (2026). *Data and code for: {post['title_en']}* (Version 1) [Data set]. Zenodo. "
      "(DOI assigned on publication.) Please also cite the report and, for Rundata-derived tables, the Samnordisk runtextdatabas.\n")
    open(os.path.join(out, "README.md"), "w", encoding="utf-8").write("\n".join(L))


if __name__ == "__main__":
    slugs = sys.argv[1:] or sorted(REPORTS)
    assert set(REPORTS) == set(DOIS), set(REPORTS) ^ set(DOIS)
    res = []
    for s in slugs:
        r = build(s)
        res.append(r)
        print(f"{s}: {r['n']} files, {human(r['bytes'])}, zip {human(r['zip'])}, {r['licence']}")
        for m in r["missing"]:
            print("   MISSING", m)
        for w in r["warnings"]:
            print("   WARN", w)
    json.dump(res, open(SUMMARY, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
