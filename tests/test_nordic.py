"""Danska, norska och svenska runstenar jämförda (src/nordic.py): grupper, dateringar, jämförbara mönster och den
danska prägeln."""
import json
import os

from src import nordic as nd


def _rec(signum="U 1", **kw):
    return {"signum": signum, "period": "V", "object": "runsten", "normalization": "", "normalization_ows": "",
            "translation_en": "", "transliteration": "", "other": "", "dating": "V", "style": "", "carvers": [], **kw}


def test_groups_follow_the_series_and_the_realms_about_1025():
    assert nd.land_of(_rec("DR 279")) == "danmark" and nd.realm_of(_rec("DR 279", district="Ljunits hd, Skåne")) == "dk_skane"
    assert nd.realm_of(_rec("DR 4", district="(Sydslesvig)")) == "dk_jylland"
    assert nd.realm_of(_rec("DR 380", district="Bornholm")) == "dk_bornholm"
    assert nd.land_of(_rec("N 68")) == "norge" and nd.realm_of(_rec("N 68")) == "norge"
    assert nd.realm_of(_rec("Sö 113")) == "svitjod" and nd.realm_of(_rec("Vg 59")) == "gotar"
    assert nd.realm_of(_rec("Bo NIYR;6")) == "omstritt"
    assert nd.land_of(_rec("GR 1")) is None and not nd.is_runestone(_rec("GR 1"))
    assert not nd.is_runestone(_rec("DR 1", object="mynt"))


def test_years_from_each_system_of_dating():
    assert nd.year_of(_rec("DR 1", dating="V efter-Jelling")) == 1015
    assert nd.year_of(_rec("DR 1", dating="V kristen efter-Jelling")) == 1025
    assert nd.year_of(_rec("DR 1", dating="V Jelling el. efter-Jelling")) == 1000
    assert nd.year_of(_rec("DR 1", dating="V Jelling, efter år 934")) == 970
    assert nd.year_of(_rec("N 1", dating="V andra hälften av 1000-t")) == 1075
    assert nd.year_of(_rec("N 1", dating="V 1050-1100")) == 1075
    assert nd.year_of(_rec("N 1", dating="V ca 900")) == 900
    assert nd.year_of(_rec("N 1", dating="V")) is None
    assert nd.bin_of(998) == "tidig" and nd.bin_of(1000) == "mitt" and nd.bin_of(1050) == "sen" and nd.bin_of(None) is None


def test_patterns_read_the_translation_not_the_normalisation():
    # A Danish prayer is normalised Guþ hialpi, which the Swedish pattern (guð …) misses; the translation is the same
    dk = _rec("DR 337", normalization='"Guþ hialpi siol þeRa wæl', translation_en="May God well help their souls.",
              transliteration="kuþ : hialbi : siaul : þeRa : uel")
    v = nd.patterns(dk, nd.features(dk))
    assert v["bon"] == 1 and v["kristen"] == 1 and v["neutral"] == 0
    # A Norwegian signature: reist rúnar in Old West Norse, "carved the runes" in English
    no = _rec("N 1", normalization='"Arnketill reist rúnar', translation_en="Arnketill carved the runes.")
    assert nd.patterns(no, nd.features(no))["signatur"] == 1
    # Raising a stone is not a signature, and a bridge made for the soul is not a prayer
    se = _rec(translation_en="Ulfr had this stone raised and made the bridge for his soul.", transliteration="stain")
    ft = nd.features(se)
    assert ft["signatur"] == 0 and ft["had"] == 1 and ft["soul"] == 0 and ft["bon"] == 0
    assert nd.patterns(se, ft)["monoftong"] == 0
    assert nd.patterns(_rec(), nd.features(_rec()))["kristen"] is None


def test_stone_monophthong_and_short_preposition():
    ft = nd.features(_rec(translation_en="x", transliteration="sati stin þansi aft faþur sin"))
    assert ft["sten_mono"] == 1 and ft["sten_diph"] == 0 and ft["aft_short"] == 1 and ft["aft_long"] == 0
    ft = nd.features(_rec(translation_en="x", transliteration="raisti stain þina iftiR"))
    assert ft["sten_diph"] == 1 and ft["aft_long"] == 1 and ft["aft_short"] == 0


def test_compare_counts_and_time_held_constant():
    rows = []
    for i in range(40):
        for land, share in (("danmark", 0.5), ("sverige", 0.1)):
            rows.append({"s": f"{land}{i}", "land": land, "rike": None, "y": 1020, "bin": "mitt",
                         "v": {"titel": int(i < 40 * share)}})
    c = nd.compare(rows, "titel", "land")
    by = {g["key"]: g for g in c["groups"]}
    assert by["danmark"]["k"] == 20 and by["sverige"]["k"] == 4 and by["norge"]["n"] == 0
    assert c["test"]["p"] < 0.01
    pair = next(p for p in c["pairs"] if p["a"] == "danmark")
    assert pair["or"] > 1 and pair["or_mh"] > 1 and pair["strata"] == 1


def test_wilson_interval():
    lo, hi = nd.wilson(5, 10)
    assert 0.2 < lo < 0.5 < hi < 0.8 and nd.wilson(0, 0) == (0.0, 0.0)


def test_realm_definitions_name_only_known_blocks():
    path = os.path.join(os.path.dirname(__file__), "..", "web", "src", "lib", "realms.json")
    defs = json.load(open(path, encoding="utf-8"))
    blocks = {"uppland", "sodermanland", "vastmanland", "narke", "dalarna", "gastrikland", "halsingland", "medelpad",
              "angermanland", "jamtland", "harjedalen", "vastergotland", "ostergotland", "dalsland", "smaland", "oland",
              "gotland", "varmland", "bohuslan", "halland", "skane", "blekinge", "more", "danmark", "bornholm", "slesvig",
              "norge", "ostfold"}
    for ep in defs["epochs"]:
        ids = [r["id"] for r in ep["regions"]]
        assert len(ids) == len(set(ids)), ep["key"]
        used = [b for r in ep["regions"] for b in r["blocks"]]
        assert set(used) <= blocks, set(used) - blocks
        assert len(used) == len(set(used)), f"{ep['key']}: a block in two regions"
        for r in ep["regions"]:
            assert r["realm"] in defs["realms"] and r["certainty"] in defs["certainty"] and r["name"] and r["note"]
