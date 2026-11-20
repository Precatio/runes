"""Vitki's fillings in R: only as an opt-in check (with_vitki_fills in R/vitki_fills.R), never in corpus.csv, and refused by
the modules that measure what the probability model builds its fillings on (METHODS 8.1)."""
import csv
import io
import os
import shutil
import subprocess

import pytest

from src import r_bridge, vitki_fills

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _store(tmp_path):
    p = str(tmp_path / "f.json")
    user = {"uid": "u", "email": "admin@example.org"}
    gap = {"key": "0:1:4", "width": 3, "start": 1, "end": 4, "carved": "h???tian"}
    for fill, word, status in (("alf", "halfdan", "bekräftad"), ("ouk", "x", "förslag")):
        gap = {**gap, "key": f"0:1:4{fill}"}
        vitki_fills.add({"signum": "U 657", "gap": gap, "fill": fill, "word": word, "name": word == "halfdan",
                         "method": "sannolikhetsmodellen", "status": status, "comment": "prov", "p": 0.98}, user, p)
    return p


def test_fills_csv_is_one_row_per_filling(tmp_path):
    rows = list(csv.DictReader(io.StringIO(r_bridge._fills_csv(_store(tmp_path)))))
    assert list(rows[0]) == r_bridge.FILLS_COLUMNS
    assert {(r["word"], r["status"], r["name"]) for r in rows} == {("halfdan", "bekräftad", "1"), ("x", "förslag", "0")}


def test_corpus_has_no_fillings_column():
    assert not any("vitki" in c for c in r_bridge.CSV_COLUMNS)


def test_no_module_calls_with_vitki_fills_by_default():
    for f in os.listdir(r_bridge.R_DIR):
        if f.endswith(".R") and f not in ("common.R", "vitki_fills.R"):
            assert "with_vitki_fills(" not in open(os.path.join(r_bridge.R_DIR, f), encoding="utf-8").read(), f


@pytest.mark.skipif(not (r_bridge.rscript() or shutil.which("Rscript")), reason="R saknas")
def test_r_adds_confirmed_words_once_and_refuses_forbidden_modules(tmp_path):
    fills = tmp_path / "f.csv"
    fills.write_text(r_bridge._fills_csv(_store(tmp_path)), encoding="utf-8")
    script = tmp_path / "t.R"
    script.write_text(f'''
source("{os.path.join(r_bridge.R_DIR, "vitki_fills.R")}")
d <- data.frame(signum = c("U 657", "U 1"), normalization = c("... ok Gunnarr", NA), stringsAsFactors = FALSE)
f <- read_vitki_fills("{fills}")
stopifnot(nrow(f) == 1)                                   # förslag never counted
x <- with_vitki_fills(d, f, "words")
stopifnot(x$normalization[1] == '... ok Gunnarr "Halfdan', x$vitki_filled[1] == 1, is.na(x$normalization[2]))
y <- with_vitki_fills(x, f, "words")                      # already there: not added twice
stopifnot(y$vitki_filled[1] == 0)
for (m in c("names", "text", "messages", "dialect", "attribution", "anonymous", "network"))
  stopifnot(inherits(tryCatch(with_vitki_fills(d, f, m), error = function(e) e), "error"))
cat("ok")
''', encoding="utf-8")
    r = subprocess.run([r_bridge.rscript() or "Rscript", "--vanilla", str(script)], capture_output=True, text=True, timeout=120)
    assert r.stdout.strip().endswith("ok"), r.stderr
