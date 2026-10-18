"""Spårläsarens rena delar (src/trace_reader.py): mallkostnader, fördelningar, bindrunespärr och mängdbredding.
Den tunga skanningsvägen (compute_features) prövas inte här; den valideras i utdata/sparlasare (led A–G)."""
import src.trace_reader as tr


def blob(cross=False, zone="end", side=1.0, long=False, w=0.9):
    return {"cross": cross, "zone": zone, "side": side, "long": long, "w": w, "length": 8.0, "ratio": 0.9}


def test_long_end_branch_points_to_u():
    p = tr.rune_probs([blob(long=True)])
    top = max(p, key=p.get)
    assert top == "u" and "u" in tr.margin_set(p)


def test_crossing_branch_gives_the_crossing_runes():
    p = tr.rune_probs([blob(cross=True, zone="mid", side=0)])
    s = tr.margin_set(p)
    assert {"a", "h", "n", "o"} <= s and "b" not in s


def test_bare_stave_prefers_the_plain_runes():
    p = tr.rune_probs([])
    assert max(p, key=p.get) in ("i", "s")


def test_low_weight_blob_changes_little():
    bare = tr.rune_probs([])
    noisy = tr.rune_probs([blob(w=0.05)])
    assert abs(bare["i"] - noisy["i"]) < 0.1


def test_bind_rune_guard_says_nothing():
    many = [blob(zone="end"), blob(zone="mid"), blob(zone="end", side=-1.0), blob(zone="mid", side=-1.0),
            blob(zone="mid", long=True)]
    assert tr.rune_probs(many) is None
    assert tr.rune_probs(many[:4]) is not None  # four deep branches still fit the richest template


def test_probs_sum_to_one_with_floor():
    p = tr.rune_probs([blob()])
    assert abs(sum(p.values()) - 1.0) < 1e-9
    assert min(p.values()) >= tr.EPS / 16 - 1e-12


def test_expand_adds_dotted_variants():
    assert {"u", "v", "w", "y"} <= tr.expand({"u"})
    assert "e" in tr.expand({"i"}) and "g" in tr.expand({"k"})


def test_blob_weight_rises_with_depth():
    assert tr.blob_weight(0.9, 3.0, 8.0) > tr.blob_weight(0.3, 3.0, 8.0)


def test_gap_align_lets_lost_runes_match_anything():
    sets = [{"u"}, {"t"}]
    cost, pairs = tr._gap_align(sets, [(0, "u"), (1, "?")])
    assert pairs == [(0, 0), (1, 1)] and cost == 0.0
