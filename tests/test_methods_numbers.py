"""METHODS.md:s siffror ska stämma med analysfilerna, som artikelbyggarna gör med sina asserts. Testen hoppar över
när underlaget inte finns på maskinen (korpusanalyserna ligger i data/cache, som inte är i git)."""
import glob
import json
import os
import re

import pytest

ROOT = os.path.join(os.path.dirname(__file__), "..")
METHODS = open(os.path.join(ROOT, "METHODS.md"), encoding="utf-8").read()


def latest_run(module: str) -> dict | None:
    runs = []
    for done in glob.glob(os.path.join(ROOT, "data", "cache", "r", "corpus", "*", "done.json")):
        p = os.path.join(os.path.dirname(done), f"{module}.json")
        if os.path.exists(p):
            runs.append((os.path.getmtime(done), p))
    return json.load(open(max(runs)[1], encoding="utf-8")) if runs else None


def test_unknown_carvers_numbers_in_methods_1g():
    a = latest_run("anonymous")
    if not a:
        pytest.skip("ingen korpusanalys på maskinen")
    sec = METHODS.split("### 1g. Okända ristare", 1)[1].split("\n### ", 1)[0]
    m = re.search(r"blev det (\d+) grupper, varav (\d+) möjliga okända ristare", sec)
    assert m, "1g saknar meningen om antal grupper"
    assert (int(m.group(1)), int(m.group(2))) == (len(a["groups"]), a["n_candidates"])
    for g in a["groups"]:
        if g.get("status") == "candidate" and g.get("name"):
            assert g["name"] in sec, g["name"]
            # "(28 stenar, Östergötland)", "(14, Småland)" or "(6 vardera, Västergötland)"
            assert re.search(rf"\({g['n']}[\s,]", sec), f"{g['name']}: {g['n']} stenar saknas i 1g"


def test_textmodel_candidates_file_is_consistent():
    p = os.path.join(ROOT, "data", "textmodel_candidates.json")
    if not os.path.exists(p):
        pytest.skip("kandidatlistan är inte byggd")
    d = json.load(open(p, encoding="utf-8"))
    assert d["counts"]["candidates"] == len(d["candidates"])
    assert all(c["p"] >= d["min_p"] and c["word"] != "<unk>" for c in d["candidates"])
    assert d["counts"]["stones"] == len({c["signum"] for c in d["candidates"]})
