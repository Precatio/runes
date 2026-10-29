"""Litteraturregistret (src/literature.py): signum i löptext, tryckta sidor och SRI-artiklar."""
from src import literature as lit


def test_signum_pattern_finds_running_text_forms():
    rx = lit.signum_pattern(["U", "Sö", "Ög", "Vg", "DR", "Sm"])
    found = [f"{m.group(1)} {m.group(2).strip()}" for m in rx.finditer(
        "jfr Ög. 231 och Vg 181, U Fv1986;84, DR 42 samt Sm111; inte Ug 3 eller s. 13")]
    assert found == ["Ög 231", "Vg 181", "U Fv1986;84", "DR 42", "Sm 111"]


def test_printed_page():
    assert lit.printed_page("\n 252 VÄSTERGÖTLAND. VILSKE HÄRAD.\ntext", 9) == "252"
    assert lit.printed_page("   133. KAGGESTAD, HEDA SN, LYSINGS HD.        127\ntext", 9) == "127"
    assert lit.printed_page("text\nmer text\n  342\n", 9) == "342"
    assert lit.printed_page("bara löptext\nutan sidnummer", 9) == "pdf 9"


def test_sri_entry_heading():
    t = "slut på förra.\n   179. Kölaby sn, Stommen. Nu på kyrkogården.\n    233. Östra Stenby kyrka, Östkinds hd.\n 12. Se ovan."
    assert [m.group(1) for m in lit.ENTRY.finditer(t)] == ["179", "233"]
