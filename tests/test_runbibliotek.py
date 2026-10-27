"""Referensbiblioteket för runformer (api/routers/runbibliotek.py): texten som runor i läsordning och läsriktningen."""
import math

from api.routers.runbibliotek import _direction, runes_of


def test_the_text_as_runes():
    r = runes_of("§A hrumuntr hikiu-(f)a [auk hunifraR] bris(a) : sun")
    letters = "".join(x["letter"] for x in r)
    assert letters == "hrumuntrhikiu-fabrisasun"  # the bracketed words are not on the stone
    assert [x["uncertain"] for x in r if x["letter"] in "fa"][:2] == [True, False]
    assert r[13]["lost"] and r[13]["letter"] == "-"
    assert r[0]["word"] == 0 and r[8]["word"] == 1 and r[-1]["word"] == 3
    assert [x["i"] for x in r] == list(range(len(r)))


def test_dividers_and_sections_are_not_runes():
    assert "".join(x["letter"] for x in runes_of("§P þiuþkiR uk| |kuþlaifr : uk ' karl × ...")) == "þiuþkiRukkuþlaifrukkarl"


def test_the_reading_direction_follows_the_neighbours():
    marks = [{"i": 0, "x": 0, "y": 0}, {"i": 1, "x": 10, "y": 10}, {"i": 2, "x": 20, "y": 20}, {"i": 3, "x": 500, "y": 0}]
    assert abs(_direction(marks, 1, box=10) - math.radians(45)) < 1e-9  # down and to the right
    assert _direction(marks, 3, box=10) == 0.0  # alone, far from the others: left to right
    marks[1]["skip"] = True
    assert abs(_direction(marks, 2, box=10) - math.radians(45)) < 1e-9  # the skipped rune is passed over


def test_two_readings_of_the_same_text_count_once():
    """Gs 11 has §P and §Q, two readings of one text: only the first is the stone's runes. Sides (§A, §B) are all kept."""
    assert "".join(x["letter"] for x in runes_of("§P þiuþkiR uk karl §Q þiuþkiR auk karl")) == "þiuþkiRukkarl"
    assert "".join(x["letter"] for x in runes_of("§A kunar §B raisti")) == "kunarraisti"
