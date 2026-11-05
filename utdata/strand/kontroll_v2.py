"""Kontroll inför rapportversion 2 av strandrapporten (2026-11-05). Rör inte den låsta analysen eller dess resultatfiler;
läser dem och korpusfilerna och skriver vad som gäller för stenarna i urvalet, kartorna och tidsordningen till
utdata/strand/kontroll_v2.json, som rapportbyggaren (utdata/blogg/build/build_rapport_strand.py) asserterar mot.

- Korpusen: planen låste d6cffd1578418f74, vars mapp inte finns kvar i cachen (sökvägen i config.R är död); samma CSV
  finns under 5fdfd1e095bfb6fb med den SHA-256 som planen anger.
- Urvalet (1 099 stenar, moved = 0 i den låsta korpusen): hur många som är försvunna (lost = 1) och hur många som räknas
  som flyttade med den rättade flyttregeln (commit 07d2ec0, 2026-10-27; korpus e83202e01a5e6d27), totalt och inom de två
  kartorna ur 06_illustration.R.
- Tidsordningen: provkörningens logg (run.log), avståndens och statistikens loggar i cachen.
    .venv/bin/python utdata/strand/kontroll_v2.py
"""
import csv
import datetime as dt
import hashlib
import json
import os
import re
import subprocess

from pyproj import Transformer

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SD = os.path.join(ROOT, "utdata", "strand")
CACHE = "/Volumes/2TB/cache/strand"
LOCKED_FP, NOW_FP, KEPT_FP = "d6cffd1578418f74", "e83202e01a5e6d27", "5fdfd1e095bfb6fb"
PROVS = ["U", "Sö", "Ög", "Sm", "Vg", "Öl"]
MX = (500000, 730000, 6480000, 6740000)  # översiktskartan i 06_illustration.R
WIN = (644000, 656000, 6610000, 6622000)  # detaljkartan (illustration.json, "window")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def stamp(t):
    return dt.datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M:%S")


def times(path):
    s = os.stat(path)
    return {"created": stamp(s.st_birthtime), "modified": stamp(s.st_mtime)}


def read(path):
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


plan = open(os.path.join(ROOT, "analysplaner", "2026-10-23-strand-och-gravfalt.md"), encoding="utf-8").read()
plan_csv_sha = re.search(r"`" + LOCKED_FP + r"` \(samma fil i den senaste körningen\s+`" + KEPT_FP + r"`\), SHA-256 `([0-9a-f]{64})`",
                         plan).group(1)
config = open(os.path.join(SD, "config.R"), encoding="utf-8").read()
config_corpus = re.search(r'CORPUS <- file.path\(REPO, "([^"]+)"\)', config).group(1)
kept_csv = os.path.join(ROOT, "data", "cache", "r", "corpus", KEPT_FP, "corpus.csv")
now_csv = os.path.join(ROOT, "data", "cache", "r", "corpus", NOW_FP, "corpus.csv")
corpus = {"locked_fingerprint": LOCKED_FP, "config_path": config_corpus,
          "config_path_exists": os.path.exists(os.path.join(ROOT, config_corpus)),
          "locked_folder_exists": os.path.isdir(os.path.join(ROOT, "data", "cache", "r", "corpus", LOCKED_FP)),
          "kept_fingerprint": KEPT_FP, "kept_csv_sha256": sha256(kept_csv), "plan_csv_sha256": plan_csv_sha,
          "now_fingerprint": NOW_FP, "now_csv_sha256": sha256(now_csv)}
corpus["kept_csv_is_plan_csv"] = corpus["kept_csv_sha256"] == plan_csv_sha
assert corpus["kept_csv_is_plan_csv"] and not corpus["config_path_exists"] and not corpus["locked_folder_exists"]

# ---- the 1 099 stones, as load_stones() + moved == 0 in config.R / 03_statistik.R ---------------------------------------
locked = read(kept_csv)
now = {r["signum"]: r for r in read(now_csv)}
sel = [r for r in locked if r["lat"] and r["lon"] and r["province"] in PROVS and r["moved"] in ("", "0")]
saved = {r["signum"] for r in read(os.path.join(SD, "stenar.csv"))}
assert {r["signum"] for r in sel} == saved and len(sel) == len(saved)
lost_locked = {r["signum"] for r in sel if r["lost"] not in ("", "0")}
lost_now = {r["signum"] for r in sel if now[r["signum"]]["lost"] not in ("", "0")}
moved_now = {r["signum"] for r in sel if now[r["signum"]]["moved"] not in ("", "0")}
missing_now = {r["signum"] for r in sel if r["signum"] not in now}
either = lost_now | moved_now | missing_now
runor = json.load(open(os.path.join(ROOT, "data", "raa", "runor_2020.json"), encoding="utf-8"))
runor = runor if isinstance(runor, list) else runor["inscriptions"]
moved_runor = {x["signum"] for x in runor if x.get("original") is False}
stays_now = {r["signum"] for r in sel} - either
stones = {"n": len(sel), "same_as_stenar_csv": True, "lost_locked": len(lost_locked), "lost_now": len(lost_now),
          "lost_same_in_both": lost_locked == lost_now, "moved_corrected_rule": len(moved_now),
          "lost_and_moved": sorted(lost_now & moved_now), "missing_in_now": len(missing_now),
          "lost_or_moved": len(either), "stays_corrected_rule": len(stays_now),
          "t1_stays_and_not_runor": len(stays_now - moved_runor), "moved_runor": len({r["signum"] for r in sel} & moved_runor)}

# Cross-checks against the saved results of the locked run (not changed here)
TR = json.load(open(os.path.join(SD, "trappan.json"), encoding="utf-8"))
RES = json.load(open(os.path.join(SD, "resultat.json"), encoding="utf-8"))
assert stones["lost_or_moved"] == TR["counts"]["not_staying_now"]
assert stones["stays_corrected_rule"] == TR["H1"]["rungs"]["dagens_flyttregel"]["n_stones"] == TR["H3"]["rungs"]["dagens_flyttregel"]["n_stones"]
assert stones["t1_stays_and_not_runor"] == RES["T1"]["n"] and stones["moved_runor"] == TR["counts"]["moved_runor"]

# ---- the two maps of 06_illustration.R (SWEREF 99 TM, strict bounds as in the R script) -----------------------------------
T = Transformer.from_crs(4326, 3006, always_xy=True)


def in_box(r, b):
    x, y = T.transform(float(r["lon"]), float(r["lat"]))
    return b[0] < x < b[1] and b[2] < y < b[3]


IL = json.load(open(os.path.join(SD, "illustration.json"), encoding="utf-8"))
assert tuple(IL["window"]) == WIN
maps = {}
for key, box, n_fig in (("overview", MX, IL["n_overview"]), ("detail", WIN, IL["n_stones"])):
    s = {r["signum"] for r in sel if in_box(r, box)}
    assert len(s) == n_fig, (key, len(s), n_fig)
    maps[key] = {"n": len(s), "lost": len(s & lost_now), "moved_corrected_rule": len(s & moved_now),
                 "lost_or_moved": len(s & either)}
maps["legend_sv"] = {"overview": "Runstenar som står kvar och ingår i studien (%d)" % IL["n_overview"],
                     "detail": "Runsten som står kvar (%d)" % IL["n_stones"]}
legend_src = open(os.path.join(SD, "06_illustration.R"), encoding="utf-8").read()
assert '"Runstenar som står kvar och ingår i studien (%d)"' in legend_src and '"Runsten som står kvar (%d)"' in legend_src

# ---- the order of events (logs in the cache; the cache is not in the repository) ----------------------------------------
# File times are those on the machine where the study was run; a fresh clone has new times, so kontroll_v2.json is the record.
run_log = open(os.path.join(CACHE, "run.log"), encoding="utf-8").read().splitlines()
done = [ln.strip() for ln in run_log if re.search(r"klar[at]?\b", ln)]
progress = [re.sub(r"^\d+ s\s+", "", ln.strip()) for ln in done]
commit = subprocess.run(["git", "show", "-s", "--format=%ci", "c0afbc8"], cwd=ROOT, capture_output=True, text=True,
                        check=True).stdout.strip()
order = {
    "plan_sha256_file": times(os.path.join(ROOT, "analysplaner", "2026-10-23-strand-och-gravfalt.sha256")),
    "plan_commit_c0afbc8": commit,
    "trial_run_log": times(os.path.join(CACHE, "run.log")),
    "trial_run_done_lines": progress,
    "trial_run_done_lines_have_numbers": any(re.search(r"\d", re.sub(r"\bH\d\b", "", p)) for p in progress),  # H1–H3 are names
    # files in the cache (also work/ and tmp/) written while the trial run ran, or within five minutes after it
    "trial_run_other_files_in_cache": sorted(
        os.path.relpath(os.path.join(dp, f), CACHE) for dp, _, fs in os.walk(CACHE) for f in fs if f != "run.log"
        and os.stat(os.path.join(CACHE, "run.log")).st_birthtime <= os.stat(os.path.join(dp, f)).st_mtime
        <= os.stat(os.path.join(CACHE, "run.log")).st_mtime + 300),
    "distances_log": times(os.path.join(CACHE, "steg1.log")),
    "distances_files": sorted({stamp(os.stat(os.path.join(CACHE, "work", f)).st_mtime)[:10]
                               for f in os.listdir(os.path.join(CACHE, "work")) if f.endswith("_avstand.rds")}),
    "statistics_log": times(os.path.join(CACHE, "steg3.log")),
    "statistics_computed_at": RES["computed_at"],
}
assert order["trial_run_done_lines"] == ["H1 klart", "H2 klart", "H3 klart", "sekundära prov klara"]
assert not order["trial_run_done_lines_have_numbers"] and not order["trial_run_other_files_in_cache"]
assert order["plan_sha256_file"]["created"] < order["trial_run_log"]["created"] < order["trial_run_log"]["modified"] < commit[:19]
assert order["distances_files"] == ["2026-10-23"] and order["statistics_computed_at"].startswith("2026-10-31")

out = {"script": "utdata/strand/kontroll_v2.py", "computed_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
       "corpus": corpus, "stones": stones, "maps": maps, "order": order}
with open(os.path.join(SD, "kontroll_v2.json"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1))
