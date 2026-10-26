"""Stavlöst läge (src/staveless.py): runorna delas efter var strecken står längs slingan."""
import numpy as np

from src import rune_bands, staveless


def synthetic(res=0.5):
    """A straight band 30 mm high and 200 mm long, five runes of two short upright strokes each (3 mm apart, 30 mm
    between runes), and a 20 mm piece of band edge running along the band."""
    H, W = 100, 400
    mask = np.zeros((H, W), bool)
    mask[20:80, 10:390] = True
    labels = np.zeros((H, W), int)
    b = 0
    for x in (50, 110, 170, 230, 290):
        for dx in (0, 6):
            b += 1
            labels[40:56, x + dx] = b  # 8 mm upright stroke
    b += 1
    labels[70, 320:360] = b  # along the band: an edge piece
    return mask, labels, res, b


def test_five_runes_of_two_strokes_and_the_edge_left_out():
    mask, labels, res, edge = synthetic()
    field = rune_bands.band_field(mask, res)
    g = staveless.group_runes(labels, field, res)
    assert len(g["runes"]) == 5
    assert all(len(r["branches"]) == 2 for r in g["runes"])
    assert edge not in g["branch_rune"]  # runs along the band
    assert g["gap_bands"] == staveless.GAP_BANDS and 3.0 < g["gap_mm"] < 27.0  # between the gaps inside a rune and between runes
    assert g["branch_rune"][1] == g["branch_rune"][2] != g["branch_rune"][3]


def test_the_coordinate_runs_along_the_band():
    mask, _, res, _ = synthetic()
    co = staveless.band_coordinate(mask, res)
    piece, s = co["piece"], co["s"]
    assert piece[50, 100] == piece[50, 300] > 0
    assert abs(abs(s[50, 300] - s[50, 100]) - 100.0) < 6.0  # 200 cells apart = 100 mm along the band
    assert abs(s[25, 200] - s[75, 200]) < 6.0  # across the band the coordinate hardly changes
    assert piece[5, 5] == 0 and np.isnan(s[5, 5])


def test_two_drawn_bands_side_by_side_stay_apart():
    """Two rows drawn as separate bands that touch (as on Hs 14): merged into one mask, the rows' strokes would share
    one coordinate and mix; with the drawn bands' own numbers each row is split on its own."""
    res = 0.5
    H, W = 140, 400
    mask = np.zeros((H, W), bool)
    mask[10:130, 10:390] = True
    pieces = np.zeros((H, W), np.int32)
    pieces[10:70, 10:390] = 1   # upper row, 30 mm high
    pieces[70:130, 10:390] = 2  # lower row, touching it
    labels = np.zeros((H, W), int)
    b = 0
    for row_y in (30, 90):
        for x in (50, 110, 170, 230):
            for dx in (0, 6):
                b += 1
                labels[row_y:row_y + 16, x + dx] = b
    field = rune_bands.band_field(mask, res)
    field["pieces"] = pieces
    g = staveless.group_runes(labels, field, res)
    assert len(g["runes"]) == 8 and {r["piece"] for r in g["runes"]} == {1, 2}
    assert all(len(r["branches"]) == 2 for r in g["runes"])
    assert abs(g["band_height_mm"] - 30.0) < 4.0  # each band's own height, not the merged 60 mm
