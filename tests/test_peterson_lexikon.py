"""scripts/peterson_lexikon.py: signum reading, attestation parsing, verification and correction against Rundata.

The examples are short constructed lines (a name form and a signum), not text from the lexicon."""
import os

import pytest

from scripts import peterson_lexikon as pl

pytestmark = pytest.mark.skipif(not os.path.exists(pl.RUNDATA), reason="data/rundata.json saknas")


@pytest.fixture(scope="module")
def rd():
    return pl.Rundata()


@pytest.mark.parametrize("tok,pre,body,flags", [
    ("U585", "U", "585", ""),
    ("Ögl83", "Ög", "183", ""),          # old-style 1 read as l
    ("S6238t", "Sö", "238", "†"),        # Sö read S6, † read t
    ("Söl70", "Sö", "170", ""),
    ("Vgl26t", "Vg", "126", "†"),
    ("SMIGA", "Sm", "16A", ""),          # 6 read G
    ("DRMI", "DR", "M1", ""),
    ("U1130+", "U", "1130", "†"),
    ("U847$", "U", "847", "$"),
    ("U817+/", "U", "817", "†"),
])
def test_parse_signum(rd, tok, pre, body, flags):
    s = pl.parse_signum(tok, rd)
    assert (s["pre"], s["body"], s["flags"]) == (pre, body, flags)


def test_parse_signum_rejects_words(rd):
    for tok in ("Litt.:", "abiorn", "Janzén", "1947b"):
        assert pl.parse_signum(tok, rd) is None


def test_lookup_spacing_side_and_alias(rd):
    assert rd.lookup("U585") == "U 585"
    assert rd.lookup("DR143A") == "DR 143"          # side letter -> the stone
    assert rd.lookup("DRAUD1999;288") == "DR AUD1999;288"
    assert rd.lookup("BrOlsen;183") == "IM MM99"     # via Rundata's aliases


def test_attestations_split_cases_and_inherit_form(rd):
    txt = "Fsv. Abiorn\nNom. abiarn U894, U957, [abiori] Sm2† Ack. abiorn U753\nLitt.: Janzén 1947b s. 62 f."
    a = pl.attestations(txt, rd)
    assert [(x["case"], x["form"], x["pre"] + x["body"]) for x in a] == [
        ("Nom", "abiarn", "U894"), ("Nom", "abiarn", "U957"), ("Nom", "[abiori]", "Sm2"), ("Ack", "abiorn", "U753")]


def test_attestations_drop_notes_and_join_split_signa(rd):
    a = pl.attestations("Nom. aki DRAUD1999; 288$, oaki DR 288 Ack. siri(p) U545$/(se Sigriðr), aka U946(?)", rd)
    assert [(x["form"], x["pre"] + x["body"]) for x in a] == [
        ("aki", "DRAUD1999;288"), ("oaki", "DR288"), ("siri(p)", "U545"), ("aka", "U946")]


def test_check_ok_and_glyph(rd):
    a = pl.attestations("Nom. aki Ögl83", rd)[0]
    c = pl.check(a, rd)
    assert c["status"] == "ok" and c["signum"] == "Ög 183" and c["rattat"] == "tecken"


def test_check_corrects_flag_read_as_figure(rd):
    a = pl.attestations("Nom. abiarn U5854", rd)[0]          # U585$ with $ read as 4
    c = pl.check(a, rd)
    assert c["status"] == "ok" and c["signum"] == "U 585" and c["rattat"].startswith("signum U5854 -> U 585")
    assert pl.check(a, rd, correct=False)["status"] == "signum_saknas"


def test_check_corrects_thorn_read_as_p(rd):
    c = pl.check(pl.attestations("Ack. albop U391$", rd)[0], rd)
    assert (c["status"], c["form_fix"], c["rattat"]) == ("ok", "alboþ", "form")


def test_check_does_not_invent(rd):
    c = pl.check(pl.attestations("Nom. xqzzy U585", rd)[0], rd)
    assert c["status"] == "form_saknas" and not c["rattat"]


def test_head_match_and_variants():
    m = pl.head_match("Agmundr/Ǫgmundr mn.")
    assert m and m.group("g") == "mn"
    assert pl.head_match("Adis (?) kvn,").group("g") == "kvn"
    assert pl.head_match("Nom. aki U570") is None
    assert pl.headword_variants("Þorgisl/-gils") == ["Þorgisl", "Þorgils"]
    assert pl.headword_variants("Adis (?)") == ["Adis"]
    assert pl.headword_variants("Hagstæinn el. Hægstæinn") == ["Hagstæinn", "Hægstæinn"]


def test_page_entries_uses_indent():
    lines = [{"x": 300, "y": 10, "text": "18"},
             {"x": 140, "y": 50, "text": "Aki mn."},
             {"x": 200, "y": 60, "text": "Fda. Aki, fsv. Ake, fvn. Áki"},
             {"x": 200, "y": 70, "text": "Nom. aki U570"},
             {"x": 140, "y": 80, "text": "Al-"},
             {"x": 200, "y": 90, "text": "< germ. *ala-"},
             {"x": 140, "y": 100, "text": "Alfriðr kvn."},
             {"x": 200, "y": 110, "text": "Nom. alfriþ U1"}]
    e = pl.page_entries([(20, lines)], dpi=300)
    assert [(x["headword"], x["g"], len(x["lines"])) for x in e] == [("Aki", "mn", 2), ("Alfriðr", "kvn", 1)]
    assert pl.fvn_form(e[0]["lines"]) == "Áki"


def test_key_matches_rundata_spelling():
    assert pl.key("UlfR") == pl.key("Ulfr")
    assert pl.key("Þorkæll") == pl.key("Þorkell")


def test_stem_meets_inflected_rundata_names(rd):
    assert pl.stem("Friðlæifr") == pl.stem("Friðlæifs")
    assert pl.stem("Hrifli") == pl.stem("Hrifla")
    assert pl.stem("Friðmundr") in rd.name_stems           # Rundata has only inflected forms of it


def test_fix_headword_small_capital_r(rd):
    hw, note = pl.fix_headword("Gunnulfk", rd)              # ʀ read k
    assert hw == "GunnulfR" and note
    assert pl.fix_headword("Gunnulfr", rd) == ("Gunnulfr", "")
    assert pl.fix_headword("Xqzzyk", rd) == ("Xqzzyk", "")


def test_borrow_from_other_reading(rd):
    bad = pl.attestations("Nom. abiqrn U753", rd)[0]       # main reading garbled
    alt = pl.attestations("Ack. abiorn U753 Nom. abiorn U753", rd)
    b = pl.borrow(bad, alt, rd, taken=set())
    assert b and b["signum"] == "U 753" and b["rattat"].startswith("annan läsning")
    assert pl.borrow(bad, alt, rd, taken={("abiorn", "U 753")}) is None   # never counted twice


def test_fvn_form_drops_gender_word():
    assert pl.fvn_form(["Fvn. mn. Hrifla"]) == "Hrifla"


def test_head_match_ocr_variants():
    assert pl.head_match("Dyøta (?) kvn.?").group("g") == "kvn"
    assert pl.head_match("Fingr kv.-binamn?").group("g") == "kvinnobinamn"
    assert pl.head_match("Þorlofkvn.").group("hw") == "Þorlof"


def test_fix_headword_glyphs(rd):
    hw, note = pl.fix_headword("Kvigbigrn", rd)
    assert hw == "Kvigbiǫrn" and "tecken" in note


def test_key_capital_o_slash():
    assert pl.key("Øybiorn") == "oybiorn"


def test_fix_headword_keeps_g_before_r(rd):
    assert pl.fix_headword("Ofæigr", rd)[0] == "Ofæigr"
    assert pl.fix_headword("Kniitr", rd)[0] == "Knutr"
